#!/usr/bin/env bash
set -e

# =============================================================================
#  build-deb.sh   –   buduje .deb z Auto Minter GUI
#  Domyślny język: angielski
# =============================================================================

REPO_DIR="$(pwd)"
VENV_DIR="$REPO_DIR/.venv"

# Domyślny język
LANG="en"

# ──────────────────────────────────────────────────────────────────────────────
# Pytanie o zmianę języka na polski (na samym początku)
# ──────────────────────────────────────────────────────────────────────────────
echo "Default language: English"
echo -n "Would you like to switch to Polish? [y/N]: "
read -r switch_to_pl
if [[ "$switch_to_pl" =~ ^[Yy]$ ]]; then
    LANG="pl"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Komunikaty w zależności od wybranego języka
# ──────────────────────────────────────────────────────────────────────────────
if [[ "$LANG" == "pl" ]]; then
    MSG_WELCOME="Tworzenie nowej wersji pakietu .deb – Auto Minter GUI"
    MSG_VERSION="Podaj numer wersji (np. 0.2.1):"
    MSG_DESC="Krótki opis zmian w tej wersji:"
    MSG_LANG_SWITCH="Opis jest po polsku. Czy chcesz przełączyć język na angielski? [y/N]: "
    MSG_CONFIRM="Kontynuować? [t/N]: "
    MSG_BUILDING="Buduję wersję"
    MSG_ICON_MISSING="Brak pliku ikony:"
    MSG_BINARY_MISSING="Brak skompilowanej binarki:"
    MSG_IMAGEMAGICK="Zainstaluj: sudo apt install imagemagick"
    MSG_SUCCESS="Gotowy pakiet:"
    MSG_INSTALL="Instalacja jednym poleceniem:"
    MSG_RUN="Uruchomienie:"
    MSG_UNINSTALL="Deinstalacja:"
else
    MSG_WELCOME="Building new .deb package – Auto Minter GUI"
    MSG_VERSION="Enter version number (e.g. 0.2.1):"
    MSG_DESC="Short description of changes in this release:"
    MSG_LANG_SWITCH="Description is in Polish. Would you like to switch language to English? [y/N]: "
    MSG_CONFIRM="Continue? [y/N]: "
    MSG_BUILDING="Building version"
    MSG_ICON_MISSING="Missing icon file:"
    MSG_BINARY_MISSING="Missing built binary:"
    MSG_IMAGEMAGICK="Install: sudo apt install imagemagick"
    MSG_SUCCESS="Package ready:"
    MSG_INSTALL="Install with one command:"
    MSG_RUN="Run:"
    MSG_UNINSTALL="Uninstall:"
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "$MSG_WELCOME"
echo "══════════════════════════════════════════════════════════════"

# Wersja
echo "$MSG_VERSION"
read -r VERSION
[ -z "$VERSION" ] && { echo "Version cannot be empty"; exit 1; }

# Opis wersji
echo ""
echo "$MSG_DESC"
read -r RELEASE_DESC
[ -z "$RELEASE_DESC" ] && RELEASE_DESC="(no description provided)"

# ──────────────────────────────────────────────────────────────────────────────
# Inteligentne pytanie o zmianę języka na podstawie języka opisu
# ──────────────────────────────────────────────────────────────────────────────
if [[ "$RELEASE_DESC" =~ [ąćęłńóśźżĄĆĘŁŃÓŚŹŻ] ]]; then
    # Wygląda na polski → pytamy o angielski
    echo ""
    echo "$MSG_LANG_SWITCH"
    read -r switch_to_en
    if [[ "$switch_to_en" =~ ^[Yy]$ ]]; then
        LANG="en"
        # przeładowanie komunikatów na angielski
        MSG_WELCOME="Building new .deb package – Auto Minter GUI"
        MSG_BUILDING="Building version"
        MSG_SUCCESS="Package ready:"
        MSG_INSTALL="Install with one command:"
        MSG_RUN="Run:"
        MSG_UNINSTALL="Uninstall:"
    fi
else
    # Wygląda na angielski → pytamy o polski
    echo ""
    echo "Description appears to be in English. Would you like to switch to Polish? [y/N]: "
    read -r switch_to_pl_late
    if [[ "$switch_to_pl_late" =~ ^[Yy]$ ]]; then
        LANG="pl"
        MSG_WELCOME="Tworzenie nowej wersji pakietu .deb – Auto Minter GUI"
        MSG_BUILDING="Buduję wersję"
        MSG_SUCCESS="Gotowy pakiet:"
        MSG_INSTALL="Instalacja jednym poleceniem:"
        MSG_RUN="Uruchomienie:"
        MSG_UNINSTALL="Deinstalacja:"
    fi
fi

echo ""
echo "→ Version: $VERSION"
echo "→ Description: $RELEASE_DESC"
echo ""
echo -n "$MSG_CONFIRM"
read -r confirm
[[ "$confirm" =~ ^[nN]$ ]] && { echo "Cancelled."; exit 0; }

# ──────────────────────────────────────────────────────────────────────────────
# venv + build
# ──────────────────────────────────────────────────────────────────────────────

[ ! -d "$VENV_DIR" ] && python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt || true
pip install pyinstaller

pyinstaller --onefile --noconsole --name auto-minter-gui main.py

# ──────────────────────────────────────────────────────────────────────────────
# Budowanie .deb
# ──────────────────────────────────────────────────────────────────────────────

ICON_SRC="$REPO_DIR/icons/auto-minter.ico"
BIN_SRC="$REPO_DIR/dist/auto-minter-gui"
PKG_DIR="auto-minter-gui_${VERSION}_amd64"
DEB_FILE="auto-minter-gui-${VERSION}-linux-amd64.deb"

command -v convert >/dev/null || { echo "$MSG_IMAGEMAGICK"; exit 1; }
[ -f "$ICON_SRC" ]  || { echo "$MSG_ICON_MISSING $ICON_SRC"; exit 1; }
[ -f "$BIN_SRC" ]   || { echo "$MSG_BINARY_MISSING $BIN_SRC"; exit 1; }

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

dpkg-deb --build "$PKG_DIR"
mv "${PKG_DIR}.deb" "$DEB_FILE"

# ──────────────────────────────────────────────────────────────────────────────
# Podsumowanie + instalacja online
# ──────────────────────────────────────────────────────────────────────────────

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "$MSG_SUCCESS $DEB_FILE"
echo "══════════════════════════════════════════════════════════════"
ls -lh "$DEB_FILE"

echo ""
echo "Quick install / uninstall:"
if [[ "$LANG" == "pl" ]]; then
    echo "  Instalacja (z internetu):"
    echo "    curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | VERSION=$VERSION bash"
    echo "  Deinstalacja:"
    echo "    sudo dpkg -r auto-minter-gui"
else
    echo "  Install (directly from internet):"
    echo "    curl -sSL https://raw.githubusercontent.com/hattimon/auto-minter-gui/main/build-deb.sh | VERSION=$VERSION bash"
    echo "  Uninstall:"
    echo "    sudo dpkg -r auto-minter-gui"
fi

deactivate
echo ""
echo "Done. Virtual environment deactivated."
