**Choose language / Wybierz język:**
👉 [English](#english)   👉 [Polski](#polski)

---

<a id="english"></a>
# 🇬🇧 English Version

# 💠 mbc20_daemon_en.sh – Universal Headless Daemon (Multi-Instance)

Installer script:
https://github.com/hattimon/auto-minter-gui/blob/main/scripts/mbc20_daemon_en.sh

Works on:

- Debian 11 / 12 (systemd)
- Ubuntu Server 20.04 / 22.04 / 24.04 (systemd)
- Raspberry Pi OS (Bookworm / Trixie, systemd)
- MX Linux 23 (SysVinit, classic init with `start-stop-daemon` + `update-rc.d`)

Supports **multiple instances** (Daemon1, Daemon2, ...).
Each folder creates its own service:

- `~/Daemon1` → `mbc20-daemon-Daemon1`
- `~/Daemon2` → `mbc20-daemon-Daemon2`
- etc.

---

## 📂 Simple Installation (Daemon1)

> Same steps for any user – home directory is detected automatically.

### 1️⃣ Create folder

```bash
cd ~
mkdir -p Daemon1
cd Daemon1
```

### 2️⃣ Download script

```bash
curl -s https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/mbc20_daemon_en.sh -o mbc20_daemon_en.sh
chmod +x mbc20_daemon_en.sh
```

### 3️⃣ Run installer

```bash
./mbc20_daemon_en.sh
```

The script will:

- detect `APP_DIR=~/Daemon1` and service name `mbc20-daemon-Daemon1`,
- clone/update `auto-minter-gui` into `~/Daemon1/auto-minter-gui`,
- create a Python venv and install dependencies,
- patch `mbc20_auto_daemon.py` (safe `MOLTBOOK_API_KEY`, `extra_comment`, fixed `main`),
- create `.env`, `mbc20_profiles.json`, `mbc20_daemon_settings.json`,
- generate `start_daemon.sh` with a PID file owned by the current user,
- create and start a system service:
  - **systemd**: `/etc/systemd/system/mbc20-daemon-Daemon1.service`,
  - **SysVinit (MX)**: `/etc/init.d/mbc20-daemon-Daemon1` + `update-rc.d`.

During option `1` in the menu you will be asked for:

- `MOLTBOOK_API_KEY` (required),
- optional `OPENAI_API_KEY`,
- `MOLTBOOK_API_NAME`,
- first mint profile (ticker, amount, title, comment).

---

## 🔁 Second Instance (Daemon2)

```bash
cd ~
mkdir -p Daemon2
cd Daemon2
cp ~/mbc20_daemon_en.sh .
chmod +x mbc20_daemon_en.sh
./mbc20_daemon_en.sh
```

Result:

- independent service `mbc20-daemon-Daemon2`,
- separate `.env`, profiles, logs,
- no conflicts with Daemon1.

Repeat for `Daemon3`, `Daemon4`, etc.

---

## 🧩 Menu Overview

```bash
cd ~/Daemon1
./mbc20_daemon_en.sh
```

```text
== MBC20 Daemon menu (Daemon1) ==
1) Install / refresh daemon
2) Add token profile
3) Edit token profile
4) Delete token profile
5) Select active profile
6) View daemon logs
7) Edit .env (API keys)
8) Enable / disable autostart
9) Reindex from history
10) Exit

  Daemon: ACTIVE | mbc20-daemon-Daemon1 (systemd|SysVinit)
```

- `1` – install/refresh daemon (code, venv, service)
- `2–4` – manage mint profiles (add/edit/delete)
- `5` – select active profile (daemon restarts)
- `6` – tail logs (`mbc20_history.log` + `daemon.log`)
- `7` – edit `.env` (API keys)
- `8` – toggle autostart (systemd enable/disable or SysVinit update-rc.d)
- `9` – reindex from history
- `10` – exit menu

---

## 🔍 Service Status & Logs

### systemd (Debian / Ubuntu / RPi OS)

```bash
# List all daemon services
systemctl list-units "mbc20-daemon-*.service" --all

# Status of Daemon1
sudo systemctl status mbc20-daemon-Daemon1

# Start / stop / restart
sudo systemctl start   mbc20-daemon-Daemon1
sudo systemctl stop    mbc20-daemon-Daemon1
sudo systemctl restart mbc20-daemon-Daemon1

# Logs (journal)
journalctl -u mbc20-daemon-Daemon1 -f
```

### SysVinit (MX Linux 23)

```bash
sudo service mbc20-daemon-Daemon1 status
sudo service mbc20-daemon-Daemon1 start
sudo service mbc20-daemon-Daemon1 stop
sudo service mbc20-daemon-Daemon1 restart
```

### Process & PID check

```bash
# Check daemon process (all instances)
ps aux | grep mbc20_auto_daemon.py | grep -v grep

# Check PID file
cat /var/run/mbc20-daemon-Daemon1.pid
```

### Logs

```bash
tail -f ~/Daemon1/auto-minter-gui/mbc20_history.log
tail -f ~/Daemon1/daemon.log
```

---

<a id="polski"></a>
# 🇵🇱 Wersja Polska

# 💠 mbc20_daemon.sh – Uniwersalny daemon headless (wiele instancji)

Skrypt instalacyjny:
https://github.com/hattimon/auto-minter-gui/blob/main/scripts/mbc20_daemon.sh

Działa na:

- Debian 11 / 12 (systemd)
- Ubuntu Server 20.04 / 22.04 / 24.04 (systemd)
- Raspberry Pi OS (Bookworm / Trixie, systemd)
- MX Linux 23 (SysVinit – klasyczny init z `start-stop-daemon` + `update-rc.d`)

Obsługuje **wiele instancji** (Daemon1, Daemon2, itd.).
Każdy katalog tworzy własną usługę:

- `~/Daemon1` → `mbc20-daemon-Daemon1`
- `~/Daemon2` → `mbc20-daemon-Daemon2`
- itd.

---

## 📂 Prosta instalacja (Daemon1)

> Te same kroki dla każdego użytkownika – katalog domowy wykrywany automatycznie.

### 1️⃣ Utworzenie katalogu

```bash
cd ~
mkdir -p Daemon1
cd Daemon1
```

### 2️⃣ Pobranie skryptu

```bash
curl -s https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/mbc20_daemon.sh -o mbc20_daemon.sh
chmod +x mbc20_daemon.sh
```

### 3️⃣ Uruchomienie instalatora

```bash
./mbc20_daemon.sh
```

Skrypt:

- wykryje `APP_DIR=~/Daemon1` i nazwę usługi `mbc20-daemon-Daemon1`,
- sklonuje/zaktualizuje `auto-minter-gui` w `~/Daemon1/auto-minter-gui`,
- stworzy wirtualne środowisko Pythona i doinstaluje zależności,
- spatchuje `mbc20_auto_daemon.py`,
- utworzy `.env`, `mbc20_profiles.json`, `mbc20_daemon_settings.json`,
- wygeneruje `start_daemon.sh` z PID-em należącym do użytkownika,
- utworzy i uruchomi usługę:
  - **systemd**: `/etc/systemd/system/mbc20-daemon-Daemon1.service`,
  - **SysVinit (MX)**: `/etc/init.d/mbc20-daemon-Daemon1` + `update-rc.d`.

Podczas opcji `1` w menu podajesz:

- `MOLTBOOK_API_KEY` (wymagany),
- opcjonalny `OPENAI_API_KEY`,
- `MOLTBOOK_API_NAME`,
- pierwszy profil mintowania (ticker, ilość, tytuł, komentarz).

---

## 🔁 Druga instancja (Daemon2)

```bash
cd ~
mkdir -p Daemon2
cd Daemon2
cp ~/mbc20_daemon.sh .
chmod +x mbc20_daemon.sh
./mbc20_daemon.sh
```

Efekt:

- osobna usługa `mbc20-daemon-Daemon2`,
- osobne `.env`, profile i logi,
- brak konfliktu z Daemon1.

Analogicznie dla `Daemon3`, `Daemon4`, itd.

---

## 🧩 Menu – krótki opis

```bash
cd ~/Daemon1
./mbc20_daemon.sh
```

```text
== MBC20 Daemon menu (Daemon1) ==
1) Zainstaluj / odswiez daemon
2) Dodaj profil tokena
3) Edytuj profil tokena
4) Usun profil tokena
5) Wybierz aktywny profil
6) Podglad logow daemona
7) Edytuj .env (API keys)
8) Wlacz / wylacz autostart
9) Reindeksuj z historii
10) Wyjscie

  Daemon: AKTYWNY | mbc20-daemon-Daemon1 (systemd|SysVinit)
```

- `1` – instalacja/odświeżenie daemona (kod, venv, usługa)
- `2–4` – zarządzanie profilami (dodaj/edytuj/usuń)
- `5` – wybór aktywnego profilu (daemon restartowany z nowym profilem)
- `6` – podgląd logów (`mbc20_history.log` + `daemon.log`)
- `7` – edycja `.env` (klucze API)
- `8` – autostart: systemd enable/disable lub SysVinit update-rc.d
- `9` – reindeksacja historii
- `10` – wyjście z menu

---

## 🔍 Sprawdzanie statusu i logów

### systemd (Debian, Ubuntu, Raspberry Pi OS)

```bash
# Wszystkie usługi daemona
systemctl list-units "mbc20-daemon-*.service" --all

# Status konkretnej instancji
sudo systemctl status mbc20-daemon-Daemon1

# Start / stop / restart
sudo systemctl start   mbc20-daemon-Daemon1
sudo systemctl stop    mbc20-daemon-Daemon1
sudo systemctl restart mbc20-daemon-Daemon1

# Logi z journalctl
journalctl -u mbc20-daemon-Daemon1 -f
```

### SysVinit (MX Linux 23)

```bash
sudo service mbc20-daemon-Daemon1 status
sudo service mbc20-daemon-Daemon1 start
sudo service mbc20-daemon-Daemon1 stop
sudo service mbc20-daemon-Daemon1 restart
```

### Kontrola procesu i PID

```bash
# Aktualne procesy daemona (wszystkie instancje)
ps aux | grep mbc20_auto_daemon.py | grep -v grep

# PID z pliku dla tej instancji
cat /var/run/mbc20-daemon-Daemon1.pid
```

### Logi

```bash
tail -f ~/Daemon1/auto-minter-gui/mbc20_history.log
tail -f ~/Daemon1/daemon.log
```

Jeśli logi pokazują:

- `Daemon invoked; pid=...`
- `Daemon start profile=...`
- `[AUTO-MINT] Creating post...`
- `Status 201 Body: {"success":true,...}`

to daemon działa i mintuje poprawnie.
