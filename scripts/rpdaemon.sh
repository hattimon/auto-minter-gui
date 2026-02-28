#!/bin/bash
# Raspberry Pi MBC20 headless daemon manager (rpdaemon.sh)

set -e

# ---------- Colors ----------
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
BOLD="\033[1m"
RESET="\033[0m"

# ---------- Basic context ----------
APP_USER="${SUDO_USER:-$USER}"
APP_DIR="$(pwd)"
APP_BASENAME="$(basename "${APP_DIR}")"
REPO_URL="https://github.com/hattimon/auto-minter-gui.git"
PYTHON_BIN="python3"
SERVICE_NAME="mbc20-daemon-${APP_BASENAME}"
LOG_FILE="${APP_DIR}/daemon.log"

AUTO_DIR="${APP_DIR}/auto-minter-gui"
ENV_FILE="${AUTO_DIR}/.env"
PROFILES_JSON="${AUTO_DIR}/mbc20_profiles.json"
SETTINGS_JSON="${AUTO_DIR}/mbc20_daemon_settings.json"

LANG="en"

# ---------- Texts (no diacritics) ----------
txt() {
  local key="$1"
  case "$LANG" in
    pl)
      case "$key" in
        title) echo "== Moltbook MBC20 Daemon menedzer (folder: ${APP_BASENAME}) ==";;
        choose_lang) echo "Wybierz jezyk:";;
        lang_en) echo "1) English";;
        lang_pl) echo "2) Polski";;
        main_menu) echo "Menu glowne:";;
        m_install) echo "1) Zainstaluj / odswiez daemon (headless)";;
        m_add_profile) echo "2) Dodaj nowy profil tokena";;
        m_edit_profile) echo "3) Edytuj profil tokena";;
        m_delete_profile) echo "4) Usun profil tokena";;
        m_select_profile) echo "5) Wybierz aktywny profil tokena";;
        m_logs) echo "6) Podglad logow daemona";;
        m_env) echo "7) Edytuj plik .env (API)";;
        m_autostart) echo "8) Wlacz / wylacz autostart daemona";;
        m_reindex) echo "9) Reindeksuj z historii logow";;
        m_exit) echo "10) Wyjscie";;
        prompt_choice) echo "Wybierz opcje";;
        installing) echo "Instalacja / aktualizacja headless daemona...";;
        done_ok) echo "Gotowe.";;

        ask_molt) echo "MOLTBOOK_API_KEY (puste = bez zmiany, przy pierwszej instalacji wymagane):";;
        ask_openai) echo "OPENAI_API_KEY (puste = brak/bez zmiany):";;
        ask_api_name) echo "MOLTBOOK_API_NAME (przyjazna nazwa serwera/API):";;

        ask_profile_name) echo "Nazwa profilu (np. GPT-mint):";;
        ask_tick) echo "Ticker tokena (np. GPT):";;
        ask_submolt) echo "Submolt (puste = domyslnie mbc20):";;
        ask_amount) echo "Ilosc tokenow na jeden mint (np. 100):";;
        ask_title) echo "Tytul posta (np. MBC20 Inscription):";;
        ask_comment) echo "Dodatkowy komentarz do postow (puste = brak):";;

        profiles_missing) echo "Brak pliku profili, najpierw zainstaluj/utworz profil.";;
        select_profile_header) echo "Dostepne profile:";;
        select_profile_prompt) echo "Wybierz numer profilu:";;

        env_menu1) echo "1) Edytuj w edytorze (nano)";;
        env_menu2) echo "2) Szybka aktualizacja wartosci";;
        env_menu3) echo "3) Powrot";;

        autostart_on) echo "Autostart jest WLACZONY. Wylaczyc? (y/n)";;
        autostart_off) echo "Autostart jest WYLACZONY. Wlaczyc? (y/n)";;
        autostart_now_on) echo "Autostart zostal wlaczony.";;
        autostart_now_off) echo "Autostart zostal wylaczony.";;

        logs_info) echo "Podglad logow (Ctrl+C aby wyjsc):";;
        reindex_info) echo "Reindeksacja z historii logow - uruchamiam...";;
        reindex_stats) echo "Statystyki reindeksacji (do uzupelnienia przez Pythona).";;
        confirm_delete) echo "Na pewno usunac ten profil? (y/n)";;
      esac
      ;;
    *)
      case "$key" in
        title) echo "== Moltbook MBC20 Daemon manager (folder: ${APP_BASENAME}) ==";;
        choose_lang) echo "Select language:";;
        lang_en) echo "1) English";;
        lang_pl) echo "2) Polski";;
        main_menu) echo "Main menu:";;
        m_install) echo "1) Install / refresh daemon (headless)";;
        m_add_profile) echo "2) Add new token profile";;
        m_edit_profile) echo "3) Edit token profile";;
        m_delete_profile) echo "4) Delete token profile";;
        m_select_profile) echo "5) Select active token profile";;
        m_logs) echo "6) Tail daemon logs";;
        m_env) echo "7) Edit .env file (API)";;
        m_autostart) echo "8) Enable / disable daemon autostart";;
        m_reindex) echo "9) Reindex from history logs";;
        m_exit) echo "10) Exit";;
        prompt_choice) echo "Choose option";;
        installing) echo "Installing / updating headless daemon...";;
        done_ok) echo "Done.";;

        ask_molt) echo "MOLTBOOK_API_KEY (empty = keep, required on first install):";;
        ask_openai) echo "OPENAI_API_KEY (empty = none/keep):";;
        ask_api_name) echo "MOLTBOOK_API_NAME (friendly server/API name):";;

        ask_profile_name) echo "Profile name (e.g. GPT-mint):";;
        ask_tick) echo "Token ticker (e.g. GPT):";;
        ask_submolt) echo "Submolt (empty = default mbc20):";;
        ask_amount) echo "Amount per mint (e.g. 100):";;
        ask_title) echo "Post title (e.g. MBC20 Inscription):";;
        ask_comment) echo "Extra comment in posts (empty = none):";;

        profiles_missing) echo "No profiles file, install/create profile first.";;
        select_profile_header) echo "Available profiles:";;
        select_profile_prompt) echo "Select profile number:";;

        env_menu1) echo "1) Edit in editor (nano)";;
        env_menu2) echo "2) Quick update values";;
        env_menu3) echo "3) Back";;

        autostart_on) echo "Autostart is ENABLED. Disable? (y/n)";;
        autostart_off) echo "Autostart is DISABLED. Enable? (y/n)";;
        autostart_now_on) echo "Autostart has been enabled.";;
        autostart_now_off) echo "Autostart has been disabled.";;

        logs_info) echo "Tailing logs (Ctrl+C to exit):";;
        reindex_info) echo "Reindexing from history logs - running...";;
        reindex_stats) echo "Reindex stats (to be printed by Python script).";;
        confirm_delete) echo "Really delete this profile? (y/n)";;
      esac
      ;;
  esac
}

