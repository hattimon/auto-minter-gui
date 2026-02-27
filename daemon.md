# 🚀 MBC20 Daemon — Installation & Usage Guide

**Choose language / Wybierz język:**  
👉 [English](#english)   👉 [Polski](#polski)  


---

<a id="english"></a>

# 🌍 English

## 🧠 What is MBC20 Daemon

MBC20 Daemon is a lightweight background worker that automatically mints MBC‑20 tokens from the selected profile at defined time intervals.   
Configuration is handled through a dedicated daemon GUI, and all configuration files and logs are shared with the main Auto Minter GUI.   


---

## ⚙️ Requirements

- 🪟 Windows 7 / 8 / 10 / 11 64‑bit  
- 🐍 Python 3.10+ available as `python` in PATH  
- 🚀 Auto Minter GUI  
  - started from source using `python main.py`  
  - or standalone executable `auto-minter-gui-<version>-windows-x86_64.exe`  


---

## 📂 Daemon Files

Inside the project directory the daemon uses the following files:   

- 🛠 `mbc20_auto_daemon.py` — daemon worker  
- 🖥 `mbc20_daemon_config_gui.py` — daemon configuration GUI  
- 🔁 Shared files  
  - `mbc20_profiles.json` — token profiles  
  - `mbc20_daemon_settings.json` — daemon settings  
  - `mbc20_history.log` — shared application log  
  - `mbc20_daemon.lock` — daemon lock file  

> If you are using the EXE version, all these files **must be located in the same folder** as `auto-minter-gui-<version>-windows-x86_64.exe`.  
> This ensures shared configuration and logging.  


---

## 🪄 Automatic Installation (Windows)

The repository provides a PowerShell installer `install-daemon.ps1` that:  

- 📥 downloads daemon files into the current project directory  
- 📦 optionally installs Python dependencies  
- 🔗 creates a **MBC20 Daemon GUI** shortcut  
- 🚀 copies the shortcut into the Windows Startup folder  


### 📥 Download Installer

Open PowerShell and navigate to your project directory:   

```powershell
cd "C:\path\to\auto-minter-gui"
```

Download the installer script:   

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/install-daemon.ps1" `
  -OutFile "install-daemon.ps1"
```


### ▶️ Run Installer

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install-daemon.ps1
```

The installer will:  

- ask for language selection  
- detect Windows and Python  
- confirm project directory  
- download daemon files  
- optionally install dependencies  
- create startup shortcut  

After completion:  

- daemon GUI starts automatically on next login  
- enable **Start daemon at startup** inside the GUI to auto‑run the background worker  


---

## 🖥 Manual Start

You can manually start the daemon GUI:   

```powershell
cd "C:\path\to\auto-minter-gui"
python mbc20_daemon_config_gui.py
```

The GUI will:  

- load or create daemon settings  
- load token profiles  
- show shared logs  

You can then:  

- save settings  
- start daemon manually  
- enable startup option  


---

## 🔁 Crash Recovery

After a system crash:  

- GUI launches again  
- daemon restarts automatically if enabled  
- old lock file is replaced  
- fresh session starts cleanly  


---

## ⚡ Quick Summary

Place `install-daemon.ps1` in your Auto Minter GUI directory.  

Run:  

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install-daemon.ps1
```

Select language and confirm installation.  

Daemon GUI will auto‑start with Windows and can launch the worker automatically.  


---

<a id="polski"></a>

# 🇵🇱 Polski

## 🧠 Czym jest MBC20 Daemon

MBC20 Daemon to lekki proces działający w tle, który automatycznie mintuje tokeny MBC‑20 z wybranego profilu w ustalonych interwałach czasowych.   
Konfiguracja odbywa się przez osobne GUI daemona, a wszystkie pliki konfiguracyjne i logi są współdzielone z głównym GUI Auto Minter.   


---

## ⚙️ Wymagania

- 🪟 Windows 7 / 8 / 10 / 11 64‑bit  
- 🐍 Python 3.10+ dostępny jako `python` w PATH  
- 🚀 Główne GUI Auto Minter  
  - uruchamiane z kodu `python main.py`  
  - lub jako plik `auto-minter-gui-<version>-windows-x86_64.exe`  


---

## 📂 Pliki daemona

W katalogu projektu daemon korzysta z:  

- 🛠 `mbc20_auto_daemon.py` — worker daemona  
- 🖥 `mbc20_daemon_config_gui.py` — GUI konfiguracji  
- 🔁 Pliki współdzielone  
  - `mbc20_profiles.json` — profile tokenów  
  - `mbc20_daemon_settings.json` — ustawienia  
  - `mbc20_history.log` — wspólny log  
  - `mbc20_daemon.lock` — lockfile  

> Przy użyciu wersji EXE wszystkie pliki **muszą znajdować się w tym samym folderze**, co plik EXE.  
> Zapewnia to współdzieloną konfigurację i logowanie.  


---

## 🪄 Automatyczna instalacja

Repozytorium zawiera instalator PowerShell `install-daemon.ps1`, który:  

- 📥 pobiera pliki daemona  
- 📦 instaluje zależności  
- 🔗 tworzy skrót GUI  
- 🚀 dodaje go do autostartu  


### 📥 Pobranie

```powershell
cd "C:\ścieżka\do\auto-minter-gui"
```

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/scripts/install-daemon.ps1" `
  -OutFile "install-daemon.ps1"
```


### ▶️ Uruchomienie

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install-daemon.ps1
```

Instalator:  

- zapyta o język  
- sprawdzi system  
- pobierze pliki  
- opcjonalnie zainstaluje zależności  
- doda skrót do autostartu  

Po zakończeniu:  

- GUI daemona uruchomi się przy starcie systemu  
- w GUI zaznacz **Start daemona przy starcie**, aby uruchamiać worker automatycznie  


---

## 🖥 Ręczne uruchomienie

```powershell
cd "C:\ścieżka\do\auto-minter-gui"
python mbc20_daemon_config_gui.py
```

GUI umożliwia:  

- konfigurację  
- ręczny start  
- włączenie autostartu  


---

## 🔁 Odzyskiwanie po awarii

Po nagłym wyłączeniu:  

- GUI startuje ponownie  
- daemon uruchamia się na nowo  
- lockfile zostaje nadpisany  
- startuje świeża sesja  


---

## ⚡ Quick Summary

Umieść `install-daemon.ps1` w katalogu projektu.  

Uruchom:  

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install-daemon.ps1
```

Po instalacji GUI daemona będzie uruchamiać się automatycznie wraz z systemem.  
