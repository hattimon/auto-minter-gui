# lobster_solver.py
import os
import re
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
    "- Words like 'adds', 'gains', 'increases by', 'speeds up by', 'picks up', 'accelerates by' mean you ADD.\n"
    "- Words like 'loses', 'reduces by', 'slows down by' mean you SUBTRACT.\n"
    "- If it asks for NET or TOTAL force between two opposing forces, "
    "subtract the smaller from the larger.\n"
    "- If there is only one number, just return that number.\n"
    "- Return ONLY the final numeric answer with exactly 2 decimal places.\n"
    "- Use a dot as decimal separator.\n"
)


# --- Mapa słów liczbowych dla prostych przypadków ---
# Parser obsługuje tylko czytelne warianty, resztę robi LLM

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twentyone": 21,
    "twentytwo": 22,
    "twentythree": 23,
    "twentyfour": 24,
    "twentyfive": 25,
    "twentysix": 26,
    "twentyseven": 27,
    "twentyeight": 28,
    "twentynine": 29,
    "thirty": 30,
    "thirtyone": 31,
    "thirtytwo": 32,
    "thirtythree": 33,
    "thirtyfour": 34,
    "thirtyfive": 35,
    "thirtysix": 36,
    "thirtyseven": 37,
    "thirtyeight": 38,
    "thirtynine": 39,
    "forty": 40,
    "fortyone": 41,
    "fortytwo": 42,
    "fortythree": 43,
}


def _clean_text(challenge: str) -> str:
    """
    Usuwa wszystkie znaki poza literami, cyframi i spacjami,
    normalizuje do małych liter, usuwa duplikaty liter.
    Parser jest uproszczony - działa dla czytelnych przypadków.
    """
    # usuń myślniki między literami (thirty-five → thirtyfive)
    cleaned = re.sub(r"([a-zA-Z])\s*-\s*([a-zA-Z])", r"\1\2", challenge)
    # zamień wszystko co nie jest literą/cyfrą/spacją na spację
    cleaned = re.sub(r"[^0-9A-Za-z\s]", " ", cleaned)
    # usuń wielokrotne spacje
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.lower().strip()
    
    # usuń duplikaty liter w tokenach (seevveen → seven, obbster → obster)
    tokens = cleaned.split()
    deduped = []
    for token in tokens:
        deduped_token = re.sub(r"([a-z])\1+", r"\1", token)
        deduped.append(deduped_token)
    cleaned = " ".join(deduped)
    
    # sklej wielowyrazowe liczby typu "thirty five" -> "thirtyfive"
    tokens = cleaned.split()
    merged = []
    skip_next = False
    for i, t in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if i + 1 < len(tokens):
            pair = t + tokens[i + 1]
            if pair in _NUMBER_WORDS:
                merged.append(pair)
                skip_next = True
                continue
        merged.append(t)
    return " ".join(merged)


def _extract_numbers(cleaned: str) -> list[int]:
    """
    Zwraca listę liczb całkowitych znalezionych w tekście:
    - najpierw cyfry,
    - potem słowa liczebników z mapy.
    """
    nums: list[int] = []

    # liczby zapisane cyframi
    for m in re.finditer(r"\d+", cleaned):
        try:
            nums.append(int(m.group(0)))
        except ValueError:
            pass

    # liczby zapisane słownie
    for token in cleaned.split():
        if token in _NUMBER_WORDS:
            nums.append(_NUMBER_WORDS[token])

    return nums


def _rule_based_solver(challenge: str, log_fn=None) -> float | None:
    """
    Prosta deterministyczna logika dla prostych przypadków:
    - czyści tekst,
    - wyciąga liczby,
    - jeśli dokładnie 2: zwraca ich sumę,
    - jeśli 1 liczba: zwraca ją,
    - inaczej None (niech zrobi to LLM).
    
    Parser celowo jest uproszczony - złożone przypadki idą do LLM.
    """
    cleaned = _clean_text(challenge)
    if log_fn:
        log_fn(f"[RULE] cleaned={cleaned!r}")

    nums = _extract_numbers(cleaned)
    if log_fn:
        log_fn(f"[RULE] numbers={nums}")

    if not nums:
        return None

    # jedna liczba → zwracamy ją
    if len(nums) == 1:
        return float(nums[0])

    # dwie liczby → sumujemy (typowe zadanie: total force, new velocity)
    if len(nums) == 2:
        return float(nums[0] + nums[1])

    # więcej liczb lub 0 liczb – oddajemy LLM-owi
    return None