# ---------- Language selection ----------
choose_language() {
  echo -e "${BOLD}${CYAN}$(txt title)${RESET}"
  echo
  echo "$(txt choose_lang)"
  echo "  $(txt lang_en)"
  echo "  $(txt lang_pl)"
  read -p "> " lang_choice
  case "$lang_choice" in
    2) LANG="pl" ;;
    *) LANG="en" ;;
  esac
}

# ---------- Headless install ----------
install_headless() {
  echo -e "${YELLOW}$(txt installing)${RESET}"

  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
      debian|ubuntu|raspbian) ;;
      *) echo -e "${RED}Unsupported distro ID=$ID (expected debian/ubuntu/raspbian).${RESET}";;
    esac
  fi

  sudo apt update
  sudo apt install -y git ${PYTHON_BIN} ${PYTHON_BIN}-venv jq

  if [ ! -d "${AUTO_DIR}" ]; then
    git clone "${REPO_URL}" "${AUTO_DIR}"
  else
    cd "${AUTO_DIR}"
    git pull
    cd "${APP_DIR}"
  fi

  cd "${AUTO_DIR}"

  if [ ! -d ".venv" ]; then
    ${PYTHON_BIN} -m venv .venv
  fi

  source .venv/bin/activate

  # headless deps only – no PyQt6, no pip upgrade
  pip install python-dotenv requests

  if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}.env found - you can update values.${RESET}"
  fi

  local NEW_MOLT NEW_OPENAI NEW_NAME
  read -p "$(txt ask_molt) " NEW_MOLT
  read -p "$(txt ask_openai) " NEW_OPENAI
  read -p "$(txt ask_api_name) " NEW_NAME

  touch "$ENV_FILE"
  cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)"

  set_kv() {
    local key="$1"
    local val="$2"
    if grep -q "^${key}=" "$ENV_FILE"; then
      [ -n "$val" ] && sed -i "s/^${key}=.*/${key}=${val}/" "$ENV_FILE"
    else
      [ -n "$val" ] && echo "${key}=${val}" >> "$ENV_FILE"
    fi
  }

  [ -n "$NEW_MOLT" ] && set_kv "MOLTBOOK_API_KEY" "$NEW_MOLT"
  [ -n "$NEW_OPENAI" ] && set_kv "OPENAI_API_KEY" "$NEW_OPENAI"
  [ -n "$NEW_NAME" ] && set_kv "MOLTBOOK_API_NAME" "$NEW_NAME"

  if [ ! -f "$PROFILES_JSON" ]; then
    add_profile
  fi

  if [ ! -f "$SETTINGS_JSON" ]; then
    local PROFILE_NAME
    PROFILE_NAME=$(jq -r '.profiles[0].name' "$PROFILES_JSON")
    cat > "$SETTINGS_JSON" <<EOF
{
  "profile_name": "${PROFILE_NAME}",
  "first_start_minutes": 1,
  "base_interval_minutes": 35,
  "retry_5xx_until_success": true,
  "retry_5xx_interval_minutes": 1,
  "use_static_backoff_for_other_errors": true,
  "static_backoff_minutes": 31,
  "start_daemon_on_launch": true,
  "language": "pl"
}
EOF
  fi

  cat > "${APP_DIR}/start_daemon.sh" <<EOF
