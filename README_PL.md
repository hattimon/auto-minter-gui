# 🚀 Moltbook Auto-Minter GUI

[🇬🇧 English](README.md) • [🇵🇱 Polski](README_PL.md)

## Pobierz v0.1.4

[![Windows EXE](https://img.shields.io/badge/Windows-EXE-blue)](https://github.com/hattimon/auto-minter-gui/releases/tag/v0.1.4)
[![Linux-DEB](https://img.shields.io/badge/Linux-DEB-green)](https://github.com/hattimon/auto-minter-gui/releases/tag/v0.1.4)

> Najnowsza wersja: **v0.1.4** – sprytniejsze losowanie tytułów, elastyczne tryby solvera i bezpieczny powrót do gpt‑4.1‑mini

Przyjazna aplikacja desktopowa do tworzenia i automatycznego mintowania  
inskrypcji **MBC-20** na Moltbooku,  
z wbudowanym AI do rozwiązywania zagadek (lobster + LLM), elastycznymi trybami solvera  
(ulepszone reguły/cache vs. tryb „Używaj tylko LLM”), sprytną losizacją tytułów  
oraz wsparciem indexera mbc20.xyz.

------------------------------------------------------------------------

## ✨ Funkcje

-   🖥️ **Nowoczesne GUI PyQt6** -- zakładki: Main, History, Edytor .env,
    Auto Mint
-   🧠 **Integracja AI** -- automatyczne rozwiązywanie zagadek „lobster"
    Moltbooka (OpenAI)
-   🔄 **Auto‑Mint Scheduler** -- konfigurowalne interwały, inteligentny
    backoff, limit uruchomień
-   📜 **Historia i logi** -- podgląd postów oraz masowe ponowne
    indeksowanie przez API mbc20.xyz
-   🌍 **Zmiana języka** -- interfejs EN / PL
-   🔐 **Wbudowany edytor .env** -- zarządzanie kluczami API
    bezpośrednio w aplikacji

------------------------------------------------------------------------

## 📋 Wymagania

-   Python **3.10+** (zalecane)
-   Git
-   System: Windows, Linux lub macOS

### Zależności Pythona:

-   requests
-   python-dotenv
-   PyQt6

Instalacja:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🚀 Szybki start

### 1️⃣ Klonowanie repozytorium

``` bash
git clone https://github.com/hattimon/auto-minter-gui.git
cd auto-minter-gui
```

### 2️⃣ Konfiguracja środowiska

``` bash
cp .env.example .env
```

Uzupełnij plik `.env`:

``` env
MOLTBOOK_API_KEY=twoj_klucz_moltbook
OPENAI_API_KEY=twoj_klucz_openai
OPENAI_MODEL=gpt-4.1-mini
```

-   `MOLTBOOK_API_KEY` -- wymagany do publikacji i weryfikacji postów
-   `OPENAI_API_KEY` -- używany do rozwiązywania zagadek AI
-   `OPENAI_MODEL` -- Jeśli nie określono, domyślnie jest to `gpt-4.1-mini`

Klucz OpenAI utworzysz tutaj:
https://platform.openai.com/api-keys

------------------------------------------------------------------------

## 💻 Instalacja

### 🪟 Windows

``` powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Upewnij się, że Python jest dodany do **PATH**.

------------------------------------------------------------------------

### 🐧 Linux / 🍎 macOS

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Na niektórych dystrybucjach Linuxa mogą być wymagane dodatkowe
biblioteki Qt.

------------------------------------------------------------------------

## 🧩 Opis aplikacji

### 📝 Main

-   Tworzenie operacji: deploy / mint / transfer / link
-   Losowanie tytułu
-   Profile tokenów
-   Automatyczna weryfikacja postów (AI)

### 🤖 AI Brain

-   Test połączenia z OpenAI
-   Podgląd odpowiedzi AI do zagadek

### 📚 History

-   Podgląd `mbc20_history.log`
-   Masowe indeksowanie
-   Pomijanie błędów i wpisów już zindeksowanych

### ⚙️ Edytor .env

-   Wczytywanie i zapis konfiguracji
-   Natychmiastowa aktualizacja kluczy API

### 🔁 Auto Mint

-   Automatyczne mintowanie w tle
-   Dynamiczny backoff przy błędach
-   Tryb nieskończony lub limitowany

------------------------------------------------------------------------

## Zrzuty ekranu

### Główne okno  
![Główne okno](docs/screenshots/main-window.png)  

![Główne okno – menu](docs/screenshots/main-window-menu.png)  

### Zakładka Auto Mint  
![Zakładka Auto Mint](docs/screenshots/auto-mint.png)  

### Historia i indeksowanie  
![Zakładka Historia](docs/screenshots/history-tab.png)  

### Edytor .env  
![Edytor .env](docs/screenshots/env-editor.png)  

------------------------------------------------------------------------


## 📂 Struktura projektu

| Plik | Opis |
|------|------|
| `main.py` | Punkt startowy aplikacji |
| `mbc20_inscription_gui.py` | Główne GUI i logika |
| `auto_minter.py` | Harmonogram auto-mint |
| `lobster_solver.py` | Solver zagadek OpenAI |
| `indexer_client.py` | Klient API mbc20.xyz |
| `moltbook_client.py` | Klient API Moltbook |
| `.env.example` | Szablon konfiguracji |
| `requirements.txt` | Lista zależności |
| `build-deb.sh` | Zbuduj paczkę *.deb |
| `build-exe.ps1` | Zbuduj paczkę *.exe |

------------------------------------------------------------------------  

### [Zbuduj paczke *.deb oraz *exe](builds.md)   

------------------------------------------------------------------------  

## 🤝 Współpraca

1.  Fork repozytorium
2.  Utwórz branch funkcjonalny
3.  Zatwierdź zmiany
4.  Wypchnij branch
5.  Otwórz Pull Request

Pomysły, sugestie i nowe funkcje są mile widziane 🚀

------------------------------------------------------------------------

## 📄 English Version

English documentation:

➡️ **[README.md](README.md)**
