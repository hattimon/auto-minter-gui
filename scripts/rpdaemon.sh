#!/bin/bash
# rpdaemon.sh - Moltbook MBC20 headless daemon manager (EN)
# Install/update headless daemon: apt, venv, psutil, no PyQt6,
# fix profiles.json, fix start_daemon.sh, multi-folder,
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
SETTINGS_JSON="${AUTO_DIR}/mbc20_daemon_settings.json}"
SETTINGS_JSON="${AUTO_DIR}/mbc20_daemon_settings.json"
HISTORY_LOG="${AUTO_DIR}/mbc20_history.log"

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
  print('  - profiles.json: converted dict.profiles -> list')
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
  print('  - profiles.json: added missing amt/amount_per_mint fields')
else:
  print('  - profiles.json: fields OK')
PYEOF
}

set_kv() {
  local key="$1" val="$2"
  if [ -z "$val" ]; then
    echo "  - ${key}: keeping existing value (empty input)"
    return 0
  fi
  mkdir -p "${AUTO_DIR}"
  touch "$ENV_FILE"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
    echo "  - ${key}: updated"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
    echo "  - ${key}: set for the first time"
  fi
}

patch_daemon_script() {
  local script="${AUTO_DIR}/mbc20_auto_daemon.py"
  if [ ! -f "$script" ]; then
    echo "  - skip daemon patch: no ${script}"
    return 0
  fi
  echo "  - patch mbc20_auto_daemon.py (configure_moltbook_api + main)..."
  python3 - "$script" <<'PYEOF'
import sys,re

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

# 1) remove ALL old configure_moltbook_api() definitions

text, n_del = re.subn(
    r'^def configure_moltbook_api\(\):[^\n]*\n(?:^[ \t]+.*\n)*',
    '',
    text,
    flags=re.MULTILINE
)
if n_del:
    print(f"    Removed {n_del} old configure_moltbook_api() definitions.")

new_conf_block = '''
# ---------- Moltbook / API ----------

def configure_moltbook_api():
    load_dotenv(dotenv_path=".env", override=True)
    api_key = os.getenv("MOLTBOOK_API_KEY")
    if not api_key:
        logger.error("MOLTBOOK_API_KEY is not set; aborting daemon run.")
        raise RuntimeError("Missing MOLTBOOK_API_KEY")
    moltbook_client.set_api_key(api_key)

'''.lstrip('\n')

insert_pat = r'(from dotenv import load_dotenv[^\n]*\n)'
new_text, n_ins = re.subn(insert_pat, r'\1\n' + new_conf_block, text, count=1)
if n_ins:
    print("    Inserted fresh configure_moltbook_api() after load_dotenv import.")
    text = new_text
else:
    text = new_conf_block + '\n\n' + text
    print("    Inserted fresh configure_moltbook_api() at top of file (no load_dotenv import match).")

# 2) cut EVERYTHING from first def main( to end of file, then append our main()

main_cut_pattern = r'^def main\([^\n]*\n(?:.|\n)*$'
text, n_cut = re.subn(main_cut_pattern, '', text, flags=re.MULTILINE)
if n_cut:
    print("    Removed old main() block and anything after it.")
else:
    print("    (Warning: did not find existing main() to cut; will append new main())")

new_main_block = '''
def main():
    settings = load_daemon_settings()
    logger.info("DEBUG: loaded settings = %r", settings)

    if not settings.get("enabled", True):
        logger.info("Daemon disabled in settings, exiting.")
        return

    gui_pid = parse_gui_pid_from_argv()

    # lockfile does not block start – systemd ensures at most one instance
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
'''.lstrip('\n')

text = text.rstrip() + '\n\n' + new_main_block + '\n'
open(path, "w", encoding="utf-8").write(text)
PYEOF
}