#!/bin/bash
cd "${AUTO_DIR}"
source .venv/bin/activate
${PYTHON_BIN} auto_minter.py --daemon >> "${LOG_FILE}" 2>&1
EOF
  chmod +x "${APP_DIR}/start_daemon.sh"

  local SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
  sudo bash -c "cat > '${SERVICE_FILE}'" <<EOF
[Unit]
Description=Moltbook MBC20 Auto-Minter (${APP_BASENAME})
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${AUTO_DIR}
ExecStart=${APP_DIR}/start_daemon.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}.service"
  sudo systemctl restart "${SERVICE_NAME}.service"

  echo -e "${GREEN}$(txt done_ok)${RESET}"
}

# ---------- Add new token profile ----------
add_profile() {
  mkdir -p "${AUTO_DIR}"
  touch "$PROFILES_JSON"
  if [ ! -s "$PROFILES_JSON" ]; then
    echo '{"profiles": []}' > "$PROFILES_JSON"
  fi

  echo -e "${CYAN}$(txt ask_profile_name)${RESET}"
  read -p "> " PROFILE_NAME
  echo -e "${CYAN}$(txt ask_tick)${RESET}"
  read -p "> " TOKEN_TICK
  echo -e "${CYAN}$(txt ask_submolt)${RESET}"
  read -p "> " SUBMOLT
  [ -z "$SUBMOLT" ] && SUBMOLT="mbc20"
  echo -e "${CYAN}$(txt ask_amount)${RESET}"
  read -p "> " AMOUNT_PER_MINT
  echo -e "${CYAN}$(txt ask_title)${RESET}"
  read -p "> " TITLE
  echo -e "${CYAN}$(txt ask_comment)${RESET}"
  read -p "> " EXTRA_COMMENT

  RAND_ID=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c10)

  TMP=$(mktemp)
  jq ".profiles += [{
    \"name\": \"${PROFILE_NAME}\",
    \"tick\": \"${TOKEN_TICK}\",
    \"submolt\": \"${SUBMOLT}\",
    \"amount_per_mint\": \"${AMOUNT_PER_MINT}\",
    \"title\": \"${TITLE}\",
    \"extra_comment\": \"${EXTRA_COMMENT}\",
    \"daemon_header_suffix\": \"[Daemon Server ${RAND_ID}]\",
    \"use_llm_only_for_riddles\": true
  }]" "$PROFILES_JSON" > "$TMP"
  mv "$TMP" "$PROFILES_JSON"

  echo -e "${GREEN}Profile added: ${PROFILE_NAME}${RESET}"
}

