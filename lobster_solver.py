# lobster_solver.py
import os
import time
import requests


MOLTBOOK_PUZZLE_SYSTEM_PROMPT = (
    "You are a precise arithmetic solver for short, noisy lobster puzzles.\n"
    "The text is noisy (random capitalization, weird symbols: ^ ~ | < > [ ] etc.).\n"
    "Rules:\n"
    "- Ignore ALL symbols that are not letters, digits or spaces.\n"
    "- Convert any number words (like 'thirty two', 'tWeLvE', 'fifteen') to integers.\n"
    "- The puzzle may describe:\n"
    "  (A) a base value and a change (increase or decrease), OR\n"
    "  (B) two forces/amounts and ask for NET or TOTAL force.\n"
    "- Words like 'exerts', 'has', 'walks at', 'swims at' give base values.\n"
    "- Words like 'adds', 'gains', 'increases by', 'speeds up by', 'picks up' mean you ADD.\n"
    "- Words like 'loses', 'reduces by', 'slows down by' mean you SUBTRACT.\n"
    "- If it asks for NET or TOTAL force between two opposing forces, "
    "subtract the smaller from the larger.\n"
    "- If there is only one number, just return that number.\n"
    "- Return ONLY the final numeric answer with exactly 2 decimal places.\n"
    "- Use a dot as decimal separator.\n"
)


def call_openai_solver(challenge: str, log_fn=None) -> str:
    """Wywołanie OpenAI z dopasowanym promptem, bez logiki GUI."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    user_prompt = (
        MOLTBOOK_PUZZLE_SYSTEM_PROMPT
        + "\nPuzzle text:\n"
        + challenge
        + "\nAnswer:"
    )

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise arithmetic solver for noisy lobster puzzles.",
            },
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": 16,
    }

    max_retries = 5
    backoff_seconds = 2.0

    for attempt in range(1, max_retries + 1):
        try:
            if log_fn:
                log_fn(
                    f"[DEBUG] OpenAI call attempt {attempt}/{max_retries} model={model}"
                )
            r = requests.post(url, headers=headers, json=body, timeout=20)
            r.raise_for_status()
            data = r.json()
            raw = data["choices"][0]["message"]["content"].strip()
            answer = raw.splitlines()[0].strip()
            if log_fn:
                openai_id = data.get("id", "unknown")
                log_fn(f"[OpenAI] id={openai_id} answer={answer}")
            return answer
        except Exception as e:
            if log_fn:
                log_fn(f"[ERROR] OpenAI attempt {attempt} failed: {e!r}")
            if attempt == max_retries:
                raise
            time.sleep(backoff_seconds)
            backoff_seconds *= 2.0

    raise RuntimeError("OpenAI retries exhausted")


def solve_lobster_challenge(challenge: str, log_fn=None) -> str:
    """
    Prosta wersja do użycia z GUI:
    1) woła OpenAI,
    2) sprawdza, czy odpowiedź jest liczbą,
    3) zwraca ją w formacie 'NN.NN'.
    """
    ai_answer = call_openai_solver(challenge, log_fn=log_fn)

    try:
        ai_val = float(ai_answer)
    except ValueError:
        if log_fn:
            log_fn(f"[ERROR] Non-numeric AI answer: {ai_answer!r}")
        raise RuntimeError("AI answer is not numeric")

    return f"{ai_val:.2f}"
