param(
    [string]$RepoBaseUrl = "https://raw.githubusercontent.com/hattimon/auto-minter-gui/main"
)

$ErrorActionPreference = "Stop"

Write-Host "Select installer language / Wybierz jezyk instalatora:"
Write-Host "  1) English"
Write-Host "  2) Polski (bez ogonkow)"
$choice = Read-Host "[1/2]"

if ($choice -eq "2") { $LANG = "pl" } else { $LANG = "en" }

function Msg {
    param([string]$Key)
    switch ($Key) {

        "title" {
            if ($LANG -eq "pl") { "MBC20 Daemon - instalator (Windows)" }
            else { "MBC20 Daemon - installer (Windows)" }
        }
        "detected_os" {
            if ($LANG -eq "pl") { "Wykryty system: {0} ({1})" }
            else { "Detected OS: {0} ({1})" }
        }
        "win_family" {
            if ($LANG -eq "pl") { "Rodzina Windows: {0}" }
            else { "Windows family: {0}" }
        }
        "confirm_os" {
            if ($LANG -eq "pl") { "Wykryto system '{0}'. Kontynuowac z tym wykryciem? [Y/n]" }
            else { "Detected system '{0}'. Continue with this detection? [Y/n]" }
        }
        "enter_win" {
            if ($LANG -eq "pl") { "Podaj wersje Windows recznie (7 / 8 / 10 / 11 / other)" }
            else { "Enter Windows version manually (7 / 8 / 10 / 11 / other)" }
        }
        "python_check" {
            if ($LANG -eq "pl") { "Sprawdzanie Pythona..." }
            else { "Checking Python..." }
        }
        "python_missing" {
            if ($LANG -eq "pl") {
                "X Nie znaleziono Pythona w PATH. Zainstaluj Python 3.10+ i upewnij sie, ze 'python' dziala w terminalu. https://www.python.org/downloads/"
            } else {
                "X Python not found in PATH. Install Python 3.10+ and ensure 'python' is available in PATH. https://www.python.org/downloads/"
            }
        }
        "python_version" {
            if ($LANG -eq "pl") { "Wersja Pythona: {0}" }
            else { "Python version: {0}" }
        }
        "project_dir" {
            if ($LANG -eq "pl") { "Katalog projektu: {0}" }
            else { "Project directory: {0}" }
        }
        "confirm_install_here" {
            if ($LANG -eq "pl") { "Zainstalowac pliki daemona w tym folderze? [Y/n]" }
            else { "Install daemon files into this folder? [Y/n]" }
        }
        "aborted" {
            if ($LANG -eq "pl") { "Przerwano." }
            else { "Aborted." }
        }
        "files_to_download" {
            if ($LANG -eq "pl") { "Pliki do pobrania:" }
            else { "Files to download:" }
        }
        "proceed_download" {
            if ($LANG -eq "pl") { "Kontynuowac pobieranie? [Y/n]" }
            else { "Proceed with download? [Y/n]" }
        }
        "downloading" {
            if ($LANG -eq "pl") { "Pobieranie {0}..." }
            else { "Downloading {0}..." }
        }
        "download_failed" {
            if ($LANG -eq "pl") { "X Blad pobierania {0}: {1}" }
            else { "X Failed to download {0}: {1}" }
        }
        "download_ok" {
            if ($LANG -eq "pl") { "OK Pliki daemona pobrane do: {0}" }
            else { "OK Daemon files downloaded to: {0}" }
        }
        "install_deps_q" {
            if ($LANG -eq "pl") { "Zainstalowac/zaktualizowac zaleznosci z requirements.txt teraz? [Y/n]" }
            else { "Install/update Python dependencies from requirements.txt now? [Y/n]" }
        }
        "installing_deps" {
            if ($LANG -eq "pl") { "Instalowanie zaleznosci..." }
            else { "Installing dependencies..." }
        }
        "deps_ok" {
            if ($LANG -eq "pl") { "OK Zaleznosci zainstalowane." }
            else { "OK Dependencies installed." }
        }
        "shortcut_q" {
            if ($LANG -eq "pl") { "Utworzyc skrot GUI daemona i dodac go do autostartu Windows? [Y/n]" }
            else { "Create shortcut for daemon GUI and add it to Windows autostart? [Y/n]" }
        }
        "skip_shortcut" {
            if ($LANG -eq "pl") { "Pominieto tworzenie skrotu/autostartu." }
            else { "Skipping shortcut/autostart setup." }
        }
        "pythonw_missing_auto" {
            if ($LANG -eq "pl") { "Nie znaleziono pythonw.exe obok python.exe." }
            else { "pythonw.exe not found next to python.exe." }
        }
        "enter_pythonw" {
            if ($LANG -eq "pl") { "Podaj pelna sciezke do pythonw.exe (np. C:\Python312\pythonw.exe)" }
            else { "Enter full path to pythonw.exe (e.g. C:\Python312\pythonw.exe)" }
        }
        "pythonw_not_found" {
            if ($LANG -eq "pl") { "X Nie znaleziono pythonw.exe. Nie mozna stworzyc skrotu GUI." }
            else { "X pythonw.exe not found. Cannot create GUI-only shortcut." }
        }
        "daemon_gui_missing" {
            if ($LANG -eq "pl") { "X Nie znaleziono mbc20_daemon_config_gui.py w katalogu projektu." }
            else { "X mbc20_daemon_config_gui.py not found in project directory." }
        }
        "shortcut_target" {
            if ($LANG -eq "pl") { "Komenda skrotu:" }
            else { "Shortcut target command:" }
        }
        "shortcut_created_project" {
            if ($LANG -eq "pl") { "OK Skrot utworzony w katalogu projektu:" }
            else { "OK Shortcut created in project folder:" }
        }
        "startup_not_found" {
            if ($LANG -eq "pl") { "UWAGA: Nie znaleziono folderu autostartu uzytkownika, pomijam autostart." }
            else { "WARN: Startup folder not found for this user, skipping autostart." }
        }
        "shortcut_copied_startup" {
            if ($LANG -eq "pl") { "OK Skrot skopiowany do autostartu:" }
            else { "OK Shortcut copied to autostart:" }
        }
        "done" {
            if ($LANG -eq "pl") {
                "Gotowe. Przy nastepnym logowaniu GUI daemona uruchomi sie automatycznie. Pamietaj, aby w GUI zaznaczyc 'Wlacz daemona przy starcie'."
            } else {
                "Done. On next login, the daemon GUI will start automatically. Remember to enable 'Start daemon at startup' in the GUI."
            }
        }
    }
}