# ---------- Edit existing token profile ----------
edit_profile() {
  if [ ! -f "$PROFILES_JSON" ]; then
    echo -e "${RED}$(txt profiles_missing)${RESET}"
    return
  fi

  echo -e "${CYAN}$(txt select_profile_header)${RESET}"
  jq -r '.profiles[].name' "$PROFILES_JSON" | nl -ba
  echo
  read -p "$(txt select_profile_prompt) " CHOICE
  INDEX=$((CHOICE-1))

  CURRENT=$(jq ".profiles[${INDEX}]" "$PROFILES_JSON")
  [ "$CURRENT" = "null" ] && { echo -e "${RED}Invalid choice${RESET}"; return; }

  CUR_NAME=$(echo "$CURRENT" | jq -r '.name')
  CUR_TICK=$(echo "$CURRENT" | jq -r '.tick')
  CUR_SUBMOLT=$(echo "$CURRENT" | jq -r '.submolt // "mbc20"')
  CUR_AMOUNT=$(echo "$CURRENT" | jq -r '.amount_per_mint')
  CUR_TITLE=$(echo "$CURRENT" | jq -r '.title // ""')
  CUR_COMMENT=$(echo "$CURRENT" | jq -r '.extra_comment // ""')

  echo "Current name: $CUR_NAME"
  echo "Current tick: $CUR_TICK"
  echo "Current submolt: $CUR_SUBMOLT"
  echo "Current amount_per_mint: $CUR_AMOUNT"
  echo "Current title: $CUR_TITLE"
  echo "Current comment: $CUR_COMMENT"
  echo

  read -p "New name (empty = keep): " NEW_NAME
  read -p "New tick (empty = keep): " NEW_TICK
  read -p "New submolt (empty = keep): " NEW_SUBMOLT
  read -p "New amount per mint (empty = keep): " NEW_AMOUNT
  read -p "New title (empty = keep): " NEW_TITLE
  read -p "New comment (empty = keep): " NEW_COMMENT

  [ -z "$NEW_NAME" ] && NEW_NAME="$CUR_NAME"
  [ -z "$NEW_TICK" ] && NEW_TICK="$CUR_TICK"
  [ -z "$NEW_SUBMOLT" ] && NEW_SUBMOLT="$CUR_SUBMOLT"
  [ -z "$NEW_AMOUNT" ] && NEW_AMOUNT="$CUR_AMOUNT"
  [ -z "$NEW_TITLE" ] && NEW_TITLE="$CUR_TITLE"
  [ -z "$NEW_COMMENT" ] && NEW_COMMENT="$CUR_COMMENT"

  TMP=$(mktemp)
  jq ".profiles[${INDEX}].name = \"${NEW_NAME}\" |
      .profiles[${INDEX}].tick = \"${NEW_TICK}\" |
      .profiles[${INDEX}].submolt = \"${NEW_SUBMOLT}\" |
      .profiles[${INDEX}].amount_per_mint = \"${NEW_AMOUNT}\" |
      .profiles[${INDEX}].title = \"${NEW_TITLE}\" |
      .profiles[${INDEX}].extra_comment = \"${NEW_COMMENT}\"" \
      "$PROFILES_JSON" > "$TMP"
  mv "$TMP" "$PROFILES_JSON"

  echo -e "${GREEN}Profile updated: ${NEW_NAME}${RESET}"
}

# ---------- Delete token profile ----------
delete_profile() {
  if [ ! -f "$PROFILES_JSON" ]; then
    echo -e "${RED}$(txt profiles_missing)${RESET}"
    return
  fi

  echo -e "${CYAN}$(txt select_profile_header)${RESET}"
  jq -r '.profiles[].name' "$PROFILES_JSON" | nl -ba
  echo
  read -p "$(txt select_profile_prompt) " CHOICE
  INDEX=$((CHOICE-1))

  NAME=$(jq -r ".profiles[${INDEX}].name" "$PROFILES_JSON")
  [ "$NAME" = "null" ] && { echo -e "${RED}Invalid choice${RESET}"; return; }

  read -p "$(txt confirm_delete) " ans
  case "$ans" in
    y|Y)
      TMP=$(mktemp)
      jq "del(.profiles[${INDEX}])" "$PROFILES_JSON" > "$TMP"
      mv "$TMP" "$PROFILES_JSON"
      echo -e "${YELLOW}Profile deleted: ${NAME}${RESET}"
      ;;
    *)
      ;;
  esac
}

# ---------- Select active token profile ----------
select_profile() {
  if [ ! -f "$PROFILES_JSON" ]; then
    echo -e "${RED}$(txt profiles_missing)${RESET}"
    return
  fi

  echo -e "${CYAN}$(txt select_profile_header)${RESET}"
  jq -r '.profiles[].name' "$PROFILES_JSON" | nl -ba
  echo
  read -p "$(txt select_profile_prompt) " CHOICE
  PROFILE_NAME=$(jq -r ".profiles[$((CHOICE-1))].name" "$PROFILES_JSON")

  mkdir -p "$(dirname "$SETTINGS_JSON")"
  touch "$SETTINGS_JSON"
  if [ ! -s "$SETTINGS_JSON" ]; then
    echo '{}' > "$SETTINGS_JSON"
  fi

  TMP=$(mktemp)
  jq --arg name "$PROFILE_NAME" '.profile_name = $name' "$SETTINGS_JSON" > "$TMP"
  mv "$TMP" "$SETTINGS_JSON"

  sudo systemctl restart "${SERVICE_NAME}" || true
  echo -e "${GREEN}Active profile: ${PROFILE_NAME}${RESET}"
}

