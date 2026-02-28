#!/bin/bash
# rpdaemon.sh - Moltbook MBC20 headless daemon manager v4
# Pelna instalacja od A do Z: apt, venv, psutil, brak PyQt6,
# fix profiles.json (format listy), fix start_daemon.sh, multi-folder,
# patch mbc20_auto_daemon.py (lockfile + load_dotenv(".env"))
set -e
RED="\\033[31m"; GREEN="\\033[32m"; YELLOW="\\033[33m"
CYAN="\\033[36m"; MAGENTA="\\033[35m"; BOLD="\\033[1m"; RESET="\\033[0m"
APP_USER="${SUDO_USER:-$USER}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BASENAME="$(basename "${APP_DIR}")"
REPO_URL="https://github.com/hattimon/auto-minter-gui.git"
SERVICE_NAME="mbc20-daemon-${APP_BASENAME}"
LOG_FILE="${APP_DIR}/daemon.log"
AUTO_DIR="${APP_DIR}/auto-minter-gui"
ENV_FILE="${AUTO_DIR}/.env"
PROFILES_JSON="${AUTO_DIR}/mbc20_profiles.json"
SETTINGS_JSON="${AUTO_DIR}/mbc20_daemon_settings.json"
HISTORY_LOG="${AUTO_DIR}/mbc20_history.log"
LANG="en"

venv_python() {
  local venv_bin="${AUTO_DIR}/.venv/bin"
  local py
  py=$(find "${venv_bin}" -maxdepth 1 -name "python3.*" ! -name "*config*" ! -name "*-*" 2>/dev/null | sort -V | tail -1)
  [ -z "$py" ] && py="${venv_bin}/python3"
  echo "$py"
}

fix_profiles_json() {
  [ -f "$PROFILES_JSON" ] || return 0
  local VENV_PY; VENV_PY="$(venv_python)"
  "$VENV_PY" - "$PROFILES_JSON" <<'PYEOF'
import json,sys
p=sys.argv[1]
with open(p) as f: d=json.load(f)
if isinstance(d,dict) and 'profiles' in d:
  with open(p,'w') as f: json.dump(d['profiles'],f,indent=2)
  print('  - profiles.json: skonwertowano do listy')
elif isinstance(d,list):
  print('  - profiles.json: format OK')
PYEOF
}

fix_profile_fields() {
  [ -f "$PROFILES_JSON" ] || return 0
  local VENV_PY; VENV_PY="$(venv_python)"
  "$VENV_PY" - "$PROFILES_JSON" <<'PYEOF'
import json,sys
p=sys.argv[1]
with open(p) as f: d=json.load(f)
if not isinstance(d,list): d=[]
changed=False
for prof in d:
  if 'amount_per_mint' in prof and 'amt' not in prof:
    prof['amt']=prof['amount_per_mint']; changed=True
  if 'amt' in prof and 'amount_per_mint' not in prof:
    prof['amount_per_mint']=prof['amt']; changed=True
if changed:
  with open(p,'w') as f: json.dump(d,f,indent=2)
  print('  - profiles.json: dodano brakujace pola amt/amount_per_mint')
else:
  print('  - profiles.json: pola OK')
PYEOF
}

# set_kv: puste = zostaw stara wartosc, z logiem
set_kv() {
  local key="$1" val="$2"
  if [ -z "$val" ]; then
    echo "  - ${key}: pozostawiono istniejaca wartosc (puste wejscie)"
    return 0
  fi
  mkdir -p "${AUTO_DIR}"
  touch "$ENV_FILE"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
    echo "  - ${key}: zaktualizowano"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
    echo "  - ${key}: ustawiono po raz pierwszy"
  fi
}