Write-Host "======================================================"
Write-Host ("  " + (Msg "title"))
Write-Host "======================================================"
Write-Host ""

$os = Get-CimInstance Win32_OperatingSystem
$caption = $os.Caption
$version = $os.Version
Write-Host ([string]::Format((Msg "detected_os"), $caption, $version))

if     ($caption -match "Windows 7")  { $winFamily = "7" }
elseif ($caption -match "Windows 8")  { $winFamily = "8" }
elseif ($caption -match "Windows 10") { $winFamily = "10" }
elseif ($caption -match "Windows 11") { $winFamily = "11" }
else  { $winFamily = "other" }

Write-Host ([string]::Format((Msg "win_family"), $winFamily))
Write-Host ""

$questionOs = [string]::Format((Msg "confirm_os"), $caption)
$answer = Read-Host $questionOs
if ($answer -match "^[nN]") {
    $winFamily = Read-Host (Msg "enter_win")
}
Write-Host ""

Write-Host (Msg "python_check")
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host (Msg "python_missing") -ForegroundColor Red
    exit 1
}

$pyVersion = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
Write-Host ([string]::Format((Msg "python_version"), $pyVersion))
Write-Host ""

$projectDir = Get-Location
Write-Host ([string]::Format((Msg "project_dir"), $projectDir))
Write-Host ""

$confirm = Read-Host (Msg "confirm_install_here")
if ($confirm -match "^[nN]") {
    Write-Host (Msg "aborted") -ForegroundColor Yellow
    exit 0
}

