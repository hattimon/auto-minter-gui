# Build Instructions (DEB + EXE)

Unified build instructions for: - Debian/Ubuntu (.deb) - Windows (.exe)

Languages: English + Polish

============================================================
====================== DEB BUILD ===========================
============================================================

## 🇬🇧 English (DEB)

### Quick Installation (one-liner from GitHub)

Build and install directly without cloning:

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- 0.2.1
```

### Non-interactive with description

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh   | VERSION=0.2.1 DESCRIPTION="Improved solver + random titles" bash
```

### Interactive installation

``` bash
cd ~/auto-minter-gui

curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh -o build-deb.sh
chmod +x build-deb.sh
./build-deb.sh
```

### After installation

``` bash
auto-minter-gui
```

Install path: /opt/auto-minter-gui/

### Uninstall

``` bash
sudo dpkg -r auto-minter-gui
```

### Requirements

-   git
-   python3-venv
-   imagemagick

------------------------------------------------------------------------

## 🇵🇱 Polski (DEB)

### Szybka instalacja (one-liner)

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- 0.2.1
```

### Tryb nieinteraktywny z opisem

``` bash
curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh   | VERSION=0.2.1 DESCRIPTION="Ulepszony solver + losowe tytuły" bash
```

### Tryb interaktywny

``` bash
cd ~/auto-minter-gui

curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh -o build-deb.sh
chmod +x build-deb.sh
./build-deb.sh
```

Po instalacji:

``` bash
auto-minter-gui
```

Ścieżka instalacji: /opt/auto-minter-gui/

Odinstalowanie:

``` bash
sudo dpkg -r auto-minter-gui
```

Wymagania:

-   git
-   python3-venv
-   imagemagick

============================================================
====================== WINDOWS EXE =========================
============================================================

## 🇬🇧 English (Windows)

### Interactive

``` powershell
cd ~/auto-minter-gui
.uild-exe.ps1
```

### Non-interactive

``` powershell
$env:VERSION="0.1.5"; $env:DESCRIPTION="Improved solver + random titles"; .uild-exe.ps1
```

### One-liner

``` powershell
powershell -Command "$env:VERSION='0.1.5'; $env:DESCRIPTION='test release'; & '.uild-exe.ps1'"
```

Output file: auto-minter-gui-0.1.5-windows-x86_64.exe

Requirements: - Windows 10/11 - git - python 3.9+ - PowerShell 5.1+

------------------------------------------------------------------------

## 🇵🇱 Polski (Windows)

### Tryb interaktywny

``` powershell
cd ~/auto-minter-gui
.uild-exe.ps1
```

### Tryb nieinteraktywny

``` powershell
$env:VERSION="0.1.5"; $env:DESCRIPTION="ulepszony solver + nowe tytuły"; .uild-exe.ps1
```

### Jednolinijkowo

``` powershell
powershell -Command "$env:VERSION='0.1.5'; $env:DESCRIPTION='test release'; & '.uild-exe.ps1'"
```

Plik wynikowy: auto-minter-gui-0.1.5-windows-x86_64.exe

Wymagania: - Windows 10/11 - git - python 3.9+ - PowerShell 5.1+

============================================================ Security

Review scripts before running:
https://github.com/hattimon/auto-minter-gui/blob/main/build-deb.sh
https://github.com/hattimon/auto-minter-gui/blob/main/build-exe.ps1