# patch_daemon_script:
# - nadpisuje main() bez blokady lockfile
# - ustawia configure_moltbook_api() z load_dotenv(dotenv_path=".env", override=True)
patch_daemon_script() {
  local script="${AUTO_DIR}/mbc20_auto_daemon.py"
  if [ ! -f "$script" ]; then
    echo "  - pomijam patch daemona: brak $script"
    return 0
  fi
  echo "  - patch mbc20_auto_daemon.py (main() + configure_moltbook_api)..."
  python3 - "$script" <<'PYEOF'
import sys,re

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

# 1) Podmiana configure_moltbook_api()
conf_pattern = r"def configure_moltbook_api\(\):[\s\S]*?^\s*[^ \t\n]"

# nowa wersja funkcji z load_dotenv('.env', override=True)
new_conf = '''
def configure_moltbook_api():
    load_dotenv(dotenv_path=".env", override=True)
    api_key = os.getenv("MOLTBOOK_API_KEY")
    if not api_key:
        logger.error("MOLTBOOK_API_KEY is not set; aborting daemon run.")
        raise RuntimeError("Missing MOLTBOOK_API_KEY")
    moltbook_client.set_api_key(api_key)

'''.lstrip()

new_text, n_conf = re.subn(conf_pattern, new_conf, text, flags=re.MULTILINE)
if n_conf == 0:
    # fallback: jak nie znajdzie starej definicji, dopisujemy na koniec importow
    if "def configure_moltbook_api()" not in new_text:
        insert_pat = r"(from dotenv import load_dotenv[^\n]*\n)"
        repl = r"\1\n" + new_conf
        new_text, n_conf2 = re.subn(insert_pat, repl, new_text, count=1)
        if n_conf2:
            print("    Dodano configure_moltbook_api() po imporcie load_dotenv.")
        else:
            print("    Uwaga: nie udalo sie automatycznie wstrzyknac configure_moltbook_api().")
    else:
        print("    Uwaga: configure_moltbook_api() juz jest w pliku (niezmienione).")
else:
    print(f"    Podmieniono configure_moltbook_api() (wystapienia: {n_conf}).")

text = new_text

# 2) Podmiana main() (usun blokade lockfile, systemd pilnuje jednej instancji)
pattern = r"def main\([\s\S]*?if __name__ == .__main__.:\\s*\\n\\s*main\(\)\\s*"

new_main_block = '''
def main():
    settings = load_daemon_settings()
    logger.info("DEBUG: loaded settings = %r", settings)

    if not settings.get("enabled", True):
        logger.info("Daemon disabled in settings, exiting.")
        return

    gui_pid = parse_gui_pid_from_argv()

    # lockfile nie blokuje startu – systemd pilnuje jednej instancji
    if is_another_daemon_running():
        return

    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    logger.info("Daemon invoked; pid=%d gui_pid=%r", os.getpid(), gui_pid)
    logger.info("Daemon timezone: %r", time.tzname)

    try:
        run_daemon_once(settings, gui_pid)
    finally:
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
'''.strip()

new_text2, n_main = re.subn(pattern, new_main_block, text, flags=re.MULTILINE)
if n_main == 0:
    print("    (Uwaga: nie znaleziono bloku main() do podmiany – sprawdz recznie.)")
else:
    print(f"    Podmieniono funkcje main() (wystapienia: {n_main}).")

open(path, "w", encoding="utf-8").write(new_text2)
PYEOF
}

