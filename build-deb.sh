#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# build-deb.sh
# Buduje pakiet .deb dla Auto Minter GUI
# Użycie:
#   ./build-deb.sh               → tryb interaktywny
#   ./build-deb.sh 0.2.1 "opis"  → tryb nieinteraktywny
#   curl ... | bash -s -- 0.2.1 "opis wersji"
# =============================================================================

REPO_DIR="$(pwd)"
VENV_DIR="$REPO_DIR/.venv"
ICON_SRC="$REPO_DIR/icons/auto-minter.ico"

# ──────────────────────────────────────────────────────────────────────────────
# Sprawdzenie zależności systemowych
# ──────────────────────────────────────────────────────────────────────────────
echo "Checking required system tools..."

command -v git      >/dev/null || { echo "❌ git is missing → sudo apt install git"; exit 1; }
command -v python3  >/dev/null || { echo "❌ python3 is missing → sudo apt install python3"; exit 1; }
python3 -c "import venv" >/dev/null 2>&1 || { echo "❌ python3-venv is missing → sudo apt install python3-venv"; exit 1; }
command -v convert  >/dev/null || { echo "❌ imagemagick is missing → sudo apt install imagemagick"; exit 1; }

echo "→ System dependencies OK"
echo ""

# ──────────────────────────────────────────────────────────────────────────────
# Domyślny język + wykrywanie trybu
# ──────────────────────────────────────────────────────────────────────────────
LANG="en"

