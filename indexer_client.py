#!/usr/bin/env python3
import os
import time
from typing import Tuple, List, Set

import requests

INDEX_URL = "https://mbc20.xyz/api/index-post"
HISTORY_LOG_FILE = "mbc20_history.log"  # ścieżka do pliku historii


def index_single_post(post_id: str, timeout: int = 15) -> dict:
    """
    Odpowiednik: 'Missing a mint? -> Single post -> Submit'
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://mbc20.xyz/",
    }
    resp = requests.get(
        INDEX_URL,
        params={"id": post_id},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def extract_post_ids_from_history(
    history_path: str | None = None,
) -> Set[str]:
    """
    Odczytaj plik historii i wyciągnij unikalne ID postów.
    """
    path = history_path or HISTORY_LOG_FILE
    if not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    post_ids: set[str] = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1) ID w JSON-ie: "id": "xxxxxxxx-..."
        if "\"id\": \"" in line and "/post/" not in line:
            try:
                part = line.split("\"id\":", 1)[1]
                part = part.strip().lstrip(":").strip()
                if part.startswith("\""):
                    pid = part.split("\"")[1]
                    if pid:
                        post_ids.add(pid)
            except Exception:
                pass

        # 2) ID w URL-u: /post/<id>
        if "/post/" in line:
            try:
                url_part = line.split("/post/", 1)[1]
                pid = url_part.split("\"")[0].split()[0].strip().rstrip(",")
                if pid:
                    post_ids.add(pid)
            except Exception:
                pass

    return post_ids


def extract_indexed_post_ids_from_history(
    history_path: str | None = None,
) -> Set[str]:
    """
    Przeszukuje plik historii i wyciąga ID postów, które już zostały
    poprawnie zindeksowane (linie z '[INDEXER] OK post_id=...').
    """
    path = history_path or HISTORY_LOG_FILE
    if not os.path.exists(path):
        return set()

    indexed_ids: set[str] = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "[INDEXER]" in line and "OK post_id=" in line:
                try:
                    part = line.split("OK post_id=", 1)[1]
                    pid = part.split(":", 1)[0].strip()
                    if pid:
                        indexed_ids.add(pid)
                except Exception:
                    continue

    return indexed_ids


def extract_error_post_ids_from_history(
    history_path: str | None = None,
) -> Set[str]:
    """
    Zwraca ID postów, które w logu miały wpis '[INDEXER] ERROR post_id=...'.
    """
    path = history_path or HISTORY_LOG_FILE
    if not os.path.exists(path):
        return set()

    error_ids: set[str] = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "[INDEXER]" in line and "ERROR post_id=" in line:
                try:
                    part = line.split("ERROR post_id=", 1)[1]
                    pid = part.split(":", 1)[0].strip()
                    if pid:
                        error_ids.add(pid)
                except Exception:
                    continue

    return error_ids


def index_all_posts_from_history(
    history_path: str | None = None,
    delay_seconds: float = 3.0,
    skip_already_indexed: bool = False,
    skip_previous_errors: bool = False,
) -> Tuple[int, int, int, List[str]]:
    """
    Zwraca: (indexed, errors, total, log_lines)
    - indexed: ile postów udało się zindeksować
    - errors: ile wywołań zakończyło się błędem
    - total: ile postów było do indeksowania (po ewentualnym skipie)
    - log_lines: szczegółowe logi (OK / ERROR / SERVER BUSY)
    """
    path = history_path or HISTORY_LOG_FILE
    if not os.path.exists(path):
        return 0, 0, 0, ["History file not found."]

    all_ids = extract_post_ids_from_history(path)
    if not all_ids:
        return 0, 0, 0, ["No post IDs found in history."]

    ids_to_index: Set[str] = set(all_ids)

    # filtr: pomijaj posty, które mają już w historii [INDEXER] OK post_id=...
    if skip_already_indexed:
        already_indexed = extract_indexed_post_ids_from_history(path)
        ids_to_index -= already_indexed

    # filtr: pomijaj posty, które wcześniej miały ERROR post_id=...
    if skip_previous_errors:
        error_ids = extract_error_post_ids_from_history(path)
        ids_to_index -= error_ids

    sorted_ids: List[str] = sorted(ids_to_index)
    if not sorted_ids:
        return 0, 0, 0, ["Nothing to index."]

    indexed = 0
    errors = 0
    log_lines: list[str] = []
    server_busy = False

    total = len(sorted_ids)

    for idx, pid in enumerate(sorted_ids, start=1):
        if server_busy:
            break

        try:
            resp = index_single_post(pid)
            # sprawdź JSON na wypadek komunikatu busy
            if isinstance(resp, dict) and resp.get("error") == "Server busy, retry later":
                log_lines.append(
                    f"SERVER BUSY for post_id={pid}: {resp}"
                )
                server_busy = True
                break

            log_lines.append(f"OK post_id={pid}: {resp}")
            indexed += 1
        except requests.HTTPError as e:
            # może w JSON-ie też jest 'Server busy'
            try:
                data = e.response.json()
                if isinstance(data, dict) and data.get("error") == "Server busy, retry later":
                    log_lines.append(
                        f"SERVER BUSY for post_id={pid}: {data}"
                    )
                    server_busy = True
                    break
            except Exception:
                pass
            log_lines.append(f"ERROR post_id={pid}: {e!r}")
            errors += 1
        except Exception as e:
            log_lines.append(f"ERROR post_id={pid}: {e!r}")
            errors += 1

        # jeśli to nie był ostatni post i serwer nie jest busy – throttling
        if not server_busy and idx < total:
            time.sleep(delay_seconds)

    if server_busy:
        log_lines.append("Stopped indexing because server is busy. Please try again later.")

    return indexed, errors, total, log_lines