install_headless() {
  echo -e "${YELLOW}Instalacja / aktualizacja headless daemona...${RESET}"
  sudo apt-get update -qq
  sudo apt-get install -y git python3 python3-venv python3-dev jq build-essential curl

  if [ ! -d "${AUTO_DIR}/.git" ]; then
    echo "  - klonowanie repo..."
    git clone "${REPO_URL}" "${AUTO_DIR}"
  else
    echo "  - aktualizacja repo..."
    cd "${AUTO_DIR}" && git pull && cd "${APP_DIR}"
  fi

  # od razu popraw wlasciciela repo
  sudo chown -R "${APP_USER}:${APP_USER}" "${AUTO_DIR}" 2>/dev/null || true

  # patch mbc20_auto_daemon.py (lockfile + configure_moltbook_api)
  patch_daemon_script

  cd "${AUTO_DIR}"
  if [ ! -d ".venv" ]; then
    echo "  - tworzenie venv..."
    python3 -m venv .venv
  fi

  VENV_PY="$(venv_python)"
  echo "  - venv python: ${VENV_PY}"
  echo "  - instalacja zaleznosci: requests, python-dotenv, psutil..."
  "$VENV_PY" -m pip install --upgrade pip --quiet
  "$VENV_PY" -m pip install requests python-dotenv psutil --quiet
  echo -e "${GREEN}  - zaleznosci OK${RESET}"

  mkdir -p "${AUTO_DIR}"

  # inicjalizacja .env (po chown)
  if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
MOLTBOOK_API_KEY=
OPENAI_API_KEY=
MOLTBOOK_API_NAME=
EOF
    echo "  - utworzono nowy plik .env: $ENV_FILE"
  else
    echo "  - wykryto istniejacy .env: $ENV_FILE"
  fi
  cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)" 2>/dev/null || true
  echo "  - backup .env zapisany"

  OLD_MOLT=$(grep '^MOLTBOOK_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  OLD_OPENAI=$(grep '^OPENAI_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  OLD_NAME=$(grep '^MOLTBOOK_API_NAME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)

  echo

  # MOLTBOOK_API_KEY: wymus przy pierwszej instalacji
  if [ -z "$OLD_MOLT" ]; then
    echo "Brak MOLTBOOK_API_KEY w .env – musisz podac wartosc."
    while true; do
      read -p "MOLTBOOK_API_KEY: " NEW_MOLT
      if [ -n "$NEW_MOLT" ]; then
        set_kv "MOLTBOOK_API_KEY" "$NEW_MOLT"
        break
      else
        echo "  - MOLTBOOK_API_KEY nie moze byc pusty (daemon tego wymaga)."
      fi
    done
  else
    echo "MOLTBOOK_API_KEY jest juz ustawiony (pokazywany jako ****)."
    read -p "MOLTBOOK_API_KEY (puste = zachowaj aktualny): " NEW_MOLT
    set_kv "MOLTBOOK_API_KEY" "$NEW_MOLT"
  fi

  # OPENAI_API_KEY – opcjonalny
  if [ -n "$OLD_OPENAI" ]; then
    echo "OPENAI_API_KEY jest juz ustawiony (****)."
  fi
  read -p "OPENAI_API_KEY (puste = zachowaj / brak): " NEW_OPENAI
  set_kv "OPENAI_API_KEY" "$NEW_OPENAI"

  # MOLTBOOK_API_NAME – przyjazna nazwa
  if [ -n "$OLD_NAME" ]; then
    echo "MOLTBOOK_API_NAME obecnie: $OLD_NAME"
  fi
  read -p "MOLTBOOK_API_NAME (puste = zachowaj / ustaw pozniej): " NEW_NAME
  set_kv "MOLTBOOK_API_NAME" "$NEW_NAME"

  echo "  - aktualny stan .env:"
  grep -E "^(MOLTBOOK_API_KEY|OPENAI_API_KEY|MOLTBOOK_API_NAME)=" "$ENV_FILE" || echo "  (brak wpisow)"

  if [ ! -f "$PROFILES_JSON" ] || [ ! -s "$PROFILES_JSON" ]; then
    echo "  - brak profili, tworzenie pierwszego..."
    add_profile
  else
    fix_profiles_json
    fix_profile_fields
  fi

  rm -f "${AUTO_DIR}/mbc20_daemon.lock"

  if [ ! -f "$SETTINGS_JSON" ] || [ ! -s "$SETTINGS_JSON" ]; then
    FIRST_PROFILE="$("$VENV_PY" -c "
import json
d=json.load(open('${PROFILES_JSON}'))
p=d if isinstance(d,list) else d.get('profiles',[])
print(p[0]['name'] if p else '')
" 2>/dev/null || echo "")"
    cat > "$SETTINGS_JSON" << JSONEOF
{
  "profile_name": "${FIRST_PROFILE}",
  "first_start_minutes": 1,
  "base_interval_minutes": 35,
  "retry_5xx_until_success": true,
  "retry_5xx_interval_minutes": 1,
  "use_static_backoff_for_other_errors": true,
  "static_backoff_minutes": 31,
  "start_daemon_on_launch": true,
  "language": "pl"
}
JSONEOF
    echo "  - settings.json utworzono (profil: ${FIRST_PROFILE})"
  fi

  cat > "${APP_DIR}/start_daemon.sh" << STARTEOF
#!/bin/bash
cd "${AUTO_DIR}"
${VENV_PY} mbc20_auto_daemon.py >> "${LOG_FILE}" 2>&1
STARTEOF
  chmod +x "${APP_DIR}/start_daemon.sh"
  echo "  - start_daemon.sh OK (python: ${VENV_PY})"

  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
  sudo tee "$SERVICE_FILE" > /dev/null << SVCEOF
[Unit]
Description=Moltbook MBC20 Auto-Minter (${APP_BASENAME})
After=network-online.target
Wants=network-online.target

[Service]
User=${APP_USER}
WorkingDirectory=${AUTO_DIR}
ExecStart=${APP_DIR}/start_daemon.sh
Restart=on-failure
RestartSec=15
StartLimitIntervalSec=120
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
SVCEOF

  # drugi chown na wszelki wypadek (logi, .env, itd.)
  sudo chown -R "${APP_USER}:${APP_USER}" "${AUTO_DIR}" "${LOG_FILE}" 2>/dev/null || true

  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}.service"
  sudo systemctl restart "${SERVICE_NAME}.service"
  echo
  echo -e "${GREEN}Gotowe.${RESET}"
  echo -e "${CYAN}  Logi: tail -f ${HISTORY_LOG}${RESET}"
  echo -e "${CYAN}  Status: systemctl status ${SERVICE_NAME}${RESET}"
}

