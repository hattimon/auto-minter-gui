import os
import requests
from dotenv import load_dotenv

# Domyślnie ładujemy z .env przy starcie procesu,
# ale klucz może być nadpisany przez GUI (set_api_key/reload_env).
load_dotenv()

MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"

# Trzymamy aktualny klucz w zmiennej modułowej.
MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")


def set_api_key(key: str | None):
    """Ustaw/zmień klucz API w trakcie działania aplikacji."""
    global MOLTBOOK_API_KEY
    MOLTBOOK_API_KEY = key


def _headers():
    if not MOLTBOOK_API_KEY:
        # Błąd dopiero przy użyciu, nie przy imporcie modułu.
        raise RuntimeError("Missing MOLTBOOK_API_KEY (set in .env or via set_api_key)")
    return {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json",
    }


# ---------- POSTY ----------

def post_to_moltbook(submolt: str, title: str, content: str, log_fn=None):
    """
    Używane przez GUI – prosty interfejs.
    Utwórz post w danym submolcie.

    log_fn – opcjonalna funkcja logująca (np. gui.log).

    Zgodnie z aktualnym API Moltbook używamy klucza `submolt_name`
    zamiast `submolt` w JSON body.

    Zwraca czysty resp.json() lub rzuca wyjątek.
    """
    url = f"{MOLTBOOK_API_BASE}/posts"
    data = {
        "submolt_name": submolt,
        "title": title,
        "content": content,
    }
    if log_fn:
        log_fn(f"[moltbook_client] POST {url} submolt_name={submolt} title={title}")
    resp = requests.post(url, headers=_headers(), json=data, timeout=30)
    if log_fn:
        log_fn(
            f"[moltbook_client] Status {resp.status_code} "
            f"Body: {resp.text}"
        )
    resp.raise_for_status()
    return resp.json()


def post_to_moltbook_with_status(submolt: str, title: str, content: str, log_fn=None):
    """
    Wersja dla AutoMinter:
    Zwraca (body:dict | None, status:int, retry_after_minutes:float | None)
    i NIE wywołuje raise_for_status().

    Dzięki temu AutoMinter może samodzielnie obsłużyć:
    - 429 Too Many Requests + retry_after_minutes,
    - timeouty,
    - inne 4xx/5xx.
    """
    url = f"{MOLTBOOK_API_BASE}/posts"
    data = {
        "submolt_name": submolt,
        "title": title,
        "content": content,
    }
    if log_fn:
        log_fn(f"[moltbook_client] POST {url} submolt_name={submolt} title={title}")
    try:
        resp = requests.post(url, headers=_headers(), json=data, timeout=60)
    except requests.exceptions.ReadTimeout as e:
        if log_fn:
            log_fn(f"[moltbook_client] ReadTimeout: {e!r}")
        # status=0, brak body i retry_after
        return None, 0, None

    if log_fn:
        log_fn(
            f"[moltbook_client] Status {resp.status_code} "
            f"Body: {resp.text}"
        )

    retry_after_minutes = None
    body = None
    try:
        body = resp.json()
    except Exception:
        body = None

    if resp.status_code == 429 and body:
        # Moltbook zwraca np.: {"retry_after_minutes": 10, ...}
        retry_after_minutes = body.get("retry_after_minutes")

    return body, resp.status_code, retry_after_minutes


def list_posts(sort: str = "hot", limit: int = 20):
    """
    Pobierz listę postów (np. sort=hot|new).
    Aktualne API zwykle zwraca słownik z kluczem 'posts'.
    """
    url = f"{MOLTBOOK_API_BASE}/posts"
    params = {"sort": sort, "limit": limit}
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_post(post_id: str):
    """
    Pobierz szczegóły pojedynczego posta.
    """
    url = f"{MOLTBOOK_API_BASE}/posts/{post_id}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_post_comments(post_id: str):
    """
    Pobierz komentarze pod postem.
    """
    url = f"{MOLTBOOK_API_BASE}/posts/{post_id}/comments"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------- PROFIL / URL‑e ----------

def get_my_profile():
    """
    Pobierz profil agenta powiązany z API key.
    Jeśli Moltbook zmieni endpoint, zaktualizuj tylko ten URL.
    """
    url = f"{MOLTBOOK_API_BASE}/agents/me"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_agent_profile_url(agent_name: str) -> str:
    """
    URL profilu agenta, np.
    https://www.moltbook.com/u/USDC_EURC_Payment_Agent
    """
    return f"https://www.moltbook.com/u/{agent_name}"


def get_post_url(post_id: str) -> str:
    """
    URL posta, np. https://www.moltbook.com/post/{post_id}
    """
    return f"https://www.moltbook.com/post/{post_id}"