# ---------- Edit .env ----------
edit_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}No .env file: $ENV_FILE${RESET}"
    return
  fi

  echo -e "${CYAN}Current .env values:${RESET}"
  grep -E '^(MOLTBOOK_API_KEY|OPENAI_API_KEY|MOLTBOOK_API_NAME)=' "$ENV_FILE" || true
  echo
  echo "$(txt env_menu1)"
  echo "$(txt env_menu2)"
  echo "$(txt env_menu3)"
  read -p "> " choice

  case "$choice" in
    1)
      ${EDITOR:-nano} "$ENV_FILE"
      ;;
    2)
      read -p "$(txt ask_molt) " NEW_MOLT
      read -p "$(txt ask_openai) " NEW_OPENAI
      read -p "$(txt ask_api_name) " NEW_NAME

      cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)"

      set_kv_env() {
        local key="$1"
        local val="$2"
        [ -z "$val" ] && return
        if grep -q "^${key}=" "$ENV_FILE"; then
          sed -i "s/^${key}=.*/${key}=${val}/" "$ENV_FILE"
        else
          echo "${key}=${val}" >> "$ENV_FILE"
        fi
      }

      set_kv_env "MOLTBOOK_API_KEY" "$NEW_MOLT"
      set_kv_env "OPENAI_API_KEY" "$NEW_OPENAI"
      set_kv_env "MOLTBOOK_API_NAME" "$NEW_NAME"

      echo -e "${GREEN}Updated .env${RESET}"
      ;;
    *)
      ;;
  esac
}

# ---------- Autostart on/off ----------
toggle_autostart() {
  local enabled
  enabled=$(systemctl is-enabled "${SERVICE_NAME}" 2>/dev/null || echo "disabled")
  if [ "$enabled" = "enabled" ]; then
    read -p "$(txt autostart_on) " ans
    case "$ans" in
      y|Y)
        sudo systemctl disable "${SERVICE_NAME}.service"
        sudo systemctl stop "${SERVICE_NAME}.service" || true
        echo -e "${YELLOW}$(txt autostart_now_off)${RESET}"
        ;;
    esac
  else
    read -p "$(txt autostart_off) " ans
    case "$ans" in
      y|Y)
        sudo systemctl enable "${SERVICE_NAME}.service"
        sudo systemctl restart "${SERVICE_NAME}.service"
        echo -e "${GREEN}$(txt autostart_now_on)${RESET}"
        ;;
    esac
  fi
}

# ---------- Logs ----------
tail_logs() {
  echo -e "${MAGENTA}$(txt logs_info)${RESET}"
  touch "$LOG_FILE"
  tail -f "$LOG_FILE"
}

# ---------- Reindex (placeholder) ----------
reindex_history() {
  echo -e "${YELLOW}$(txt reindex_info)${RESET}"
  cd "${AUTO_DIR}"
  source .venv/bin/activate
  python3 indexer_client.py --reindex-from-history
  echo -e "${GREEN}$(txt reindex_stats)${RESET}"
}

# ---------- Language + menu ----------
choose_language

main_menu() {
  while true; do
    echo
    echo -e "${BOLD}${CYAN}$(txt main_menu)${RESET}"
    echo -e "${YELLOW}$(txt m_install)${RESET}"
    echo -e "${YELLOW}$(txt m_add_profile)${RESET}"
    echo -e "${YELLOW}$(txt m_edit_profile)${RESET}"
    echo -e "${YELLOW}$(txt m_delete_profile)${RESET}"
    echo -e "${YELLOW}$(txt m_select_profile)${RESET}"
    echo -e "${YELLOW}$(txt m_logs)${RESET}"
    echo -e "${YELLOW}$(txt m_env)${RESET}"
    echo -e "${YELLOW}$(txt m_autostart)${RESET}"
    echo -e "${YELLOW}$(txt m_reindex)${RESET}"
    echo -e "${YELLOW}$(txt m_exit)${RESET}"
    echo
    read -p "$(txt prompt_choice): " choice
    case "$choice" in
      1) install_headless ;;
      2) add_profile ;;
      3) edit_profile ;;
      4) delete_profile ;;
      5) select_profile ;;
      6) tail_logs ;;
      7) edit_env ;;
      8) toggle_autostart ;;
      9) reindex_history ;;
      10) exit 0 ;;
      *) ;;
    esac
  done
}

main_menu