install_headless() {
  echo -e "${YELLOW}Installing / updating headless daemon...${RESET}"
  sudo apt-get update -qq
  sudo apt-get install -y git python3 python3-venv python3-dev jq build-essential curl

  if [ ! -d "${AUTO_DIR}/.git" ]; then
    echo "  - cloning repo..."
    git clone "${REPO_URL}" "${AUTO_DIR}"
  else
    echo "  - updating repo..."
    cd "${AUTO_DIR}" && git pull && cd "${APP_DIR}"
  fi

  sudo chown -R "${APP_USER}:${APP_USER}" "${AUTO_DIR}" 2>/dev/null || true

  patch_daemon_script

  cd "${AUTO_DIR}"
  if [ ! -d ".venv" ]; then
    echo "  - creating venv..."
    python3 -m venv .venv
  fi

  VENV_PY="$(venv_python)"
  echo "  - venv python: ${VENV_PY}"
  echo "  - installing dependencies: requests, python-dotenv, psutil..."
  "$VENV_PY" -m pip install --upgrade pip --quiet
  "$VENV_PY" -m pip install requests python-dotenv psutil --quiet
  echo -e "${GREEN}  - dependencies OK${RESET}"

  mkdir -p "${AUTO_DIR}"

  if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
MOLTBOOK_API_KEY=
OPENAI_API_KEY=
MOLTBOOK_API_NAME=
EOF
    echo "  - created new .env: $ENV_FILE"
  else
    echo "  - existing .env detected: $ENV_FILE"
  fi
  cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)" 2>/dev/null || true
  echo "  - .env backup saved"

  OLD_MOLT=$(grep '^MOLTBOOK_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  OLD_OPENAI=$(grep '^OPENAI_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  OLD_NAME=$(grep '^MOLTBOOK_API_NAME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)

  echo

  if [ -z "$OLD_MOLT" ]; then
    echo "MOLTBOOK_API_KEY is empty in .env – you must provide a value."
    while true; do
      read -p "MOLTBOOK_API_KEY: " NEW_MOLT
      if [ -n "$NEW_MOLT" ]; then
        set_kv "MOLTBOOK_API_KEY" "$NEW_MOLT"
        break
      else
        echo "  - MOLTBOOK_API_KEY cannot be empty (daemon requires it)."
      fi
    done
  else
    echo "MOLTBOOK_API_KEY is already set (shown as ****)."
    read -p "MOLTBOOK_API_KEY (empty = keep current): " NEW_MOLT
    set_kv "MOLTBOOK_API_KEY" "$NEW_MOLT"
  fi

  if [ -n "$OLD_OPENAI" ]; then
    echo "OPENAI_API_KEY is already set (****)."
  fi
  read -p "OPENAI_API_KEY (empty = keep / none): " NEW_OPENAI
  set_kv "OPENAI_API_KEY" "$NEW_OPENAI"

  if [ -n "$OLD_NAME" ]; then
    echo "MOLTBOOK_API_NAME currently: $OLD_NAME"
  fi
  read -p "MOLTBOOK_API_NAME (empty = keep / set later): " NEW_NAME
  set_kv "MOLTBOOK_API_NAME" "$NEW_NAME"

  echo "  - current .env state:"
  grep -E "^(MOLTBOOK_API_KEY|OPENAI_API_KEY|MOLTBOOK_API_NAME)=" "$ENV_FILE" || echo "  (no entries)"

  if [ ! -f "$PROFILES_JSON" ] || [ ! -s "$PROFILES_JSON" ]; then
    echo "  - no profiles, creating first one..."
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
  "language": "en"
}
JSONEOF
    echo "  - settings.json created (profile: ${FIRST_PROFILE})"
  fi

  cat > "${APP_DIR}/start_daemon.sh" << STARTEOF
#!/bin/bash
cd "${AUTO_DIR}"
${VENV_PY} mbc20_auto_daemon.py >> "${LOG_FILE}" 2>&1
STARTEOF

  chmod +x "${APP_DIR}/start_daemon.sh"
  sudo chown "${APP_USER}:${APP_USER}" "${APP_DIR}/start_daemon.sh" 2>/dev/null || true
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

  sudo chown -R "${APP_USER}:${APP_USER}" "${AUTO_DIR}" "${LOG_FILE}" 2>/dev/null || true

  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}.service"
  sudo systemctl restart "${SERVICE_NAME}.service"
  echo
  echo -e "${GREEN}Done.${RESET}"
  echo -e "${CYAN}  Logs: tail -f ${HISTORY_LOG}${RESET}"
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
  read -p "Profile name (e.g. GPT-mint): " PROFILE_NAME
  read -p "Token ticker (e.g. GPT): " TOKEN_TICK
  read -p "Submolt (empty=mbc20): " SUBMOLT
  [ -z "$SUBMOLT" ] && SUBMOLT="mbc20"
  read -p "Amount per mint (e.g. 100): " AMOUNT
  read -p "Post title: " TITLE
  read -p "Extra comment (empty=none): " COMMENT
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
print(f'  - Profile added: {name}')
PYEOF
}