add_profile() {
  mkdir -p "${AUTO_DIR}"
  if [ ! -f "$PROFILES_JSON" ] || [ ! -s "$PROFILES_JSON" ]; then
    echo "[]" > "$PROFILES_JSON"
  fi
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo
  read -p "Nazwa profilu (np. GPT-mint): " PROFILE_NAME
  read -p "Ticker tokena (np. GPT): " TOKEN_TICK
  read -p "Submolt (puste=mbc20): " SUBMOLT
  [ -z "$SUBMOLT" ] && SUBMOLT="mbc20"
  read -p "Ilosc tokenow na mint (np. 100): " AMOUNT
  read -p "Tytul posta: " TITLE
  read -p "Komentarz dodatkowy (puste=brak): " COMMENT
  RAND_ID=$(tr -dc A-Za-z0-9 </dev/urandom | head -c10)
  "$VENV_PY" - "$PROFILES_JSON" "$PROFILE_NAME" "$TOKEN_TICK" "$SUBMOLT" "$AMOUNT" "$TITLE" "$COMMENT" "$RAND_ID" <<'PYEOF'
import json,sys
path,name,tick,submolt,amt,title,comment,rand=sys.argv[1:]
with open(path) as f: profiles=json.load(f)
if not isinstance(profiles,list): profiles=[]
profiles.append({'name':name,'tick':tick,'submolt':submolt,
  'amount_per_mint':amt,'amt':amt,'title':title,
  'extra_comment':comment,'daemon_header_suffix':f'[Daemon {rand}]',
  'use_llm_only_for_riddles':True})
with open(path,'w') as f: json.dump(profiles,f,indent=2)
print(f'  - Profil dodany: {name}')
PYEOF
}

