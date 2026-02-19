# =============================================================================
# build-exe.ps1
# Buduje portable .exe dla Auto Minter GUI na Windows
# Użycie:
#   .\build-exe.ps1                        → interaktywny
#   .\build-exe.ps1 0.1.5 "nowy opis"      → nieinteraktywny
# =============================================================================

param (
    [string]$VERSION = $env:VERSION,
    [string]$DESCRIPTION = $env:DESCRIPTION
)

$ErrorActionPreference = "Stop"

$REPO_DIR = Get-Location
$VENV_DIR = Join-Path $REPO_DIR ".venv"
$ICON_SRC = Join-Path $REPO_DIR "icons\auto-minter.ico"

# ─────────────────────────────────────────────────────────────────────────────
# Sprawdzenie wymagań
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "Checking required tools..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ git missing → install from https://git-scm.com/" -ForegroundColor Red
    exit 1
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ python missing → install from https://www.python.org/" -ForegroundColor Red
    exit 1
}

Write-Host "→ Basic requirements OK" -ForegroundColor Green
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# Domyślny język + tryb
# ─────────────────────────────────────────────────────────────────────────────
$LANG = "en"
$INTERACTIVE = [string]::IsNullOrEmpty($VERSION)

if (-not $INTERACTIVE) {
    $RELEASE_DESC = if ($DESCRIPTION) { $DESCRIPTION } else { "(no description)" }
    Write-Host "Non-interactive mode" -ForegroundColor Cyan
    Write-Host "Version     : $VERSION"
    Write-Host "Description : $RELEASE_DESC"
} 

function Load-Messages {
    if ($LANG -eq "pl") {
        $script:MSG_WELCOME     = "Tworzenie portable .exe – Auto Minter GUI"
        $script:MSG_VERSION     = "Podaj numer wersji (np. 0.1.5): "
        $script:MSG_DESC        = "Krótki opis zmian: "
        $script:MSG_LANG_PROMPT = "Opis wygląda na polski. Przełączyć język na polski? [Y/n] "
        $script:MSG_CONFIRM     = "Kontynuować? [Y/n] "
        $script:MSG_BUILDING    = "Buduję wersję"
        $script:MSG_ICON_ERR    = "Brak ikony:"
        $script:MSG_BIN_ERR     = "Nie zbudowano binarki:"
        $script:MSG_SUCCESS     = "Gotowy plik:"
        $script:MSG_RUN         = "Uruchom:"
    } else {
        $script:MSG_WELCOME     = "Building portable .exe – Auto Minter GUI"
        $script:MSG_VERSION     = "Enter version number (e.g. 0.1.5): "
        $script:MSG_DESC        = "Short description of changes: "
        $script:MSG_LANG_PROMPT = "Description appears to be in Polish. Switch to Polish? [Y/n] "
        $script:MSG_CONFIRM     = "Continue? [Y/n] "
        $script:MSG_BUILDING    = "Building version"
        $script:MSG_ICON_ERR    = "Missing icon:"
        $script:MSG_BIN_ERR     = "Binary not built:"
        $script:MSG_SUCCESS     = "Ready file:"
        $script:MSG_RUN         = "Run:"
    }
}

Load-Messages

# ─────────────────────────────────────────────────────────────────────────────
# Tryb interaktywny
# ─────────────────────────────────────────────────────────────────────────────
if ($INTERACTIVE) {
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host $MSG_WELCOME -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

    $VERSION = Read-Host $MSG_VERSION
    if ([string]::IsNullOrWhiteSpace($VERSION)) { Write-Host "Version cannot be empty" -ForegroundColor Red; exit 1 }

    $RELEASE_DESC = Read-Host $MSG_DESC
    if ([string]::IsNullOrWhiteSpace($RELEASE_DESC)) { $RELEASE_DESC = "(no description)" }

    # Wykrywanie języka opisu
    if ($RELEASE_DESC -cmatch "[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]") {
        $answer = Read-Host $MSG_LANG_PROMPT
        if ($answer -notmatch "^[nN]") {
            $LANG = "pl"
            Load-Messages
        }
    } else {
        $answer = Read-Host "Description appears English. Switch to Polish? [y/N]"
        if ($answer -match "^[Yy]") {
            $LANG = "pl"
            Load-Messages
        }
    }

    Write-Host ""
    Write-Host "→ Version     : $VERSION"
    Write-Host "→ Description : $RELEASE_DESC"
    Write-Host ""
    $confirm = Read-Host $MSG_CONFIRM
    if ($confirm -match "^[nN]") { Write-Host "Anulowano." -ForegroundColor Yellow; exit 0 }
}

# ─────────────────────────────────────────────────────────────────────────────
# venv + instalacja + build
# ─────────────────────────────────────────────────────────────────────────────
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VENV_DIR
}

& "$VENV_DIR\Scripts\Activate.ps1"

Write-Host "Updating pip + installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt
pip install pyinstaller | Out-Null

Write-Host "Building EXE with PyInstaller..." -ForegroundColor Yellow
pyinstaller `
    --onefile `
    --noconsole `
    --name "auto-minter-gui" `
    --icon "$ICON_SRC" `
    main.py

# ─────────────────────────────────────────────────────────────────────────────
# Finalna nazwa pliku (Twój styl)
# ─────────────────────────────────────────────────────────────────────────────
$DIST_EXE = Join-Path $REPO_DIR "dist\auto-minter-gui.exe"
$FINAL_EXE = "auto-minter-gui-$VERSION-windows-x86_64.exe"

if (-not (Test-Path $DIST_EXE)) {
    Write-Host "$MSG_BIN_ERR dist\auto-minter-gui.exe" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $ICON_SRC)) {
    Write-Host "$MSG_ICON_ERR $ICON_SRC" -ForegroundColor Yellow
}

Copy-Item $DIST_EXE $FINAL_EXE -Force

# ─────────────────────────────────────────────────────────────────────────────
# Podsumowanie
# ─────────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "$MSG_SUCCESS $FINAL_EXE" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green

Get-Item $FINAL_EXE | Select-Object Name, Length, LastWriteTime

Write-Host ""
if ($LANG -eq "pl") {
    Write-Host "Uruchomienie:"
    Write-Host "  .\$FINAL_EXE" -ForegroundColor Cyan
} else {
    Write-Host "Run:"
    Write-Host "  .\$FINAL_EXE" -ForegroundColor Cyan
}

deactivate
Write-Host ""
Write-Host "Done. venv deactivated." -ForegroundColor Green