edit_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "No profiles file."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Available profiles:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']} tick={p.get('tick','')} amt={p.get('amt',p.get('amount_per_mint',''))}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Select number: " CHOICE
  INDEX=$((CHOICE-1))
  read -p "New name (empty=keep): " NN
  read -p "New ticker (empty=keep): " NT
  read -p "New submolt (empty=keep): " NS
  read -p "New amount (empty=keep): " NA
  read -p "New title (empty=keep): " NTI
  read -p "New comment (empty=keep): " NC
  "$VENV_PY" - "$PROFILES_JSON" "$INDEX" "$NN" "$NT" "$NS" "$NA" "$NTI" "$NC" <<'PYEOF'
import json,sys
path,idx=sys.argv[1],int(sys.argv[2])
nn,nt,ns,na,nti,nc=sys.argv[3:]
with open(path) as f: p=json.load(f)
r=p[idx]
if nn: r['name']=nn
if nt: r['tick']=nt
if ns: r['submolt']=ns
if na:
    r['amt']=na
    r['amount_per_mint']=na
if nti: r['title']=nti
if nc: r['extra_comment']=nc
with open(path,'w') as f: json.dump(p,f,indent=2)
print(f'  - Updated: {r["name"]}')
PYEOF
}

delete_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "No profiles file."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Available profiles:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Select number: " CHOICE
  read -p "Really delete? (y/n): " CONFIRM
  if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    INDEX=$((CHOICE-1))
    "$VENV_PY" - "$PROFILES_JSON" "$INDEX" <<'PYEOF'
import json,sys
path,idx=sys.argv[1],int(sys.argv[2])
with open(path) as f: p=json.load(f)
rem=p.pop(idx)
with open(path,'w') as f: json.dump(p,f,indent=2)
print(f'  - Deleted: {rem["name"]}')
PYEOF
  fi
}

select_profile() {
  [ -f "$PROFILES_JSON" ] || { echo "No profiles file."; return; }
  fix_profiles_json
  VENV_PY="$(venv_python)"
  echo "Available profiles:"
  "$VENV_PY" -c "import json; [print(f\"{i+1}) {p['name']}\") for i,p in enumerate(json.load(open('$PROFILES_JSON')))]"
  echo
  read -p "Select number: " CHOICE
  PROFILE_NAME="$("$VENV_PY" -c "import json; p=json.load(open('$PROFILES_JSON')); print(p[$((CHOICE-1))]['name'])")"
  touch "$SETTINGS_JSON"
  [ -s "$SETTINGS_JSON" ] || echo "{}" > "$SETTINGS_JSON"
  "$VENV_PY" - "$SETTINGS_JSON" "$PROFILE_NAME" <<'PYEOF'
import json,sys
path,name=sys.argv[1],sys.argv[2]
with open(path) as f: s=json.load(f)
s['profile_name']=name
with open(path,'w') as f: json.dump(s,f,indent=2)
print(f'  - Active profile: {name}')
PYEOF
  sudo systemctl restart "${SERVICE_NAME}.service" 2>/dev/null || true
  echo -e "${GREEN}  - Daemon restarted with profile: ${PROFILE_NAME}${RESET}"
}

