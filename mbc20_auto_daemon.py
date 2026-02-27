#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import random
import string
import sys
import time
from pathlib import Path
from typing import Optional, Dict

import psutil
from dotenv import load_dotenv

import moltbook_client
import indexer_client
from auto_minter import AutoMintConfig

BASE_DIR = Path(__file__).resolve().parent
HISTORY_LOG = BASE_DIR / "mbc20_history.log"
SETTINGS_FILE = BASE_DIR / "mbc20_daemon_settings.json"
PROFILES_FILE = BASE_DIR / "mbc20_profiles.json"
LOCK_FILE = BASE_DIR / "mbc20_daemon.lock"

# ---------- logging ----------

logger = logging.getLogger("mbc20_daemon")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    fh = logging.FileHandler(HISTORY_LOG, encoding="utf-8")
    fmt = logging.Formatter(
        "%(asctime)s [DAEMON] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)


# ---------- helpers: tytuły jak w GUI ----------

def generate_random_suffix(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def build_auto_title(base_title: str, agent_name: Optional[str] = None) -> str:
    base = (base_title.split("[")[0].strip() or "MBC-20 inscription")
    if agent_name:
        base = f"{base} ({agent_name})"
    suffix = generate_random_suffix(10)
    return f"{base} [{suffix}]"


# ---------- config / profiles ----------

def load_daemon_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {
            "profile_name": "",
            "use_llm_only": True,
            "base_interval_minutes": 1,
            "first_start_minutes": 0,
            "retry_moltbook_5xx": True,
            "retry_interval_minutes_5xx": 1,
            "use_fixed_backoff": True,
            "fixed_backoff_minutes": 31,
            "enabled": True,
            "language": "en",
        }
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("language", "en")
    if "base_interval_minutes" not in data and "base_interval_seconds" in data:
        data["base_interval_minutes"] = max(
            1, int(data["base_interval_seconds"] / 60)
        )
    if (
        "retry_interval_minutes_5xx" not in data
        and "retry_interval_seconds_5xx" in data
    ):
        data["retry_interval_minutes_5xx"] = max(
            1, int(data["retry_interval_seconds_5xx"] / 60)
        )
    data.setdefault("first_start_minutes", 0)
    return data


def load_all_token_profiles() -> Dict[str, dict]:
    if not PROFILES_FILE.exists():
        return {}
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data
    out: Dict[str, dict] = {}
    if isinstance(data, list):
        for item in data:
            name = item.get("name")
            if name:
                out[name] = item
    return out


def load_profile_by_name(name: str) -> Optional[dict]:
    profiles = load_all_token_profiles()
    return profiles.get(name)


# ---------- Moltbook / API ----------

def configure_moltbook_api():
    load_dotenv(override=True)
    api_key = os.getenv("MOLTBOOK_API_KEY")
    if not api_key:
        logger.error("MOLTBOOK_API_KEY is not set; aborting daemon run.")
        raise RuntimeError("Missing MOLTBOOK_API_KEY")
    moltbook_client.set_api_key(api_key)


def build_inscription_json(profile: dict) -> dict:
    tick = profile.get("tick", "").strip()
    amt = profile.get("amt", "").strip()
    if not tick or not amt:
        raise ValueError("Profile must contain 'tick' and 'amt' for mint.")
    return {
        "p": "mbc-20",
        "op": "mint",
        "tick": tick,
        "amt": amt,
    }


def get_post_description(profile: dict) -> str:
    return profile.get("description", "")


def create_mint_post(config: AutoMintConfig, profile: dict):
    """
    Tworzy post w submolcie przez moltbook_client.post_to_moltbook_with_status.
    """
    inscription = build_inscription_json(profile)
    inscription_str = json.dumps(inscription, ensure_ascii=False)
    description = get_post_description(profile)

    content = f"{inscription_str}\n\nmbc20.xyz"
    if description:
        content = f"{description.strip()}\n\n{content}"

    base_title = profile.get("title", "MBC-20 inscription")
    title = build_auto_title(base_title, config.agent_name)

    logger.info(
        "[AUTO-MINT] Creating post in '%s' title='%s' inscription=%s",
        config.submolt,
        title,
        inscription_str,
    )

    body, status, retry_after_min = moltbook_client.post_to_moltbook_with_status(
        submolt=config.submolt,
        title=title,
        content=content,
        log_fn=lambda msg: logger.info("[AUTO-MINT] %s", msg),
    )

    logger.info(
        "[AUTO-MINT] Response status=%s body=%r retry_after=%r",
        status,
        body,
        retry_after_min,
    )

    return body, status, retry_after_min


# ---------- indeksowanie (nie wpływa na backoff) ----------

def index_post_non_fatal(post_id: str, sleep_seconds: float = 3.0) -> None:
    if not post_id:
        logger.info("[INDEXER] Skipping indexer: missing post_id.")
        return

    try:
        logger.info(
            "[INDEXER] Will index post_id=%s in %.1f seconds.",
            post_id,
            sleep_seconds,
        )
        time.sleep(sleep_seconds)

        resp = indexer_client.index_single_post(post_id)
        logger.info("[INDEXER] OK post_id=%s: %r", post_id, resp)
    except Exception as e:
        logger.info(
            "[INDEXER] ERROR post_id=%s (non-fatal for daemon): %r",
            post_id,
            e,
        )


# ---------- GUI PID / lifecycle ----------

def parse_gui_pid_from_argv() -> Optional[int]:
    try:
        if "--gui-pid" in sys.argv:
            idx = sys.argv.index("--gui-pid")
            if idx + 1 < len(sys.argv):
                return int(sys.argv[idx + 1])
    except Exception:
        return None
    return None


def should_exit_if_gui_closed(gui_pid: Optional[int]) -> bool:
    if gui_pid is None:
        return False
    try:
        p = psutil.Process(gui_pid)
        if not p.is_running():
            return True
        return False
    except psutil.NoSuchProcess:
        return True
    except Exception:
        return False


# ---------- Daemon loop ----------

def is_server_5xx(status_code: Optional[int]) -> bool:
    if status_code is None:
        return False
    return 500 <= status_code <= 599


def run_daemon_once(settings: dict, gui_pid: Optional[int]):
    profile_name = settings.get("profile_name") or ""
    profile = load_profile_by_name(profile_name)
    if not profile:
        logger.error("Profile '%s' not found. Aborting daemon run.", profile_name)
        return

    configure_moltbook_api()

    base_interval_min = settings.get("base_interval_minutes", 35)
    first_start_min = settings.get("first_start_minutes", 1)
    retry_5xx = settings.get("retry_moltbook_5xx", True)
    retry_5xx_interval_min = settings.get("retry_interval_minutes_5xx", 1)
    use_fixed_backoff = settings.get("use_fixed_backoff", True)
    fixed_backoff_min = settings.get("fixed_backoff_minutes", 31)

    config = AutoMintConfig(
        submolt=profile.get("submolt", "mbc20"),
        tick=profile.get("tick", ""),
        amt=profile.get("amt", ""),
        base_interval=base_interval_min * 60.0,
        min_interval=base_interval_min * 60.0,
        error_backoff=fixed_backoff_min * 60.0,
        max_runs=0,
        agent_name="daemon",
    )

    logger.info(
        "Daemon start profile=%s, use_llm_only=%s, config=%r, "
        "first_start=%dmin, base_interval=%dmin, retry_5xx=%s every %dmin, "
        "fixed_backoff=%s %dmin, gui_pid=%r",
        profile_name,
        settings.get("use_llm_only", True),
        config.__dict__,
        first_start_min,
        base_interval_min,
        retry_5xx,
        retry_5xx_interval_min,
        use_fixed_backoff,
        fixed_backoff_min,
        gui_pid,
    )

    if first_start_min > 0:
        logger.info(
            "Daemon: waiting %d minutes before first run.", first_start_min
        )
        for _ in range(first_start_min * 60):
            if should_exit_if_gui_closed(gui_pid):
                logger.info("GUI is closed during initial wait. Exiting daemon.")
                return
            time.sleep(1.0)

    while True:
        if should_exit_if_gui_closed(gui_pid):
            logger.info("GUI is not running anymore (pid=%r). Exiting daemon.", gui_pid)
            return

        try:
            body, status, retry_after_min = create_mint_post(config, profile)
        except Exception as e:
            logger.error("Unexpected error during mint: %r", e)
            if use_fixed_backoff:
                logger.info(
                    "Error during mint, sleeping fixed_backoff %dmin.",
                    fixed_backoff_min,
                )
                for _ in range(fixed_backoff_min * 60):
                    if should_exit_if_gui_closed(gui_pid):
                        logger.info("GUI closed during fixed_backoff. Exiting daemon.")
                        return
                    time.sleep(1.0)
            else:
                logger.info(
                    "Error during mint, sleeping base_interval %dmin.",
                    base_interval_min,
                )
                for _ in range(base_interval_min * 60):
                    if should_exit_if_gui_closed(gui_pid):
                        logger.info("GUI closed during base_interval. Exiting daemon.")
                        return
                    time.sleep(1.0)
            continue

        if status == 201 and body:
            logger.info(
                "Daemon mint success (201), sleeping base_interval %dmin.",
                base_interval_min,
            )

            post_obj = None
            if isinstance(body, dict):
                post_obj = body.get("post") or body

            post_id = None
            if isinstance(post_obj, dict):
                post_id = post_obj.get("id")

            if post_id:
                logger.info(
                    "[INDEXER] Scheduling non-fatal indexer for post_id=%s.",
                    post_id,
                )
                index_post_non_fatal(post_id, sleep_seconds=3.0)
            else:
                logger.info(
                    "[INDEXER] Skipping indexer: cannot extract post_id from body=%r.",
                    body,
                )

        elif status == 429 and retry_after_min:
            logger.info(
                "Daemon got 429, retry_after_minutes=%s, sleeping that.",
                retry_after_min,
            )
            seconds = float(retry_after_min) * 60.0
            for _ in range(int(seconds)):
                if should_exit_if_gui_closed(gui_pid):
                    logger.info("GUI closed during 429 backoff. Exiting daemon.")
                    return
                time.sleep(1.0)
            continue
        elif is_server_5xx(status) and retry_5xx:
            logger.info(
                "Daemon got 5xx (%s), retry every %dmin.",
                status,
                retry_5xx_interval_min,
            )
            for _ in range(retry_5xx_interval_min * 60):
                if should_exit_if_gui_closed(gui_pid):
                    logger.info("GUI closed during 5xx backoff. Exiting daemon.")
                    return
                time.sleep(1.0)
            continue
        else:
            logger.info(
                "Daemon mint finished with status=%s, sleeping base_interval %dmin.",
                status,
                base_interval_min,
            )

        for _ in range(base_interval_min * 60):
            if should_exit_if_gui_closed(gui_pid):
                logger.info("GUI closed during base_interval. Exiting daemon.")
                return
            time.sleep(1.0)


def is_another_daemon_running() -> bool:
    """
    Zwraca zawsze False – nie blokujemy startu na podstawie innych procesów.
    Kontrolę pozostawiamy lockfile'owi i GUI PID.
    """
    return False


def main():
    settings = load_daemon_settings()
    logger.info("DEBUG: loaded settings = %r", settings)

    if not settings.get("enabled", True):
        logger.info("Daemon disabled in settings, exiting.")
        return

    gui_pid = parse_gui_pid_from_argv()

    if LOCK_FILE.exists():
        logger.info("Lockfile exists; another daemon likely running. Exiting.")
        return

    if is_another_daemon_running():
        return

    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    logger.info("Daemon invoked; pid=%d gui_pid=%r", os.getpid(), gui_pid)
    logger.info("Daemon timezone: %r", time.tzname)

    try:
        run_daemon_once(settings, gui_pid)
    finally:
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