def call_openai_solver(challenge: str, log_fn=None) -> str:
    """Wywołanie OpenAI z dopasowanym promptem."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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


def solve_lobster_challenge(challenge: str, log_fn=None, retry_on_fail=False, verify_fn=None, verification_code=None) -> str:
    """
    Wersja do użycia z GUI/auto-mint:
    1) próbuje deterministycznie policzyć wynik z tekstu (parser dla prostych przypadków),
    2) jeśli parser nie ogarnie – woła OpenAI,
    3) jeśli retry_on_fail=True i weryfikacja zwróci False, spróbuje ponownie z OpenAI,
    4) wynik zawsze zwraca w formacie 'NN.NN'.
    
    Args:
        challenge: tekst zagadki
        log_fn: funkcja do logowania
        retry_on_fail: czy przy błędnej weryfikacji spróbować ponownie z OpenAI
        verify_fn: funkcja weryfikacji (verification_code, answer) -> (bool, str)
        verification_code: kod weryfikacji do użycia z verify_fn
    """
    # 1. Spróbujmy policzyć sami (tylko proste przypadki)
    try:
        rb_val = _rule_based_solver(challenge, log_fn=log_fn)
    except Exception as e:
        rb_val = None
        if log_fn:
            log_fn(f"[RULE] exception: {e!r}")

    answer = None
    
    if rb_val is not None:
        if log_fn:
            log_fn(f"[RULE] using deterministic result={rb_val}")
        answer = f"{float(rb_val):.2f}"
    else:
        # 2. Fallback na OpenAI (dla złożonych przypadków)
        if log_fn:
            log_fn(f"[RULE] parser returned None, using OpenAI")
        ai_answer = call_openai_solver(challenge, log_fn=log_fn)
        try:
            ai_val = float(ai_answer)
            answer = f"{ai_val:.2f}"
        except ValueError:
            if log_fn:
                log_fn(f"[ERROR] Non-numeric AI answer: {ai_answer!r}")
            raise RuntimeError("AI answer is not numeric")

    # 3. Jeśli retry_on_fail i mamy verify_fn, sprawdź poprawność
    if retry_on_fail and verify_fn and verification_code:
        if log_fn:
            log_fn(f"[SOLVER] First attempt answer: {answer}, verifying...")
        
        ok, verify_log = verify_fn(verification_code, answer)
        
        if not ok:
            if log_fn:
                log_fn(f"[SOLVER] First attempt FAILED. Retrying with OpenAI...")
            
            # Spróbuj ponownie z OpenAI (nawet jeśli parser dał wynik)
            try:
                ai_answer = call_openai_solver(challenge, log_fn=log_fn)
                ai_val = float(ai_answer)
                answer = f"{ai_val:.2f}"
                
                if log_fn:
                    log_fn(f"[SOLVER] Retry answer: {answer}, verifying again...")
                
                # Weryfikuj ponownie
                ok2, verify_log2 = verify_fn(verification_code, answer)
                
                if not ok2:
                    if log_fn:
                        log_fn(f"[SOLVER] Retry also FAILED. Giving up.")
                    # Zwróć ostatnią odpowiedź mimo błędu
                    return answer
                else:
                    if log_fn:
                        log_fn(f"[SOLVER] Retry SUCCESS!")
                    return answer
                    
            except Exception as e:
                if log_fn:
                    log_fn(f"[SOLVER] Retry exception: {e!r}")
                # Zwróć pierwotną odpowiedź
                return answer
        else:
            if log_fn:
                log_fn(f"[SOLVER] First attempt SUCCESS!")

    return answer
