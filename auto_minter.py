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
    base_interval: float   # sekundy
    min_interval: float    # sekundy
    error_backoff: float   # sekundy
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
        solve_fn(challenge:str) -> str       – czysta funkcja rozwiązująca zagadkę
        verify_fn(code:str, answer:str) -> (ok:bool, log:str)
        build_title_fn() -> str             – generuje tytuł
        get_description_fn() -> str         – zwraca opis posta
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

        resp = moltbook_client.post_to_moltbook(
            submolt=submolt,
            title=title,
            content=full_content,
        )

        self.log(
            "[AUTO-MINT] Post response:\n"
            + json.dumps(resp, indent=2, ensure_ascii=False)
        )

        post_obj = resp.get("post") or {}
        post_id = post_obj.get("id")
        if not post_id:
            raise RuntimeError("Post created but missing post.id in response")

        post_url = moltbook_client.get_post_url(post_id)
        self.log(f"[AUTO-MINT] Post URL: {post_url}")

        verification = resp.get("verification") or {}
        verification_required = (
            resp.get("verification_required") or verification.get("required")
        )

        if not verification or not verification_required:
            self.log("[AUTO-MINT] No verification required.")

            # brak weryfikacji – od razu indeksujemy po krótkim wait
            self.log(
                f"[AUTO-MINT] [INDEXER] No verify required, will index "
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

            return

        challenge = verification.get("challenge", "")
        code = verification.get("code")
        expires_at = verification.get("expires_at")

        self.log(
            f"[AUTO-MINT] Verification required. Code={code} "
            f"Expires={expires_at}\nChallenge:\n{challenge}"
        )

        if not code or not challenge:
            raise RuntimeError("Missing verification code or challenge")

        answer = self.solve_fn(challenge)
        self.log(f"[AUTO-MINT] LLM answer: {answer}")

        ok, verify_log = self.verify_fn(code, answer)
        self.log("[AUTO-MINT] Verify response:\n" + verify_log)

        if not ok:
            raise RuntimeError("Verification failed")

        # w tym miejscu mamy poprawną weryfikację – czekamy 10 s i dopiero indeksujemy
        self.log(
            f"[AUTO-MINT] [INDEXER] Verification OK, will index "
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

    def run_loop(self):
        runs_done = 0
        consecutive_errors = 0

        # pierwszy mint dopiero po pierwszym interwale (base/min)
        self._sleep_with_check(self.current_interval)

        while not self._should_stop(runs_done):
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
