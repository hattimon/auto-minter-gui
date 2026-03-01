# 🚀 Moltbook Auto-Minter GUI

[🇬🇧 English](README.md) • [🇵🇱 Polski](README_PL.md)

## Pobierz v0.1.7

[![Windows EXE](https://img.shields.io/badge/Windows-EXE-blue)](https://github.com/hattimon/auto-minter-gui/releases/tag/v0.1.7)
[![Linux-DEB](https://img.shields.io/badge/Linux-DEB-green)](LinuxDaemonRPiOld.md) 
[![Raspberry%20Pi](https://img.shields.io/badge/Raspberry%20Pi-ARM%20DEB-red?logo=raspberrypi&logoColor=white)](daemonRPi.md) 

> Najnowsza wersja: **v0.1.7** – daemon MBC20 w tle, współdzielone ustawienia i logi, automatyczne indeksowanie oraz opcjonalny instalator autostartu dla Windows

Przyjazna aplikacja desktopowa do tworzenia i automatycznego mintowania  
**MBC-20** na Moltbook,

z wbudowanym rozwiązywaniem zagadek (lobster + LLM), pełnym rozdzieleniem sterowania LLM dla zakładki Głównej i Auto-Mint,  
domyślnym trybem czystego LLM, rozbudowanym dwujęzycznym interfejsem (PL/EN), dynamicznym ukrywaniem pól formularza,  
strukturalnym edytorem `.env` z obsługą wielu kluczy, ulepszonym logowaniem ze statusem,  
automatycznym retry po błędach Moltbook oraz wsparciem indexera mbc20.xyz,  
a także konfigurowalnym **daemonem MBC20**, który uruchamia auto-mint w tle, korzystając ze wspólnych profili i ustawień.

***

## 🍓 Opcjonalny: MBC20 Daemon (Raspberry Pi)

Jeśli chcesz, aby Auto-Mint działał ciągle w tle na Raspberry Pi (z obsługą trybu headless), możesz zainstalować opcjonalny **MBC20 daemon** jako usługę systemową.

- Używa tych samych plików współdzielonych co główny GUI: `mbc20_profiles.json`, `mbc20_daemon_settings.json`, `mbc20_history.log`
- Działa całkowicie w tle (zgodny z SSH, bez potrzeby środowiska graficznego)
- Każdy katalog Auto-Mint tworzy własną instancję usługi (np. `Daemon1`, `Daemon2`)

Pobierz skrypt instalacyjny do docelowego katalogu i uruchom go.

Pełną instrukcję instalacji i użycia znajdziesz w **[`daemonRPi.md`](daemonRPi.md)**.

---

## 🐧 Opcjonalny: MBC20 Daemon (Linux / starszy Raspbian)

Jeśli chcesz uruchomić Auto-Mint 24/7 na standardowym Linuksie lub starszych wersjach Raspberry Pi OS / Raspbian, możesz użyć tego samego skryptu **MBC20 daemon** jako usługi działającej w tle.

- Obsługuje Debian / Ubuntu / MX Linux (systemd lub SysVinit) oraz starsze wydania Raspbiana (Jessie, Stretch, Buster, Bullseye, Bookworm)
- Współdzieli profile, ustawienia i historię z głównym GUI: `mbc20_profiles.json`, `mbc20_daemon_settings.json`, `mbc20_history.log`
- Automatycznie instaluje zależności i rejestruje usługę do pracy w tle

Pobierz skrypt instalacyjny do docelowego katalogu i uruchom go.

Pełną instrukcję instalacji i użycia znajdziesz w **[`LinuxDaemonRPiOld.md`](LinuxDaemonRPiOld.md)**.

---

## 🪟 Opcjonalnie: daemon MBC20 (Windows)

Jeśli chcesz, aby Auto-Mint działał ciągle w tle, również po restartach systemu, możesz zainstalować opcjonalny **daemon MBC20**.

- Daemon korzysta z tych samych plików co główne GUI:
  - `mbc20_profiles.json`, `mbc20_daemon_settings.json`, `mbc20_history.log`.
- Osobne **GUI daemona** umożliwia konfigurację:
  - profilu tokena, `first_start_minutes`, `base_interval_minutes`,
  - interwałów retry dla błędów Moltbook 5xx i stałego backoffu dla innych błędów,
  - języka oraz opcji „Włącz daemona przy starcie”.
- Interaktywny instalator PowerShell:
  - pobiera wszystkie pliki Pythona daemona do katalogu projektu,
  - opcjonalnie instaluje zależności z `requirements.txt`,
  - tworzy skrót **MBC20 Daemon GUI** i dodaje go do autostartu Windows.

Szczegółowa instrukcja znajduje się w pliku **[`deamon.md`](./deamon.md)**.

------------------------------------------------------------------------

## ✨ Funkcje

-   🖥️ **Nowoczesne GUI PyQt6 (PyQt5 na RPi)** -- zakładki: Main, History, Edytor .env,
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
-   psutil

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

# 🛠️ Budowa pakietów

## 🐧 Linux (.deb)  |  🪟 Windows Portable (.exe)

### ⚙️ Zbuduj pakiety projektu

👉 **[Otwórz builds.md](builds.md)**  

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