edit_env() {
  if [ ! -f "$ENV_FILE" ]; then echo ".env not found"; return; fi
  echo "Current keys:"
  grep -E "^(MOLTBOOK_API_KEY|OPENAI_API_KEY|MOLTBOOK_API_NAME)=" "$ENV_FILE" | sed 's/=.*/=****/' || true
  echo
  echo "1) Edit in nano"
  echo "2) Quick update"
  echo "3) Back"
  read -p "> " ch
  case "$ch" in
    1) ${EDITOR:-nano} "$ENV_FILE" ;;
    2)
      read -p "MOLTBOOK_API_KEY (empty=keep): " NM
      read -p "OPENAI_API_KEY (empty=keep): " NO
      read -p "MOLTBOOK_API_NAME (empty=keep): " NN
      cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%s)" 2>/dev/null || true
      set_kv "MOLTBOOK_API_KEY" "$NM"
      set_kv "OPENAI_API_KEY" "$NO"
      set_kv "MOLTBOOK_API_NAME" "$NN"
      echo -e "${GREEN}  - .env updated${RESET}"
      sudo systemctl restart "${SERVICE_NAME}.service" 2>/dev/null || true
    ;;
  esac
}

toggle_autostart() {
  local enabled
  enabled=$(systemctl is-enabled "${SERVICE_NAME}.service" 2>/dev/null || echo "disabled")
  if [ "$enabled" = "enabled" ]; then
    read -p "Autostart ENABLED. Disable? (y/n): " ans
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
      sudo systemctl disable "${SERVICE_NAME}.service"
      sudo systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
      echo -e "${YELLOW}Autostart disabled.${RESET}"
    fi
  else
    read -p "Autostart DISABLED. Enable? (y/n): " ans
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
      sudo systemctl enable "${SERVICE_NAME}.service"
      sudo systemctl restart "${SERVICE_NAME}.service"
      echo -e "${GREEN}Autostart enabled.${RESET}"
    fi
  fi
}

tail_logs() {
  echo -e "${MAGENTA}Tailing logs (Ctrl+C to exit):${RESET}"
  touch "$HISTORY_LOG" "$LOG_FILE" 2>/dev/null || true
  tail -f "$HISTORY_LOG" "$LOG_FILE"
}

reindex_history() {
  echo -e "${YELLOW}Reindexing from history...${RESET}"
  VENV_PY="$(venv_python)"
  if [ -f "${AUTO_DIR}/indexer_client.py" ]; then
    cd "${AUTO_DIR}"
    "$VENV_PY" indexer_client.py --reindex-from-history || echo "  - reindex finished (check logs)"
  else
    echo -e "${RED}indexer_client.py not found${RESET}"
  fi
}

main_menu() {
  while true; do
    echo
    echo -e "${BOLD}${CYAN}== MBC20 Daemon menu (${APP_BASENAME}) ==${RESET}"
    echo -e "${YELLOW}1) Install / refresh daemon${RESET}"
    echo -e "${YELLOW}2) Add token profile${RESET}"
    echo -e "${YELLOW}3) Edit token profile${RESET}"
    echo -e "${YELLOW}4) Delete token profile${RESET}"
    echo -e "${YELLOW}5) Select active profile${RESET}"
    echo -e "${YELLOW}6) Tail daemon logs${RESET}"
    echo -e "${YELLOW}7) Edit .env (API keys)${RESET}"
    echo -e "${YELLOW}8) Enable / disable autostart${RESET}"
    echo -e "${YELLOW}9) Reindex from history${RESET}"
    echo -e "${YELLOW}10) Exit${RESET}"
    echo
    STATUS=$(systemctl is-active "${SERVICE_NAME}.service" 2>/dev/null || echo "inactive")
    if [ "$STATUS" = "active" ]; then
      echo -e "  Daemon: ${GREEN}ACTIVE${RESET} | ${SERVICE_NAME}"
    else
      echo -e "  Daemon: ${RED}INACTIVE${RESET} | ${SERVICE_NAME}"
    fi
    echo
    read -p "Choose option: " choice
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

main_menu