$filesToDownload = @(
    @{ Name = "mbc20_auto_daemon.py";       Url = "$RepoBaseUrl/mbc20_auto_daemon.py" },
    @{ Name = "mbc20_daemon_config_gui.py"; Url = "$RepoBaseUrl/mbc20_daemon_config_gui.py" },
    @{ Name = "auto_minter.py";            Url = "$RepoBaseUrl/auto_minter.py" },
    @{ Name = "indexer_client.py";         Url = "$RepoBaseUrl/indexer_client.py" },
    @{ Name = "lobster_solver.py";         Url = "$RepoBaseUrl/lobster_solver.py" },
    @{ Name = "moltbook_client.py";        Url = "$RepoBaseUrl/moltbook_client.py" },
    @{ Name = "requirements.txt";          Url = "$RepoBaseUrl/requirements.txt" }
)

Write-Host (Msg "files_to_download")
foreach ($f in $filesToDownload) {
    Write-Host "  - $($f.Name) <- $($f.Url)"
}
Write-Host ""

$confirm = Read-Host (Msg "proceed_download")
if ($confirm -match "^[nN]") {
    Write-Host (Msg "aborted") -ForegroundColor Yellow
    exit 0
}

foreach ($f in $filesToDownload) {
    $targetPath = Join-Path $projectDir $f.Name
    Write-Host ([string]::Format((Msg "downloading"), $f.Name))
    try {
        Invoke-WebRequest -Uri $f.Url -OutFile $targetPath -UseBasicParsing
    } catch {
        Write-Host ([string]::Format((Msg "download_failed"), $f.Name, $_.Exception.Message)) -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host ([string]::Format((Msg "download_ok"), $projectDir)) -ForegroundColor Green
Write-Host ""

if (Test-Path (Join-Path $projectDir "requirements.txt")) {
    $installDeps = Read-Host (Msg "install_deps_q")
    if ($installDeps -notmatch "^[nN]") {
        Write-Host ""
        Write-Host (Msg "installing_deps") -ForegroundColor Yellow
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        Write-Host (Msg "deps_ok") -ForegroundColor Green
        Write-Host ""
    }
}

$addShortcut = Read-Host (Msg "shortcut_q")
if ($addShortcut -match "^[nN]") {
    Write-Host (Msg "skip_shortcut")
    exit 0
}

$pythonPath = (Get-Command python).Source
$pythonDir  = Split-Path $pythonPath -Parent
$pythonw    = Join-Path $pythonDir "pythonw.exe"

if (-not (Test-Path $pythonw)) {
    Write-Host (Msg "pythonw_missing_auto") -ForegroundColor Yellow
    $pythonw = Read-Host (Msg "enter_pythonw")
}
if (-not (Test-Path $pythonw)) {
    Write-Host (Msg "pythonw_not_found") -ForegroundColor Red
    exit 1
}

$daemonGuiPath = Join-Path $projectDir "mbc20_daemon_config_gui.py"
if (-not (Test-Path $daemonGuiPath)) {
    Write-Host (Msg "daemon_gui_missing") -ForegroundColor Red
    exit 1
}

$shortcutTarget = "`"$pythonw`" `"$daemonGuiPath`""

Write-Host ""
Write-Host (Msg "shortcut_target")
Write-Host "  $shortcutTarget"
Write-Host ""

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcutPathProject = Join-Path $projectDir "MBC20 Daemon GUI.lnk"
$shortcut = $WScriptShell.CreateShortcut($shortcutPathProject)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments  = "`"$daemonGuiPath`""
$shortcut.WorkingDirectory = $projectDir
$shortcut.WindowStyle = 1
$shortcut.IconLocation = $pythonw
$shortcut.Save()

Write-Host (Msg "shortcut_created_project")
Write-Host "   $shortcutPathProject"
Write-Host ""

$startupDir = [Environment]::GetFolderPath("Startup")
if (-not (Test-Path $startupDir)) {
    Write-Host (Msg "startup_not_found") -ForegroundColor Yellow
    Write-Host "  Startup: $startupDir"
} else {
    $shortcutPathStartup = Join-Path $startupDir "MBC20 Daemon GUI.lnk"
    Copy-Item $shortcutPathProject $shortcutPathStartup -Force
    Write-Host (Msg "shortcut_copied_startup")
    Write-Host "   $shortcutPathStartup"
}

Write-Host ""
Write-Host (Msg "done")