edit_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "Brak pliku profili."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Dostepne profile:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']} tick={p.get('tick','')} amt={p.get('amt',p.get('amount_per_mint',''))}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Wybierz numer: " CHOICE
  INDEX=$((CHOICE-1))
  read -p "Nowa nazwa (puste=zachowaj): " NN
  read -p "Nowy ticker (puste=zachowaj): " NT
  read -p "Nowy submolt (puste=zachowaj): " NS
  read -p "Nowa ilosc (puste=zachowaj): " NA
  read -p "Nowy tytul (puste=zachowaj): " NTI
  read -p "Nowy komentarz (puste=zachowaj): " NC
  "$VENV_PY" - "$PROFILES_JSON" "$INDEX" "$NN" "$NT" "$NS" "$NA" "$NTI" "$NC" <<'PYEOF'
import json,sys
path,idx=sys.argv[1],int(sys.argv[2])
nn,nt,ns,na,nti,nc=sys.argv[3:]
with open(path) as f: p=json.load(f)
r=p[idx]
if nn: r['name']=nn
if nt: r['tick']=nt
if ns: r['submolt']=ns
if na: r['amt']=na; r['amount_per_mint']=na
if nti: r['title']=nti
if nc: r['extra_comment']=nc
with open(path,'w') as f: json.dump(p,f,indent=2)
print(f'  - Zaktualizowano: {r["name"]}')
PYEOF
}

delete_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "Brak pliku profili."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Dostepne profile:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Wybierz numer: " CHOICE
  read -p "Na pewno usunac? (y/n): " CONFIRM
  if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    INDEX=$((CHOICE-1))
    "$VENV_PY" - "$PROFILES_JSON" "$INDEX" <<'PYEOF'
import json,sys
path,idx=sys.argv[1],int(sys.argv[2])
with open(path) as f: p=json.load(f)
rem=p.pop(idx)
with open(path,'w') as f: json.dump(p,f,indent=2)
print(f'  - Usunieto: {rem["name"]}')
PYEOF
  fi
}

select_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "Brak pliku profili."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Dostepne profile:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Wybierz numer: " CHOICE
  PROFILE_NAME="$("$VENV_PY" -c "import json; p=json.load(open('$PROFILES_JSON')); print(p[$((CHOICE-1))]['name'])")"
  touch "$SETTINGS_JSON"
  [ -s "$SETTINGS_JSON" ] || echo "{}" > "$SETTINGS_JSON"
  "$VENV_PY" - "$SETTINGS_JSON" "$PROFILE_NAME" <<'PYEOF'
import json,sys
path,name=sys.argv[1],sys.argv[2]
with open(path) as f: s=json.load(f)
s['profile_name']=name
with open(path,'w') as f: json.dump(s,f,indent=2)
print(f'  - Aktywny profil: {name}')
PYEOF
  sudo systemctl restart "${SERVICE_NAME}.service" 2>/dev/null || true
  echo -e "${GREEN}  - Daemon zrestartowany z profilem: ${PROFILE_NAME}${RESET}"
}

edit_env() {
  if [ ! -f "$ENV_FILE" ]; then echo "Brak .env"; return; fi
  echo "Aktualne klucze:"
  grep -E "^(MOLTBOOK_API_KEY|OPENAI_API_KEY|MOLTBOOK_API_NAME)=" "$ENV_FILE" | sed 's/=.*/=****/' || true
  echo
  echo "1) Edytuj w nano"
  echo "2) Szybka aktualizacja"
  echo "3) Powrot"
  read -p "> " ch
  case "$ch" in
    1) ${EDITOR:-nano} "$ENV_FILE" ;;
    2)
      read -p "MOLTBOOK_API_KEY (puste=zachowaj): " NM
      read -p "OPENAI_API_KEY (puste=zachowaj): " NO
      read -p "MOLTBOOK_API_NAME (puste=zachowaj): " NN
      cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)" 2>/dev/null || true
      set_kv "MOLTBOOK_API_KEY" "$NM"
      set_kv "OPENAI_API_KEY" "$NO"
      set_kv "MOLTBOOK_API_NAME" "$NN"
      echo -e "${GREEN}  - .env zaktualizowany${RESET}"
      sudo systemctl restart "${SERVICE_NAME}.service" 2>/dev/null || true
    ;;
  esac
}

