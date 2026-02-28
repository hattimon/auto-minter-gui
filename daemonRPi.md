# 🍓 daemonRPi -- Instalacja i konfiguracja (Multi-Instance)

Skrypt instalacyjny:
https://github.com/hattimon/auto-minter-gui/blob/main/scripts/rpdaemon.sh

------------------------------------------------------------------------

# 🇵🇱 Wersja Polska

## 🧠 Informacje

-   Testowane na Raspberry Pi 3 (Raspbian Trixie -- headless)
-   Działa również na Raspberry Pi 2 / 4 / Zero
-   Niskie wymagania sprzętowe
-   Obsługa wielu instancji (Daemon1, Daemon2, itd.)
-   Każdy folder = osobna usługa systemowa
-   Brak konfliktów między instancjami

------------------------------------------------------------------------

# 📂 Instalacja w dowolnym folderze

Nie klonujemy całego repozytorium. Pobieramy wyłącznie skrypt do
docelowego katalogu aplikacji.

------------------------------------------------------------------------

## 🔹 Przykład -- pierwsza instancja (Daemon1)

### 1️⃣ Utworzenie katalogu

    mkdir Daemon1
    cd Daemon1

### 2️⃣ Pobranie skryptu

    wget https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/rpdaemon.sh

### 3️⃣ Nadanie uprawnień

    chmod +x rpdaemon.sh

### 4️⃣ Instalacja

    sudo ./rpdaemon.sh

------------------------------------------------------------------------

## ⚙️ Co robi skrypt?

-   Instaluje wymagane zależności
-   Tworzy usługę systemd
-   Włącza autostart
-   Nadaje nazwę usługi na podstawie folderu (np. Daemon1)

------------------------------------------------------------------------

# 🔁 Druga instancja (Daemon2)

    mkdir Daemon2
    cd Daemon2
    wget https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/rpdaemon.sh
    chmod +x rpdaemon.sh
    sudo ./rpdaemon.sh

Efekt: - Powstaje niezależna usługa systemowa Daemon2 - Brak konfliktu z
Daemon1 - Obie instancje działają równolegle

------------------------------------------------------------------------

# 🔍 Zarządzanie usługą (przykład: Daemon1)

Status:

    sudo systemctl status Daemon1

Start:

    sudo systemctl start Daemon1

Stop:

    sudo systemctl stop Daemon1

Restart:

    sudo systemctl restart Daemon1

Logi:

    journalctl -u Daemon1 -f

------------------------------------------------------------------------

# 🖥️ Tryb pracy

-   System: Raspbian (Trixie testowane)
-   Tryb: Headless
-   Instalacja przez SSH możliwa
-   Działa w tle jako daemon

------------------------------------------------------------------------

# 🇬🇧 English Version

## 🧠 Overview

-   Tested on Raspberry Pi 3 (Raspbian Trixie -- headless)
-   Works on Raspberry Pi 2 / 4 / Zero
-   Low hardware requirements
-   Supports multiple instances (Daemon1, Daemon2, etc.)
-   Each folder creates its own system service
-   No conflicts between instances

------------------------------------------------------------------------

# 📂 Install in Any Folder

Do NOT clone the entire repository. Download only the script into your
target application folder.

------------------------------------------------------------------------

## 🔹 Example -- First Instance (Daemon1)

    mkdir Daemon1
    cd Daemon1
    wget https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/rpdaemon.sh
    chmod +x rpdaemon.sh
    sudo ./rpdaemon.sh

------------------------------------------------------------------------

## 🔁 Second Instance (Daemon2)

    mkdir Daemon2
    cd Daemon2
    wget https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/rpdaemon.sh
    chmod +x rpdaemon.sh
    sudo ./rpdaemon.sh

Result: - Independent system service named after folder - No service
conflicts - Multiple daemons can run simultaneously

------------------------------------------------------------------------

# 🔍 Service Management Example (Daemon1)

    sudo systemctl status Daemon1
    sudo systemctl start Daemon1
    sudo systemctl stop Daemon1
    sudo systemctl restart Daemon1
    journalctl -u Daemon1 -f

------------------------------------------------------------------------

# 🖥️ Runtime Mode

-   OS: Raspbian (Trixie tested)
-   Headless compatible
-   SSH installation supported
-   Runs fully in background
