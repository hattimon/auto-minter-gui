#!/usr/bin/env python3
import json
import time
from dataclasses import dataclass

import moltbook_client
import indexer_client  # klient indexera mbc20.xyz


@dataclass
class AutoMintConfig:
    submolt: str
    tick: str
    amt: str
    base_interval: float  # sekundy
    min_interval: float   # sekundy
    error_backoff: float  # sekundy
    max_runs: int
    agent_name: str


class AutoMinter:
    """
    Główny scheduler auto-minta.
    Operuje na sekundach, ale GUI podaje mu wartości już przeliczone z minut.
    Backoff: backoff, 2*backoff, 4*backoff... reset po sukcesie.
    """

    def __init__(
        self,
        solve_fn,
        verify_fn,
        config: AutoMintConfig,
        log_fn=None,
        stop_flag_fn=None,
        build_title_fn=None,
        get_description_fn=None,
    ):
        """
        solve_fn(challenge:str) -> str – czysta funkcja rozwiązująca zagadkę
        verify_fn(verification_code:str, answer:str) -> (ok:bool, log:str)
        build_title_fn() -> str – generuje tytuł
        get_description_fn() -> str – zwraca opis posta
        """
        self.solve_fn = solve_fn
        self.verify_fn = verify_fn
        self.config = config
        self.log = log_fn or (lambda msg: None)
        self.stop_flag_fn = stop_flag_fn or (lambda: False)
        self.build_title_fn = build_title_fn or (lambda: "MBC-20 inscription")
        self.get_description_fn = get_description_fn or (lambda: "")

        # pierwszy interwał: respektuj zarówno base_interval jak i min_interval
        self.current_interval = max(config.base_interval, config.min_interval)

        # czas ostatniego udanego posta (mintu) – dla miękkiego limitu Moltbooka
        self.last_success_post_ts: float | None = None

    def _should_stop(self, runs_done: int) -> bool:
        if self.stop_flag_fn():
            return True
        if self.config.max_runs and runs_done >= self.config.max_runs:
            return True
        return False

    def _sleep_with_check(self, seconds: float):
        remaining = seconds
        step = min(30.0, seconds)  # co max 30 s sprawdzamy flagę stop
        while remaining > 0:
            if self.stop_flag_fn():
                break
            time.sleep(step)
            remaining -= step

    def _one_mint(self):
        # budujemy inskrypcję jak w GUI
        inscription_obj = {
            "p": "mbc-20",
            "op": "mint",
            "tick": self.config.tick,
            "amt": self.config.amt,
        }
        inscription_json = json.dumps(
            inscription_obj,
            ensure_ascii=False,
            separators=(",", ":"),  # bez spacji, jak w oryginalnym mbc-20
        )

        description = (self.get_description_fn() or "").strip()
        parts = []
        if description:
            parts.append(description)
        parts.append(inscription_json)
        parts.append("mbc20.xyz")
        full_content = "\n\n".join(parts)

        title = self.build_title_fn()
        submolt = (self.config.submolt or "mbc20").strip()
        # jeśli ktoś poda m/mbc20 → zostaw samo mbc20
        if submolt.lower().startswith("m/"):
            submolt = submolt[2:]
        # autokorekta typowej literówki
        if submolt.lower() == "bc20":
            submolt = "mbc20"

        self.log(
            f"[AUTO-MINT] Creating post in '{submolt}' title='{title}' "
            f"inscription={inscription_json}"
        )

        # --- POST do Moltbooka z obsługą statusu / retry_after ---
        resp_body, status, retry_after = moltbook_client.post_to_moltbook_with_status(
            submolt=submolt,
            title=title,
            content=full_content,
            log_fn=self.log,
        )

        if status == 0:
            # timeout / problem sieci
            raise RuntimeError("Moltbook ReadTimeout or network error")

        if status == 429:
            # miękki limit serwera – respektujemy retry_after_minutes
            if retry_after:
                wait_sec = float(retry_after) * 60.0
                minutes = wait_sec / 60.0
                self.log(
                    f"[AUTO-MINT] 429 Too Many Requests. "
                    f"Retry after {minutes:.2f}min (server hint)."
                )
                self.current_interval = max(wait_sec, self.config.min_interval)
            else:
                wait_sec = 30.0 * 60.0
                self.log(
                    "[AUTO-MINT] 429 Too Many Requests without retry_after. "
                    "Assuming 30min server limit."
                )
                self.current_interval = max(wait_sec, self.config.min_interval)
            # sygnał dla run_loop, że to rate limit, a nie błąd solvera
            raise RuntimeError("Moltbook 429 rate limit")

        if status < 200 or status >= 300 or not resp_body:
            raise RuntimeError(f"Moltbook POST failed with status {status}")

        self.log(
            "[AUTO-MINT] Post response:\n"
            + json.dumps(resp_body, indent=2, ensure_ascii=False)
        )

        # --- NOWY FORMAT VERIFICATION (jak w GUI) ---
        post_obj = resp_body.get("post") or {}
        post_id = post_obj.get("id")
        if not post_id:
            raise RuntimeError("Post created but missing post.id in response")

        post_url = moltbook_client.get_post_url(post_id)
        self.log(f"[AUTO-MINT] Post URL: {post_url}")

        verification = post_obj.get("verification") or {}
        verification_code = verification.get("verification_code")
        challenge_text = verification.get("challenge_text")
        expires_at = verification.get("expires_at")

        if not verification_code or not challenge_text:
            self.log("[AUTO-MINT] No verification required.")
            # brak weryfikacji – od razu indeksujemy po krótkim wait
            self.log(
                "[AUTO-MINT] [INDEXER] No verify required, will index "
                f"post_id={post_id} in 10 seconds."
            )
            time.sleep(10.0)
            try:
                idx_resp = indexer_client.index_single_post(post_id)
                self.log(
                    f"[AUTO-MINT] [INDEXER] OK post_id={post_id}: {idx_resp}"
                )
            except Exception as e:
                self.log(
                    f"[AUTO-MINT] [INDEXER] ERROR post_id={post_id}: {e!r}"
                )
            # mint uznajemy za sukces niezależnie od indexera
            self.last_success_post_ts = time.time()
            return

        self.log(
            f"[AUTO-MINT] Verification required. Code={verification_code} "
            f"Expires={expires_at}\nChallenge:\n{challenge_text}"
        )

        answer = self.solve_fn(challenge_text)
        self.log(f"[AUTO-MINT] LLM answer: {answer}")

        ok, verify_log = self.verify_fn(verification_code, answer)
        self.log("[AUTO-MINT] Verify response:\n" + verify_log)

        if not ok:
            raise RuntimeError("Verification failed")

        # w tym miejscu mamy poprawną weryfikację – czekamy 10 s i dopiero indeksujemy
        self.log(
            "[AUTO-MINT] [INDEXER] Verification OK, will index "
            f"post_id={post_id} in 10 seconds."
        )
        time.sleep(10.0)
        try:
            idx_resp = indexer_client.index_single_post(post_id)
            self.log(
                f"[AUTO-MINT] [INDEXER] OK post_id={post_id}: {idx_resp}"
            )
        except Exception as e:
            self.log(
                f"[AUTO-MINT] [INDEXER] ERROR post_id={post_id}: {e!r}"
            )

        # mint sukces, niezależnie od stanu indexera
        self.last_success_post_ts = time.time()

    def run_loop(self):
        runs_done = 0
        consecutive_errors = 0

        # pierwszy mint dopiero po pierwszym interwale (base/min)
        self._sleep_with_check(self.current_interval)

        MOLTBOOK_SOFT_LIMIT = 30 * 60  # 30 min

        while not self._should_stop(runs_done):
            # miękki limit – tylko informacja w logu, nie twarda blokada
            if self.last_success_post_ts is not None:
                elapsed = time.time() - self.last_success_post_ts
                if elapsed < MOLTBOOK_SOFT_LIMIT:
                    self.log(
                        "[AUTO-MINT] Soft Moltbook limit: last success "
                        f"{elapsed/60.0:.2f}min ago. "
                        "Will still try; server may respond 429."
                    )

            try:
                self._one_mint()
                runs_done += 1
                consecutive_errors = 0
                # po sukcesie wracamy do bazowego interwału (z poszanowaniem min_interval)
                self.current_interval = max(
                    self.config.base_interval,
                    self.config.min_interval,
                )
                minutes = self.current_interval / 60.0
                self.log(
                    f"[AUTO-MINT] Mint #{runs_done} OK. "
                    f"Next run in {minutes:.2f}min"
                )

            except Exception as e:
                msg = str(e)
                if "429 rate limit" in msg:
                    # current_interval ustawiony w _one_mint na retry_after
                    minutes = self.current_interval / 60.0
                    self.log(
                        f"[AUTO-MINT] RATE LIMIT: {e}. "
                        f"Next attempt in {minutes:.2f}min"
                    )
                    # NIE zwiększamy consecutive_errors
                else:
                    consecutive_errors += 1
                    backoff_base = self.config.error_backoff
                    # kaskada: backoff, 2*backoff, 4*backoff...
                    wait = backoff_base * (2 ** (consecutive_errors - 1))
                    # ale nigdy mniej niż min_interval
                    self.current_interval = max(wait, self.config.min_interval)
                    minutes = self.current_interval / 60.0
                    self.log(
                        f"[AUTO-MINT] ERROR: {e}. "
                        f"Backoff #{consecutive_errors}, wait {minutes:.2f}min"
                    )

            if self._should_stop(runs_done):
                break

            self._sleep_with_check(self.current_interval)

        self.log(f"[AUTO-MINT] Stopped. Total runs: {runs_done}")


# --------------- Daemon helper API ---------------

def run_auto_mint_once(
    solve_fn,
    verify_fn,
    config: AutoMintConfig,
    log_fn=None,
    build_title_fn=None,
    get_description_fn=None,
) -> tuple[bool, str | None]:
    """
    Helper dla daemona.

    - Używa istniejącej klasy AutoMinter oraz metody _one_mint().
    - Wykonuje dokładnie jedno podejście mintowania (jedno POST do Moltbooka + verify + indexer).
    - Nie uruchamia run_loop i nie zmienia globalnego stanu GUI.
    - Zwraca:
        (True, None)            – sukces,
        (False, "moltbook_5xx") – HTTP 5xx z Moltbooka,
        (False, "other")        – inne błędy.
    """
    am = AutoMinter(
        solve_fn=solve_fn,
        verify_fn=verify_fn,
        config=config,
        log_fn=log_fn,
        stop_flag_fn=lambda: False,
        build_title_fn=build_title_fn,
        get_description_fn=get_description_fn,
    )

    try:
        am._one_mint()
        return True, None
    except Exception as e:
        msg = str(e)
        if "status 5" in msg or " 5xx" in msg:
            return False, "moltbook_5xx"
        return False, "other"
