# 🚀 Moltbook Auto-Minter GUI

[🇬🇧 English](README.md) • [🇵🇱 Polski](README_PL.md)

## Download v0.1.4

[![Windows EXE](https://img.shields.io/badge/Windows-EXE-blue)](https://github.com/hattimon/auto-minter-gui/releases/tag/v0.1.4)
[![Linux-DEB](https://img.shields.io/badge/Linux-DEB-green)](https://github.com/hattimon/auto-minter-gui/releases/tag/v0.1.4)

> Latest version: **v0.1.4** – smarter title randomization, flexible solver modes, and a safe return to gpt‑4.1‑mini

A user-friendly desktop application for creating and auto-minting  
**MBC-20** inscriptions on Moltbook,  
with integrated AI puzzle solving (lobster + LLM), flexible solver modes (enhanced rules/cache vs. LLM-only),  
smart title randomization, and mbc20.xyz indexer support.

------------------------------------------------------------------------

## ✨ Features

-   🖥️ **Modern PyQt6 GUI** -- Tabs: Main, History, .env Editor, Auto
    Mint  
-   🧠 **AI Brain Integration** -- Automatically solves Moltbook lobster
    puzzles using OpenAI  
-   🔄 **Auto-Mint Scheduler** -- Configurable intervals, smart backoff,
    max runs control  
-   📜 **History Log Viewer** -- Track posts and bulk re-index via
    mbc20.xyz API  
-   🌍 **Language Switcher** -- English / Polish interface  
-   🔐 **Built-in .env Editor** -- Manage API keys directly inside the
    app

------------------------------------------------------------------------

## 📋 Requirements

-   Python **3.10+** (recommended)
-   Git
-   Windows, Linux or macOS

### Python dependencies:

-   requests  
-   python-dotenv  
-   PyQt6

Install them via:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🚀 Getting Started

### 1️⃣ Clone Repository

``` bash
git clone https://github.com/hattimon/auto-minter-gui.git
cd auto-minter-gui
```

### 2️⃣ Configure Environment

Copy example configuration:

``` bash
cp .env.example .env
```

Edit `.env` and add:

``` env
MOLTBOOK_API_KEY=your_moltbook_api_key_here
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4.1-mini
```

-   `MOLTBOOK_API_KEY` -- Required for Moltbook posting & verification  
-   `OPENAI_API_KEY` -- Used for lobster puzzle solving  
-   `OPENAI_MODEL` -- Defaults to `gpt-4.1-mini` if not specified

Create OpenAI key:  
https://platform.openai.com/api-keys

------------------------------------------------------------------------

## 💻 Installation

### 🪟 Windows

``` powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Make sure Python is added to PATH.

------------------------------------------------------------------------

### 🐧 Linux / 🍎 macOS

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On some Linux distributions, additional Qt runtime libraries may be
required.

------------------------------------------------------------------------

## 🧩 Application Overview

### 📝 Main Tab

-   Create deploy / mint / transfer / link operations  
-   Randomize title  
-   Save and load token profiles  
-   Auto-verify posts with AI puzzle solver

### 🤖 AI Brain

-   Test OpenAI integration  
-   View expected vs actual lobster puzzle answers

### 📚 History

-   View `mbc20_history.log`  
-   Bulk re-index posts  
-   Skip indexed or errored entries

### ⚙️ .env Editor

-   Reload and edit environment configuration  
-   Instantly update API keys

### 🔁 Auto Mint

-   Configure minting intervals  
-   Smart exponential backoff on errors  
-   Infinite or limited run modes  
-   Background worker thread execution

------------------------------------------------------------------------

## Screenshots

### Main window  
![Main window](docs/screenshots/main-window.png)  

![Main window menu](docs/screenshots/main-window-menu.png)  

### Auto Mint tab  
![Auto Mint tab](docs/screenshots/auto-mint.png)  

### History & indexer  
![History tab](docs/screenshots/history-tab.png)  

### .env editor  
![.env editor](docs/screenshots/env-editor.png)  

------------------------------------------------------------------------

## 📂 Project Structure

| File | Description |
|------|------------|
| `main.py` | Application entry point |
| `mbc20_inscription_gui.py` | Main GUI and logic |
| `auto_minter.py` | Auto-mint scheduler |
| `lobster_solver.py` | OpenAI puzzle solver |
| `indexer_client.py` | mbc20.xyz API client |
| `moltbook_client.py` | Moltbook API wrapper |
| `.env.example` | Environment template |
| `requirements.txt` | Dependencies list |
| `build-deb.sh` | Build *.deb package |

------------------------------------------------------------------------  

## Quick Installation (one-liner from GitHub)

Build and install the latest version directly from GitHub without cloning the repository.

### Non-interactive (specify version)

```bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- 0.2.1
```

### Non-interactive with custom description

```bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh   | VERSION=0.2.1 DESCRIPTION="Improved solver + random titles" bash
```

### Interactive installation (recommended for manual builds)

```bash
# 1. Enter the repository directory
cd ~/auto-minter-gui   # or wherever you cloned the repository

# 2. Download or update the script (if not already present in the repo)
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh -o build-deb.sh

# 3. Make the script executable
chmod +x build-deb.sh

# 4. Run
./build-deb.sh
```

### After installation

```bash
auto-minter-gui
```

Install path:
```
/opt/auto-minter-gui/
```

### Uninstall

```bash
sudo dpkg -r auto-minter-gui
```

### Requirements

- git
- python3-venv
- imagemagick

### Security

Review the script before running:
https://github.com/hattimon/auto-minter-gui/blob/main/build-deb.sh

------------------------------------------------------------------------  

## 🤝 Contributing

1.  Fork the repository  
2.  Create feature branch  
3.  Commit changes  
4.  Push branch  
5.  Open Pull Request

Ideas, improvements and feature suggestions are welcome!

------------------------------------------------------------------------

## 📄 Polish Version

For Polish documentation see:

➡️ **[README_PL.md](README_PL.md)**