toggle_autostart() {
  local enabled
  enabled=$(systemctl is-enabled "${SERVICE_NAME}.service" 2>/dev/null || echo "disabled")
  if [ "$enabled" = "enabled" ]; then
    read -p "Autostart WLACZONY. Wylaczyc? (y/n): " ans
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
      sudo systemctl disable "${SERVICE_NAME}.service"
      sudo systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
      echo -e "${YELLOW}Autostart wylaczony.${RESET}"
    fi
  else
    read -p "Autostart WYLACZONY. Wlaczyc? (y/n): " ans
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
      sudo systemctl enable "${SERVICE_NAME}.service"
      sudo systemctl restart "${SERVICE_NAME}.service"
      echo -e "${GREEN}Autostart wlaczony.${RESET}"
    fi
  fi
}

tail_logs() {
  echo -e "${MAGENTA}Podglad logow (Ctrl+C aby wyjsc):${RESET}"
  touch "$HISTORY_LOG" "$LOG_FILE" 2>/dev/null || true
  tail -f "$HISTORY_LOG" "$LOG_FILE"
}

reindex_history() {
  echo -e "${YELLOW}Reindeksacja z historii...${RESET}"
  VENV_PY="$(venv_python)"
  if [ -f "${AUTO_DIR}/indexer_client.py" ]; then
    cd "${AUTO_DIR}"
    "$VENV_PY" indexer_client.py --reindex-from-history || echo "  - reindex zakonczony"
  else
    echo -e "${RED}Brak indexer_client.py${RESET}"
  fi
}

choose_language() {
  echo -e "${BOLD}${CYAN}== MBC20 Daemon manager (folder: ${APP_BASENAME}) ==${RESET}"
  echo
  echo "Select language / Wybierz jezyk:"
  echo "  1) English"
  echo "  2) Polski"
  read -p "> " lc
  case "$lc" in
    2) LANG="pl" ;;
    *) LANG="en" ;;
  esac
}

main_menu() {
  while true; do
    echo
    echo -e "${BOLD}${CYAN}== MBC20 Daemon menu (${APP_BASENAME}) ==${RESET}"
    echo -e "${YELLOW}1) Zainstaluj / odswiez daemon${RESET}"
    echo -e "${YELLOW}2) Dodaj profil tokena${RESET}"
    echo -e "${YELLOW}3) Edytuj profil tokena${RESET}"
    echo -e "${YELLOW}4) Usun profil tokena${RESET}"
    echo -e "${YELLOW}5) Wybierz aktywny profil${RESET}"
    echo -e "${YELLOW}6) Podglad logow daemona${RESET}"
    echo -e "${YELLOW}7) Edytuj .env (API keys)${RESET}"
    echo -e "${YELLOW}8) Wlacz / wylacz autostart${RESET}"
    echo -e "${YELLOW}9) Reindeksuj z historii${RESET}"
    echo -e "${YELLOW}10) Wyjscie${RESET}"
    echo
    STATUS=$(systemctl is-active "${SERVICE_NAME}.service" 2>/dev/null || echo "inactive")
    if [ "$STATUS" = "active" ]; then
      echo -e "  Daemon: ${GREEN}AKTYWNY${RESET} | ${SERVICE_NAME}"
    else
      echo -e "  Daemon: ${RED}NIEAKTYWNY${RESET} | ${SERVICE_NAME}"
    fi
    echo
    read -p "Wybierz opcje: " choice
    case "$choice" in
      1)  install_headless ;;
      2)  add_profile ;;
      3)  edit_profile ;;
      4)  delete_profile ;;
      5)  select_profile ;;
      6)  tail_logs ;;
      7)  edit_env ;;
      8)  toggle_autostart ;;
      9)  reindex_history ;;
      10) exit 0 ;;
      *)  ;;
    esac
  done
}

choose_language
main_menu