if [ $# -ge 1 ]; then
    VERSION="$1"
    RELEASE_DESC="${2:-no description provided}"
    INTERACTIVE=false
    echo "Non-interactive mode → version = $VERSION"
    echo "Description    → $RELEASE_DESC"
else
    INTERACTIVE=true
fi

# ──────────────────────────────────────────────────────────────────────────────
# Funkcja ładująca komunikaty w wybranym języku
# ──────────────────────────────────────────────────────────────────────────────
load_messages() {
    if [ "$LANG" = "pl" ]; then
        MSG_WELCOME="Tworzenie pakietu .deb – Auto Minter GUI"
        MSG_VERSION="Podaj numer wersji (np. 0.2.1): "
        MSG_DESC="Krótki opis tej wersji: "
        MSG_LANG_PROMPT="Opis wygląda na polski. Przełączyć na język polski? [Y/n] "
        MSG_CONFIRM="Kontynuować? [Y/n] "
        MSG_BUILDING="Buduję wersję"
        MSG_ICON_ERR="Brak ikony:"
        MSG_BIN_ERR="Brak binarki:"
        MSG_SUCCESS="Gotowy pakiet:"
        MSG_INSTALL="Instalacja:"
        MSG_RUN="Uruchom:"
        MSG_UNINSTALL="Deinstalacja:"
    else
        MSG_WELCOME="Building .deb package – Auto Minter GUI"
        MSG_VERSION="Enter version number (e.g. 0.2.1): "
        MSG_DESC="Short description of this release: "
        MSG_LANG_PROMPT="Description appears to be in Polish. Switch to Polish? [Y/n] "
        MSG_CONFIRM="Continue? [Y/n] "
        MSG_BUILDING="Building version"
        MSG_ICON_ERR="Missing icon:"
        MSG_BIN_ERR="Missing binary:"
        MSG_SUCCESS="Package ready:"
        MSG_INSTALL="Install:"
        MSG_RUN="Run:"
        MSG_UNINSTALL="Uninstall:"
    fi
}

load_messages

# ──────────────────────────────────────────────────────────────────────────────
# Tryb interaktywny – zbieranie danych
# ──────────────────────────────────────────────────────────────────────────────
if $INTERACTIVE; then
    echo "══════════════════════════════════════════════════════════════"
    echo "$MSG_WELCOME"
    echo "══════════════════════════════════════════════════════════════"

    echo -n "$MSG_VERSION"
    read -r VERSION
    [ -z "$VERSION" ] && { echo "Version cannot be empty"; exit 1; }

    echo -n "$MSG_DESC"
    read -r RELEASE_DESC
    [ -z "$RELEASE_DESC" ] && RELEASE_DESC="(no description provided)"

    # ───────────────────────────────────────────────────────────────
    # Inteligentne wykrywanie języka opisu i propozycja zmiany
    # ───────────────────────────────────────────────────────────────
    if [[ "$RELEASE_DESC" =~ [ąćęłńóśźżĄĆĘŁŃÓŚŹŻ] ]]; then
        # Prawdopodobnie polski
        echo ""
        echo -n "$MSG_LANG_PROMPT"
        read -r answer
        if [[ ! "$answer" =~ ^[nN]$ ]]; then
            LANG="pl"
            load_messages
        fi
    else
        # Prawdopodobnie angielski – pytamy o polski
        echo ""
        echo -n "Description appears to be English. Switch to Polish? [y/N]: "
        read -r answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            LANG="pl"
            load_messages
        fi
    fi

    echo ""
    echo "→ Version     : $VERSION"
    echo "→ Description : $RELEASE_DESC"
    echo ""
    echo -n "$MSG_CONFIRM"
    read -r confirm
    [[ "$confirm" =~ ^[nN]$ ]] && { echo "Cancelled."; exit 0; }
fi

# ──────────────────────────────────────────────────────────────────────────────
# venv + zależności + budowanie binarki
# ──────────────────────────────────────────────────────────────────────────────

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Updating pip & installing dependencies..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt || echo "Warning: some requirements failed to install"
pip install pyinstaller >/dev/null || true

echo "Building binary with PyInstaller..."
pyinstaller --onefile --noconsole --name auto-minter-gui main.py

# ──────────────────────────────────────────────────────────────────────────────
# Zmienne .deb
# ──────────────────────────────────────────────────────────────────────────────

BIN_SRC="$REPO_DIR/dist/auto-minter-gui"
PKG_DIR="auto-minter-gui_${VERSION}_amd64"
DEB_FILE="auto-minter-gui-${VERSION}-linux-amd64.deb"

[ -f "$ICON_SRC" ]  || { echo "$MSG_ICON_ERR $ICON_SRC"; exit 1; }
[ -f "$BIN_SRC" ]   || { echo "$MSG_BIN_ERR $BIN_SRC"; exit 1; }

rm -rf "$PKG_DIR" "$DEB_FILE" 2>/dev/null || true

mkdir -p "$PKG_DIR"/{DEBIAN,opt/auto-minter-gui,usr/share/{applications,icons/hicolor/64x64/apps}}

cp "$BIN_SRC" "$PKG_DIR/opt/auto-minter-gui/"
chmod 755 "$PKG_DIR/opt/auto-minter-gui/auto-minter-gui"

convert "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/64x64/apps/auto-minter-gui.png" 2>/dev/null || true

cat > "$PKG_DIR/usr/share/applications/auto-minter-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Auto Minter GUI
Comment=MBC-20 Auto-Minter v$VERSION – $RELEASE_DESC
Exec=/opt/auto-minter-gui/auto-minter-gui
Icon=auto-minter-gui
Terminal=false
Categories=Utility;Network;
EOF

cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: auto-minter-gui
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: hattimon
Depends: python3
Description: Auto Minter GUI v$VERSION
 $RELEASE_DESC
 .
 MBC-20 Auto-Minter – GUI minting tool
EOF

cat > "$PKG_DIR/DEBIAN/postinst" << EOF
#!/bin/sh
set -e
update-desktop-database 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
echo "Auto Minter GUI v$VERSION installed in /opt/auto-minter-gui"
echo "Run: auto-minter-gui"
exit 0
EOF
chmod +x "$PKG_DIR/DEBIAN/postinst"

echo "$MSG_BUILDING v$VERSION – $RELEASE_DESC"
dpkg-deb --build "$PKG_DIR"
mv "${PKG_DIR}.deb" "$DEB_FILE"

# ──────────────────────────────────────────────────────────────────────────────
# Podsumowanie + szybka instalacja online
# ──────────────────────────────────────────────────────────────────────────────

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "$MSG_SUCCESS $DEB_FILE"
echo "══════════════════════════════════════════════════════════════"
ls -lh "$DEB_FILE"

echo ""
if [ "$LANG" = "pl" ]; then
    echo "Szybka instalacja z GitHub (dla przyszłych wydań):"
    echo "  curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- $VERSION"
    echo ""
    echo "Deinstalacja:"
    echo "  sudo dpkg -r auto-minter-gui"
else
    echo "Quick install from GitHub (for future releases):"
    echo "  curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | bash -s -- $VERSION"
    echo ""
    echo "Uninstall:"
    echo "  sudo dpkg -r auto-minter-gui"
fi

deactivate
echo ""
echo "Done. venv deactivated."
