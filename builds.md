# 🚀 Build Guide --- auto-minter-gui

Professional build instructions for Linux (.deb) and Windows (.exe)

------------------------------------------------------------------------

# 📚 Table of Contents

## 🌍 Choose Language

-   🇬🇧 [English](#-english)
-   🇵🇱 [Polski](#-polski)

------------------------------------------------------------------------

# 🇬🇧 English

## 🐧 Linux --- Debian / Ubuntu / MX Linux (.deb)

### ⚡ Quick Build (One-Liner)

Replace `0.2.1` with your desired version:

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- 0.2.1
```

------------------------------------------------------------------------

### 📝 Build with Custom Description

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | \
  VERSION=0.2.1 DESCRIPTION="Improved solver + random titles" bash
```

------------------------------------------------------------------------

### 💬 Interactive Mode

``` bash
cd ~/auto-minter-gui
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh -o build-deb.sh
chmod +x build-deb.sh
./build-deb.sh
```

------------------------------------------------------------------------

### 📦 Install After Build

``` bash
sudo dpkg -i auto-minter-gui-*.deb
auto-minter-gui
```

Install path:

    /opt/auto-minter-gui/

Uninstall:

``` bash
sudo dpkg -r auto-minter-gui
```

------------------------------------------------------------------------

### 📋 Requirements

``` bash
sudo apt update
sudo apt install git python3-venv imagemagick
```

------------------------------------------------------------------------

## 🪟 Windows --- Portable EXE (.exe)

### 💬 Interactive Mode

``` powershell
cd ~/auto-minter-gui
Remove-Item Env:VERSION,Env:DESCRIPTION -ErrorAction SilentlyContinue
Invoke-Expression ((Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content)
```

------------------------------------------------------------------------

### ⚡ Non-Interactive

``` powershell
Invoke-Expression ((Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content) -VERSION "0.1.5" -DESCRIPTION "Improved solver + random titles"
```

------------------------------------------------------------------------

### 🔁 Alternative (Environment Variables)

``` powershell
$env:VERSION="0.1.5"
$env:DESCRIPTION="Improved solver + random titles"

Invoke-Expression ((iwr "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content)
```

------------------------------------------------------------------------

Output file:

    auto-minter-gui-0.1.5-windows-x86_64.exe

Fully portable. No installer required.

------------------------------------------------------------------------

# 🇵🇱 Polski

## 🐧 Linux --- Debian / Ubuntu / MX Linux (.deb)

### ⚡ Szybka budowa

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- 0.2.1
```

------------------------------------------------------------------------

### 📝 Budowa z opisem zmian

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | \
  VERSION=0.2.1 DESCRIPTION="Ulepszony solver + losowe tytuły" bash
```

------------------------------------------------------------------------

### 💬 Tryb interaktywny

``` bash
cd ~/auto-minter-gui
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh -o build-deb.sh
chmod +x build-deb.sh
./build-deb.sh
```

------------------------------------------------------------------------

### 📦 Instalacja

``` bash
sudo dpkg -i auto-minter-gui-*.deb
auto-minter-gui
```

Ścieżka instalacji:

    /opt/auto-minter-gui/

Odinstalowanie:

``` bash
sudo dpkg -r auto-minter-gui
```

------------------------------------------------------------------------

### 📋 Wymagania

``` bash
sudo apt update
sudo apt install git python3-venv imagemagick
```

------------------------------------------------------------------------

## 🪟 Windows --- Portable EXE (.exe)

### 💬 Tryb interaktywny

``` powershell
cd ~/auto-minter-gui
Remove-Item Env:VERSION,Env:DESCRIPTION -ErrorAction SilentlyContinue
Invoke-Expression ((Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content)
```

------------------------------------------------------------------------

### ⚡ Tryb nieinteraktywny

``` powershell
Invoke-Expression ((Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content) -VERSION "0.1.5" -DESCRIPTION "Ulepszony solver + nowe tytuły"
```

------------------------------------------------------------------------

### 🔁 Alternatywa

``` powershell
$env:VERSION="0.1.5"
$env:DESCRIPTION="Ulepszony solver + nowe tytuły"

Invoke-Expression ((iwr "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-exe.ps1" -UseBasicParsing).Content)
```

------------------------------------------------------------------------

Plik wynikowy:

    auto-minter-gui-0.1.5-windows-x86_64.exe

W pełni przenośny. Bez instalatora.
