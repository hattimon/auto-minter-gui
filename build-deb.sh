#!/bin/bash
set -e

# ------------------------------------------------------------------------------
#   Skrypt: clone → venv → build binary → build .deb z pytaniem o język i opis
# ------------------------------------------------------------------------------

REPO_URL="https://github.com/hattimon/auto-minter-gui.git"
REPO_DIR="$HOME/auto-minter-gui"
VENV_DIR="$REPO_DIR/.venv"

# ──────────────────────────────────────────────────────────────────────────────
# Wybór języka
# ──────────────────────────────────────────────────────────────────────────────
echo "Wybierz język instalacji / Choose installation language:"
echo "  [1] English (default)"
echo "  [2] Polski"
echo -n "Wybór (1 lub 2) [domyślnie 1]: "

read -r LANG_CHOICE
if [[ "$LANG_CHOICE" == "2" ]]; then
    LANG="pl"
    MSG_WELCOME="Budowanie nowej wersji Auto Minter GUI"
    MSG_VERSION="Podaj numer wersji (tag release), np. 0.1.5:"
    MSG_DESC="Podaj krótki opis tej wersji (changelog):"
    MSG_BUILDING="Buduję wersję"
    MSG_ICON_MISSING="Brak pliku ikony:"
    MSG_BINARY_MISSING="Brak skompilowanej binarki:"
    MSG_INSTALL_IMAGEMAGICK="Zainstaluj: sudo apt install imagemagick"
    MSG_SUCCESS="SUKCES! Gotowy pakiet:"
    MSG_INSTALL_CMD="Instalacja:"
    MSG_RUN_CMD="Uruchomienie:"
    MSG_UNINSTALL_CMD="Deinstalacja:"
else
    LANG="en"
    MSG_WELCOME="Building new version of Auto Minter GUI"
    MSG_VERSION="Enter version number (release tag), e.g. 0.1.5:"
    MSG_DESC="Enter short description of this release (changelog):"
    MSG_BUILDING="Building version"
    MSG_ICON_MISSING="Missing icon file:"
    MSG_BINARY_MISSING="Missing built binary:"
    MSG_INSTALL_IMAGEMAGICK="Install: sudo apt install imagemagick"
    MSG_SUCCESS="SUCCESS! Package ready:"
    MSG_INSTALL_CMD="Installation:"
    MSG_RUN_CMD="Run:"
    MSG_UNINSTALL_CMD="Uninstall:"
fi

echo ""
echo "──────────────────────────────────────────────────────────────"
echo "$MSG_WELCOME"
echo "──────────────────────────────────────────────────────────────"

# Pobierz / aktualizuj repo
if [ -d "$REPO_DIR" ]; then
    echo "Aktualizuję istniejące repozytorium..."
    cd "$REPO_DIR"
    git pull origin main || { echo "Błąd podczas git pull"; exit 1; }
else
    echo "Klonuję repozytorium..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Wersja
echo ""
echo "$MSG_VERSION"
read -r VERSION
if [ -z "$VERSION" ]; then
    echo "Wersja nie może być pusta!"
    exit 1
fi

# Opis wersji (changelog / release note)
echo ""
echo "$MSG_DESC"
read -r RELEASE_DESC
if [ -z "$RELEASE_DESC" ]; then
    RELEASE_DESC="(no description provided)"
fi

echo ""
echo "→ Wersja: $VERSION"
echo "→ Opis:   $RELEASE_DESC"
echo ""
echo -n "Kontynuować? (t/n) [t]: "
read -r CONFIRM
[[ "$CONFIRM" =~ ^[nN]$ ]] && { echo "Anulowano."; exit 0; }

# ──────────────────────────────────────────────────────────────────────────────
# venv + zależności + budowanie binarki
# ──────────────────────────────────────────────────────────────────────────────

if [ ! -d "$VENV_DIR" ]; then
    echo "Tworzę wirtualne środowisko..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Aktualizuję pip i instaluję zależności..."
pip install --upgrade pip
pip install -r requirements.txt || echo "Ostrzeżenie: niektóre zależności nie zainstalowały się"
pip install pyinstaller

echo "Buduję binarkę PyInstaller..."
pyinstaller --onefile --noconsole --name auto-minter-gui main.py

# ──────────────────────────────────────────────────────────────────────────────
# Ścieżki i zmienne .deb
# ──────────────────────────────────────────────────────────────────────────────

ICON_SRC="$REPO_DIR/icons/auto-minter.ico"
BIN_SRC="$REPO_DIR/dist/auto-minter-gui"
PKG_DIR="auto-minter-gui_${VERSION}_amd64"
DEB_FILE="auto-minter-gui-${VERSION}-linux-amd64.deb"

echo "$MSG_BUILDING v$VERSION – $RELEASE_DESC"

# Sprawdzenia
command -v convert >/dev/null || { echo "$MSG_INSTALL_IMAGEMAGICK"; exit 1; }
[ -f "$ICON_SRC" ]  || { echo "$MSG_ICON_MISSING $ICON_SRC"; exit 1; }
[ -f "$BIN_SRC" ]   || { echo "$MSG_BINARY_MISSING $BIN_SRC"; exit 1; }

# Czyść stare pliki
rm -rf "$PKG_DIR" "$DEB_FILE" 2>/dev/null || true

# Struktura katalogów
mkdir -p "$PKG_DIR/DEBIAN" \
         "$PKG_DIR/opt/auto-minter-gui" \
         "$PKG_DIR/usr/share/applications" \
         "$PKG_DIR/usr/share/icons/hicolor/64x64/apps"

# Kopiuj binarkę
cp "$BIN_SRC" "$PKG_DIR/opt/auto-minter-gui/"
chmod 755 "$PKG_DIR/opt/auto-minter-gui/auto-minter-gui"

# Ikona
convert "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/64x64/apps/auto-minter-gui.png" 2>/dev/null

# .desktop
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

# control
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
 MBC-20 Auto-Minter – narzędzie do mintingu z graficznym interfejsem.
EOF

# postinst
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e
update-desktop-database 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
echo "Auto Minter GUI v(VERSION) zainstalowany w /opt/auto-minter-gui"
echo "Uruchom: auto-minter-gui"
exit 0
EOF
sed -i "s/(VERSION)/$VERSION/" "$PKG_DIR/DEBIAN/postinst"
chmod +x "$PKG_DIR/DEBIAN/postinst"

# Budowanie pakietu
echo "Buduję pakiet .deb..."
dpkg-deb --build "$PKG_DIR"
mv "${PKG_DIR}.deb" "$DEB_FILE"

# Podsumowanie
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "$MSG_SUCCESS $DEB_FILE"
echo "══════════════════════════════════════════════════════════════"
ls -lh "$DEB_FILE"

echo ""
echo "Informacje o pakiecie:"
dpkg-deb --info "$DEB_FILE"

echo ""
echo "$MSG_INSTALL_CMD"
echo "  sudo dpkg -i $DEB_FILE"
echo ""
echo "$MSG_RUN_CMD"
echo "  auto-minter-gui"
echo ""
echo "$MSG_UNINSTALL_CMD"
echo "  sudo dpkg -r auto-minter-gui"

deactivate
echo ""
echo "Gotowe. Środowisko venv zostało deaktywowane."
