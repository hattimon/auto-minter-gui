edit_env() {
  if [ ! -f "$ENV_FILE" ]; then echo "No .env file"; return; fi
  echo "Current keys (masked):"
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
      if [ "$USE_SYSTEMD" -eq 1 ]; then
        sudo systemctl restart "${SERVICE_NAME}.service" 2>/dev/null || true
      else
        sudo service "${SERVICE_NAME}" restart 2>/dev/null || true
      fi
    ;;
  esac
}

toggle_autostart() {
  if [ "$USE_SYSTEMD" -eq 1 ]; then
    # systemd
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
  else
    # SysVinit (MX, old Debian)
    echo "SysVinit: checking autostart..."
    if ls /etc/rc*.d/*"${SERVICE_NAME}"* >/dev/null 2>&1; then
      # enabled
      read -p "Autostart ENABLED. Disable? (y/n): " ans
      if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
        sudo update-rc.d -f "${SERVICE_NAME}" remove
        sudo service "${SERVICE_NAME}" stop 2>/dev/null || true
        echo -e "${YELLOW}Autostart disabled (SysVinit).${RESET}"
      fi
    else
      # disabled
      read -p "Autostart DISABLED. Enable? (y/n): " ans
      if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
        sudo update-rc.d "${SERVICE_NAME}" defaults
        sudo service "${SERVICE_NAME}" start 2>/dev/null || true
        echo -e "${GREEN}Autostart enabled (SysVinit).${RESET}"
      fi
    fi
  fi
}

tail_logs() {
  echo -e "${MAGENTA}Log tail (Ctrl+C to exit):${RESET}"
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
    echo -e "${YELLOW}6) View daemon logs${RESET}"
    echo -e "${YELLOW}7) Edit .env (API keys)${RESET}"
    echo -e "${YELLOW}8) Enable / disable autostart${RESET}"
    echo -e "${YELLOW}9) Reindex from history${RESET}"
    echo -e "${YELLOW}10) Exit${RESET}"
    echo
    if [ "$USE_SYSTEMD" -eq 1 ]; then
      STATUS=$(systemctl is-active "${SERVICE_NAME}.service" 2>/dev/null || echo "inactive")
      if [ "$STATUS" = "active" ]; then
        echo -e "  Daemon: ${GREEN}ACTIVE${RESET} | ${SERVICE_NAME} (systemd)"
      else
        echo -e "  Daemon: ${RED}INACTIVE${RESET} | ${SERVICE_NAME} (systemd)"
      fi
    else
      if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}" 2>/dev/null)" 2>/dev/null; then
        echo -e "  Daemon: ${GREEN}ACTIVE${RESET} | ${SERVICE_NAME} (SysVinit)"
      else
        echo -e "  Daemon: ${RED}INACTIVE${RESET} | ${SERVICE_NAME} (SysVinit)"
      fi
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
