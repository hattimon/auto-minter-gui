#!/usr/bin/env python3
import os
import sys
import json
import random
import string
import time

from lobster_solver import solve_lobster_challenge
from typing import Optional

from datetime import datetime
import indexer_client

import requests
from dotenv import load_dotenv

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QTextBrowser,
    QPushButton,
    QMessageBox,
    QComboBox,
    QTabWidget,
    QCheckBox,
)

from PyQt6.QtGui import QTextCursor, QGuiApplication, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject

import moltbook_client  # upewnij się że nazwa modułu jest poprawna
from auto_minter import AutoMinter, AutoMintConfig


MOLTBOOK_BASE_URL = "https://www.moltbook.com"
HISTORY_LOG_FILE = "mbc20_history.log"
PROFILES_FILE = "mbc20_profiles.json"
AUTO_PROFILES_FILE = "mbc20_auto_profiles.json"
ENV_FILE = ".env"

load_dotenv()

MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def reload_env():
    """Przeładuj .env i zaktualizuj globalne klucze + moltbook_client."""
    global MOLTBOOK_API_KEY, OPENAI_API_KEY, OPENAI_MODEL

    load_dotenv(override=True)
    MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    try:
        moltbook_client.set_api_key(MOLTBOOK_API_KEY)
    except Exception as e:
        print(f"[reload_env] Error setting Moltbook API key: {e!r}", file=sys.stderr)


LANG_STRINGS = {
    "en": {
        "window_title": "Moltbook MBC-20 Inscription GUI",
        "submolt": "Submolt (e.g. mbc20)",
        "title": "Title",
        "operation": "Operation",
        "tick": "Tick",
        "amount": "Amount (amt)",
        "max": "Max supply (max)",
        "lim": "Mint limit (lim)",
        "to": "To (recipient)",
        "addr": "Wallet address (addr)",
        "postdesc": "Post description",
        "create_btn": "Create mbc-20 post (auto-verify)",
        "log": "Log",
        "title_required": "Title is required.",
        "tick_len": "Tick must be 1-8 characters.",
        "amt_required": "Amount (amt) is required.",
        "amt_int": "Amount (amt) must be an integer.",
        "max_required": "Max supply (max) is required.",
        "max_int": "Max supply (max) must be an integer.",
        "lim_required": "Mint limit (lim) is required.",
        "lim_int": "Mint limit (lim) must be an integer.",
        "to_required": "Recipient (to) is required for transfer.",
        "addr_format": "Wallet address must be 0x + 40 hex chars.",
        "post_error_no_id": "Post created response has no post.id. Check log.",
        "post_created_no_ver": "Post created (no verification).",
        "post_verified": "Post verified.",
        "post_ver_failed": "Verification failed.",
        "post_id_url": "Post ID {postid}\n{posturl} copied to clipboard.",
        "post_id_url_fail": "Post ID {postid}\n{posturl} failed. Log for details.",
        "ver_error_missing": "Missing verification code or challenge in response.",
        "error": "Error",
        "op_deploy": "deploy",
        "op_mint": "mint",
        "op_transfer": "transfer",
        "op_link": "link",
        "lang_label": "Language",
        "tab_main": "Main",
        "tab_history": "History",
        "tab_env": ".env editor",
        "tab_auto": "Auto Mint",
        "test_ai": "Test AI Brain",
        "random_title": "Randomize title",
        "env_load": "Reload .env",
        "env_save": "Save .env",
        "profiles_label": "Profile",
        "profile_save": "Save profile",
        "profile_delete": "Delete profile",
        "history_reload": "Reload history",
        "history_empty": "History file not found.",
        "profile_name_required": "Profile name is required.",
        "profile_saved": "Profile saved.",
        "profile_deleted": "Profile deleted.",
        "auto_profiles_label": "Agent profile",
        "auto_profile_save": "Save agent profile",
        "auto_profile_delete": "Delete agent profile",
        "auto_profile_name_required": "Agent profile name is required.",
        "auto_profile_saved": "Agent profile saved.",
        "auto_profile_deleted": "Agent profile deleted.",
        "auto_agent_name": "Agent name",
        "auto_base_interval": "Base interval (minutes)",
        "auto_min_interval": "Min interval (minutes)",
        "auto_error_backoff": "Error backoff (minutes)",
        "auto_max_runs": "Max runs (0 = infinite)",
        "auto_start": "Start auto-mint",
        "auto_stop": "Stop auto-mint",
        "auto_need_tick_amt": "Tick and amt must be set on Main tab.",
        "auto_invalid_numbers": "Invalid numeric values in Auto Mint tab.",
        "auto_running": "Auto-mint is already running.",
        "ph_auto_agent_name": "Enter the name to be added in the post header (e.g. AgentName)",
        "ph_auto_base_interval": "Minutes between successful mints, e.g. 35",
        "ph_auto_min_interval": "Minimal gap between runs, safety limit",
        "ph_auto_error_backoff": "Backoff after error, e.g. 65 or 125 (2h05)",
        "ph_auto_max_runs": "Total mints in this session, 0 = no limit",
        "ph_auto_profile_name": "Auto profile name e.g. AgentName-125m",
        "auto_desc_template":
            "Agent '{agent}' will start immediately. First mint will happen after {baseint} minutes, "
            "then every {baseint} minutes on success. \nOn errors, the agent waits (backoff) "
            "{backoff1} / {backoff2} / {backoff3} minutes, increasing the delay on each consecutive error, "
            "until a successful mint. Max runs: {maxruns}.",
        "auto_desc_agent_unnamed": "Agent (no name)",
        "auto_desc_max_infinite": "infinite",

        "use_enhanced_solver": "Use enhanced lobster solver (NoAI)",
        "use_only_llm": "Use only LLM (skip rules/cache)",
        "molt_auto_retry": "Moltbook server auto-retry on timeout (30 s / errors 5xx)",
        "molt_retry_interval": "Retry interval (sec)",
        "molt_retry_attempts": "Max attempts",
        "env_api_config": "[API configuration]",
        "env_moltbook_key_label": "Moltbook API key slots",
        "env_moltbook_key_help": "You can keep multiple Moltbook API keys with descriptions. Only checked ones without '#' will be active in .env.",
        "env_openai_key_label": "OpenAI API key",
        "env_openai_key_help": "Used by the puzzle solver (OpenAI Chat API).",
        "env_openai_model_label": "OpenAI model for puzzles",
        "env_openai_model_help": "Recommended: gpt-4.1-mini or gpt-4.1. Manual field is always used.",
        "env_openai_model_manual": "Manual model name (override)",
        "env_openai_model_combo": "Suggested models",
        "env_multi_key_label": "Unlock multi key support (Experimental!)",
    },
    "pl": {
        "window_title": "Moltbook MBC-20 GUI Inskrypcje",
        "submolt": "Submolt (np. mbc20)",
        "title": "Tytuł",
        "operation": "Operacja",
        "tick": "Ticker",
        "amount": "Ilość (amt)",
        "max": "Maks. podaż (max)",
        "lim": "Limit mintu (lim)",
        "to": "Do (odbiorca)",
        "addr": "Adres portfela (addr)",
        "postdesc": "Opis posta",
        "create_btn": "Utwórz post mbc-20 (auto-weryfikacja)",
        "log": "Log",
        "title_required": "Tytuł jest wymagany.",
        "tick_len": "Ticker musi mieć 1–8 znaków.",
        "amt_required": "Ilość (amt) jest wymagana.",
        "amt_int": "Ilość (amt) musi być liczbą całkowitą.",
        "max_required": "Maks. podaż (max) jest wymagana.",
        "max_int": "Maks. podaż (max) musi być liczbą całkowitą.",
        "lim_required": "Limit mintu (lim) jest wymagany.",
        "lim_int": "Limit mintu (lim) musi być liczbą całkowitą.",
        "to_required": "Odbiorca (to) jest wymagany dla transferu.",
        "addr_format": "Adres portfela musi mieć format 0x + 40 znaków hex.",
        "post_error_no_id": "Odpowiedź z API nie zawiera post.id. Sprawdź log.",
        "post_created_no_ver": "Post utworzony (bez weryfikacji).",
        "post_verified": "Post zweryfikowany.",
        "post_ver_failed": "Weryfikacja nieudana.",
        "post_id_url": "ID posta {postid}\n{posturl} skopiowany do schowka.",
        "post_id_url_fail": "ID posta {postid}\n{posturl} nieudane. Sprawdź log.",
        "ver_error_missing": "Brak kodu weryfikacyjnego lub zagadki w odpowiedzi.",
        "error": "Błąd",
        "op_deploy": "deploy",
        "op_mint": "mint",
        "op_transfer": "transfer",
        "op_link": "link",
        "lang_label": "Język",
        "tab_main": "Główne",
        "tab_history": "Historia",
        "tab_env": "Edytor .env",
        "tab_auto": "Auto Mint",
        "test_ai": "Test AI Brain",
        "random_title": "Losuj tytuł",
        "env_load": "Wczytaj .env",
        "env_save": "Zapisz .env",
        "profiles_label": "Profil",
        "profile_save": "Zapisz profil",
        "profile_delete": "Usuń profil",
        "history_reload": "Odśwież historię",
        "history_empty": "Brak pliku historii.",
        "profile_name_required": "Nazwa profilu jest wymagana.",
        "profile_saved": "Profil zapisany.",
        "profile_deleted": "Profil usunięty.",
        "auto_profiles_label": "Profil agenta",
        "auto_profile_save": "Zapisz profil agenta",
        "auto_profile_delete": "Usuń profil agenta",
        "auto_profile_name_required": "Nazwa profilu agenta jest wymagana.",
        "auto_profile_saved": "Profil agenta zapisany.",
        "auto_profile_deleted": "Profil agenta usunięty.",
        "auto_agent_name": "Nazwa agenta",
        "auto_base_interval": "Bazowy interwał (minuty)",
        "auto_min_interval": "Minimalny interwał (minuty)",
        "auto_error_backoff": "Backoff po błędzie (minuty)",
        "auto_max_runs": "Maks. liczba runów (0 = nieskończoność)",
        "auto_start": "Start auto-mint",
        "auto_stop": "Stop auto-mint",
        "auto_need_tick_amt": "Ticker i ilość (amt) muszą być ustawione na zakładce Główne.",
        "auto_invalid_numbers": "Nieprawidłowe wartości liczbowe w zakładce Auto Mint.",
        "auto_running": "Auto-mint już działa.",
        "ph_auto_agent_name": "Wprowadź nazwę, która zostanie dodana w nagłówku posta (np. AgentName)",
        "ph_auto_base_interval": "Minuty między udanymi mintami, np. 35",
        "ph_auto_min_interval": "Minimalna przerwa między runami, limit bezpieczeństwa",
        "ph_auto_error_backoff": "Backoff po błędzie, np. 65 lub 125 (2h05)",
        "ph_auto_max_runs": "Łączna liczba mintów w sesji, 0 = bez limitu",
        "ph_auto_profile_name": "Nazwa profilu auto, np. NazwaAgenta-125m",
        "auto_desc_template":
            "Agent „{agent}” wystartuje od razu. Pierwszy mint nastąpi po {baseint} minutach, "
            "a kolejne udane minty również co {baseint} minut. \nPrzy błędach agent czeka (backoff) "
            "{backoff1} / {backoff2} / {backoff3} minut, za każdym kolejnym błędem wydłużając przerwę, "
            "aż do udanego mintu. Maks. liczba mintów: {maxruns}.",
        "auto_desc_agent_unnamed": "Agent (bez nazwy)",
        "auto_desc_max_infinite": "bez limitu",

        "use_enhanced_solver": "Użyj ulepszonego rozwiązywacza zagadek (NoAI)",
        "use_only_llm": "Używaj tylko LLM (pomiń reguły/cache)",
        "molt_auto_retry": "Serwer Moltbook – automatyczne ponawianie po przekroczeniu czasu (30 s / błędy 5xx)",
        "molt_retry_interval": "Odstęp między ponowieniami (sekundy)",
        "molt_retry_attempts": "Maks. prób",
        "env_api_config": "[Konfiguracja API]",
        "env_moltbook_key_label": "Sloty Moltbook API key",
        "env_moltbook_key_help": "Możesz trzymać wiele kluczy Moltbook z opisami. Tylko odznaczone '#' (zaznaczone w GUI) będą aktywne w .env.",
        "env_openai_key_label": "OpenAI API key",
        "env_openai_key_help": "Używany przez solver zagadek (OpenAI Chat API).",
        "env_openai_model_label": "Model OpenAI do zagadek",
        "env_openai_model_help": "Rekomendowane: gpt-4.1-mini lub gpt-4.1. Ręczne pole ma zawsze pierwszeństwo.",
        "env_openai_model_manual": "Ręczna nazwa modelu (nadpisuje wybór)",
        "env_openai_model_combo": "Sugerowane modele",
        "env_multi_key_label": "Odblokuj obsługę wielu kluczy (Eksperymentalne!)",
    },
}


class AutoMintWorker(QObject):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, gui, config: AutoMintConfig):
        super().__init__()
        self.gui = gui
        self.config = config
        self._stop = False

    def stop(self):
        self._stop = True

    def should_stop(self) -> bool:
        return self._stop
    
    def run(self):
        def logfn(msg: str):
            self.log_signal.emit(f"[AUTO-MINT] {msg}")

        logfn("Worker run() started.")

        minter = AutoMinter(
            solve_fn=self.gui.solve_challenge_with_openai,
            verify_fn=self.gui.send_verification,
            config=self.config,
            log_fn=logfn,
            stop_flag_fn=self.should_stop,
            build_title_fn=self.gui.build_auto_title,
            get_description_fn=self.gui.get_post_description,
        )
        try:
            minter.run_loop()
            logfn("run_loop() finished.")
        except Exception as e:
            import traceback
            logfn(f"EXCEPTION in AutoMintWorker.run: {e!r}")
            logfn(traceback.format_exc())
        finally:
            self.finished.emit()



class Mbc20InscriptionGUI(QWidget):
    def __init__(self):
        super().__init__()
        reload_env()  # wczytaj .env i ustaw klucze na start
        self.current_lang = "en"
        self.tr = LANG_STRINGS[self.current_lang]

        # proste testy AI
        self.test_challenges = [
            {
                "problem": "A lobster claw exerts twenty newtons of force and gains ten newtons during molting. What is the total force?",
                "answer": "30.00",
            },
            {
                "problem": "A crab walks at fifteen centimeters per second and increases speed by five centimeters per second. What is the new speed?",
                "answer": "20.00",
            },
            {
                "problem": "A shark swims thirty meters, then swims twelve more meters. What is the total distance?",
                "answer": "42.00",
            },
            {
                "problem": "A turtle moves seven centimeters per second and slows down by two centimeters per second. What is the new speed?",
                "answer": "5.00",
            },
            {
                "problem": "A seagull has nine shells and picks up three more shells. How many shells does it have now?",
                "answer": "12.00",
            },
        ]

        self.setWindowTitle(self.tr["window_title"])
        self.resize(900, 650)

        self.autominter_thread: QThread | None = None
        self.autominter_worker: AutoMintWorker | None = None
        self.auto_profiles = {}
        self.profiles = {}

        self.init_ui()
        self.load_profiles()
        self.load_auto_profiles()
        self.load_history_to_widget()
        self.load_env_to_widget()
        self.update_auto_description()
        
        
    # ---------- UI ----------

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # MAIN TAB
        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, self.tr["tab_main"])
        main_tab_layout = QVBoxLayout(self.main_tab)

        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.tr["lang_label"])
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Polski"])
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        main_tab_layout.addLayout(lang_layout)

        form = QFormLayout()
        main_tab_layout.addLayout(form)
        self.form_layout = form

        self.submolt_edit = QLineEdit()
        self.submolt_edit.setText("mbc20")

        title_layout = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setText("MBC-20 inscription")
        self.random_title_button = QPushButton(self.tr["random_title"])
        self.random_title_button.clicked.connect(self.on_randomize_title)
        title_layout.addWidget(self.title_edit)
        title_layout.addWidget(self.random_title_button)

        self.op_combo = QComboBox()
        self.op_combo.addItems(
            [
                self.tr["op_deploy"],
                self.tr["op_mint"],
                self.tr["op_transfer"],
                self.tr["op_link"],
            ]
        )
        self.op_combo.currentTextChanged.connect(self.update_fields_visibility)

        self.tick_edit = QLineEdit()
        self.tick_edit.setPlaceholderText("Token ticker, 1-8 chars e.g. CLAW")
        self.amt_edit = QLineEdit()
        self.amt_edit.setPlaceholderText("Amount integer")
        self.max_edit = QLineEdit()
        self.max_edit.setPlaceholderText("Max supply integer")
        self.lim_edit = QLineEdit()
        self.lim_edit.setPlaceholderText("Mint limit per operation integer")
        self.to_edit = QLineEdit()
        self.to_edit.setPlaceholderText("Recipient agent name")
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("0xYourWalletAddress on Base")

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Optional post description. At the end the mbc-20 JSON and mbc20.xyz link will be added automatically."
        )

        profile_layout = QHBoxLayout()
        self.profile_label = QLabel(self.tr["profiles_label"])
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        self.profile_name_edit = QLineEdit()
        self.profile_name_edit.setPlaceholderText("Profile name e.g. TokenName")
        self.profile_save_button = QPushButton(self.tr["profile_save"])
        self.profile_delete_button = QPushButton(self.tr["profile_delete"])
        self.profile_save_button.clicked.connect(self.save_current_profile)
        self.profile_delete_button.clicked.connect(self.delete_current_profile)
        profile_layout.addWidget(self.profile_label)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.profile_name_edit)
        profile_layout.addWidget(self.profile_save_button)
        profile_layout.addWidget(self.profile_delete_button)

        self.submolt_label = QLabel(self.tr["submolt"])
        self.title_label = QLabel(self.tr["title"])
        self.operation_label = QLabel(self.tr["operation"])
        self.tick_label = QLabel(self.tr["tick"])
        self.amount_label = QLabel(self.tr["amount"])
        self.max_label = QLabel(self.tr["max"])
        self.lim_label = QLabel(self.tr["lim"])
        self.to_label = QLabel(self.tr["to"])
        self.addr_label = QLabel(self.tr["addr"])
        self.postdesc_label = QLabel(self.tr["postdesc"])

        form.addRow(self.submolt_label, self.submolt_edit)
        form.addRow(self.title_label, title_layout)
        form.addRow(self.operation_label, self.op_combo)
        form.addRow(self.tick_label, self.tick_edit)
        form.addRow(self.amount_label, self.amt_edit)
        form.addRow(self.max_label, self.max_edit)
        form.addRow(self.lim_label, self.lim_edit)
        form.addRow(self.to_label, self.to_edit)
        form.addRow(self.addr_label, self.addr_edit)
        form.addRow(self.postdesc_label, self.description_edit)
        form.addRow(profile_layout)

        # --- Solver (LLM) + Moltbook auto‑retry w dwóch kolumnach ---

        solver_retry_row = QHBoxLayout()

        # LEWA KOLUMNA – solver
        solver_col = QVBoxLayout()
        self.use_enhanced_lobster_solver = QCheckBox(self.tr["use_enhanced_solver"])
        self.use_enhanced_lobster_solver.setChecked(False)  # domyślnie wyłączony
        solver_col.addWidget(self.use_enhanced_lobster_solver)

        self.use_only_llm_checkbox = QCheckBox(self.tr["use_only_llm"])
        self.use_only_llm_checkbox.setChecked(True)  # domyślnie włączony
        solver_col.addWidget(self.use_only_llm_checkbox)

        solver_retry_row.addLayout(solver_col)

        # PRAWA KOLUMNA – Moltbook auto‑retry
        retry_col = QVBoxLayout()

        self.molt_auto_retry_checkbox = QCheckBox(self.tr["molt_auto_retry"])
        self.molt_auto_retry_checkbox.setChecked(False)
        retry_col.addWidget(self.molt_auto_retry_checkbox)

        retry_row_inner = QHBoxLayout()

        self.molt_retry_interval_label = QLabel(self.tr["molt_retry_interval"])
        retry_row_inner.addWidget(self.molt_retry_interval_label)

        self.molt_retry_interval_edit = QLineEdit("60")  # sekundy
        self.molt_retry_interval_edit.setFixedWidth(80)
        retry_row_inner.addWidget(self.molt_retry_interval_edit)

        self.molt_retry_attempts_label = QLabel(self.tr["molt_retry_attempts"])
        retry_row_inner.addWidget(self.molt_retry_attempts_label)

        self.molt_retry_attempts_edit = QLineEdit("3")
        self.molt_retry_attempts_edit.setFixedWidth(60)
        retry_row_inner.addWidget(self.molt_retry_attempts_edit)

        retry_row_inner.addStretch()
        retry_col.addLayout(retry_row_inner)

        solver_retry_row.addLayout(retry_col)
        solver_retry_row.addStretch()

        main_tab_layout.addLayout(solver_retry_row)
        # koniec bloku z tabelką


        button_layout = QHBoxLayout()
        self.post_button = QPushButton(self.tr["create_btn"])
        self.post_button.clicked.connect(self.create_inscription_post)
        button_layout.addWidget(self.post_button)

        self.test_button = QPushButton(self.tr["test_ai"])
        self.test_button.clicked.connect(self.run_ai_test)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        main_tab_layout.addLayout(button_layout)

        self.log_label = QLabel(self.tr["log"])
        main_tab_layout.addWidget(self.log_label)

        # używamy QTextBrowser zamiast QTextEdit, żeby linki były klikalne
        self.log_edit = QTextBrowser()
        self.log_edit.setReadOnly(True)
        self.log_edit.setOpenExternalLinks(True)
        main_tab_layout.addWidget(self.log_edit)

        # HISTORY TAB
        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, self.tr["tab_history"])
        history_layout = QVBoxLayout(self.history_tab)

        btn_row = QHBoxLayout()
        self.history_reload_button = QPushButton(self.tr["history_reload"])
        self.history_reload_button.clicked.connect(self.load_history_to_widget)
        btn_row.addWidget(self.history_reload_button)

        # nowy przycisk indexera (tylko EN, jak chciałeś)
        self.history_index_all_button = QPushButton("INDEX ALL POSTS FROM HISTORY")
        self.history_index_all_button.clicked.connect(self.index_all_posts_from_history)
        btn_row.addWidget(self.history_index_all_button)

        # checkbox – pomijaj już zindeksowane posty
        self.history_skip_indexed_checkbox = QCheckBox("Skip already indexed")
        self.history_skip_indexed_checkbox.setChecked(False)
        btn_row.addWidget(self.history_skip_indexed_checkbox)

        # checkbox – pomijaj posty, które wcześniej dały ERROR
        self.history_skip_errors_checkbox = QCheckBox("Skip previous errors")
        self.history_skip_errors_checkbox.setChecked(False)
        btn_row.addWidget(self.history_skip_errors_checkbox)

        btn_row.addStretch()
        history_layout.addLayout(btn_row)

        self.history_edit = QTextEdit()
        self.history_edit.setReadOnly(True)
        history_layout.addWidget(self.history_edit)

        # status indeksowania
        self.history_index_status_label = QLabel("")
        history_layout.addWidget(self.history_index_status_label)

        # ENV TAB
        self.env_tab = QWidget()
        self.tabs.addTab(self.env_tab, self.tr["tab_env"])
        env_layout = QVBoxLayout(self.env_tab)

        # --- przyciski ładowania/zapisu .env ---
        env_buttons = QHBoxLayout()
        self.env_load_button = QPushButton(self.tr["env_load"])
        self.env_save_button = QPushButton(self.tr["env_save"])
        self.env_load_button.clicked.connect(self.load_env_to_widget)
        self.env_save_button.clicked.connect(self.save_env_from_widget)
        env_buttons.addWidget(self.env_load_button)
        env_buttons.addWidget(self.env_save_button)
        env_buttons.addStretch()
        env_layout.addLayout(env_buttons)

        # --- [Konfiguracja API] ---
        self.env_api_group_label = QLabel(self.tr["env_api_config"])
        self.env_api_group_label.setStyleSheet(
            "color:#ffd54f; font-weight:bold; margin-top:8px;"
        )
        env_layout.addWidget(self.env_api_group_label)

        # checkbox multi-key (Experimental!)
        multi_row = QHBoxLayout()
        self.env_multi_key_checkbox = QCheckBox(self.tr["env_multi_key_label"])
        self.env_multi_key_checkbox.setStyleSheet("color:#ff5555;")  # czerwony tekst
        self.env_multi_key_checkbox.setChecked(False)
        self.env_multi_key_checkbox.stateChanged.connect(
            self.on_env_multi_key_toggled
        )
        multi_row.addWidget(self.env_multi_key_checkbox)
        multi_row.addStretch()
        env_layout.addLayout(multi_row)

        # sloty MOLTBOOK_API_KEY (lista dynamicznych wierszy)
        self.env_moltbook_slots_layout = QVBoxLayout()
        env_layout.addLayout(self.env_moltbook_slots_layout)
        # lista słowników: {"checkbox", "label_edit", "key_edit", "slot_meta"}
        self.env_moltbook_slots_widgets = []

        # przyciski dodaj/usuń slot API
        slots_btn_row = QHBoxLayout()
        self.env_add_slot_button = QPushButton("+ API key")
        self.env_remove_slot_button = QPushButton("- API key")
        self.env_add_slot_button.clicked.connect(self.on_add_moltbook_slot)
        self.env_remove_slot_button.clicked.connect(self.on_remove_moltbook_slot)
        slots_btn_row.addWidget(self.env_add_slot_button)
        slots_btn_row.addWidget(self.env_remove_slot_button)
        slots_btn_row.addStretch()
        env_layout.addLayout(slots_btn_row)


        # OpenAI – pojedynczy key + model
        api_form = QFormLayout()

        # OPENAI_API_KEY
        openai_key_label = QLabel(self.tr["env_openai_key_label"])
        openai_key_help = QLabel(self.tr["env_openai_key_help"])
        openai_key_help.setWordWrap(True)
        openai_key_help.setStyleSheet("color:#aaaaaa; font-size:8pt;")
        openai_label_layout = QVBoxLayout()
        openai_label_layout.addWidget(openai_key_label)
        openai_label_layout.addWidget(openai_key_help)
        openai_label_widget = QWidget()
        openai_label_widget.setLayout(openai_label_layout)

        self.env_openai_key_edit = QLineEdit()
        self.env_openai_key_edit.setPlaceholderText("Paste your API key here (e.g. sk-proj-yourKey)")
        api_form.addRow(openai_label_widget, self.env_openai_key_edit)

        # OPENAI_MODEL
        openai_model_label = QLabel(self.tr["env_openai_model_label"])
        openai_model_help = QLabel(self.tr["env_openai_model_help"])
        openai_model_help.setWordWrap(True)
        openai_model_help.setStyleSheet("color:#aaaaaa; font-size:8pt;")
        openai_model_label_layout = QVBoxLayout()
        openai_model_label_layout.addWidget(openai_model_label)
        openai_model_label_layout.addWidget(openai_model_help)
        openai_model_label_widget = QWidget()
        openai_model_label_widget.setLayout(openai_model_label_layout)

        model_row_widget = QWidget()
        model_row_layout = QHBoxLayout(model_row_widget)
        model_row_layout.setContentsMargins(0, 0, 0, 0)

        self.env_openai_model_combo = QComboBox()
        self.env_openai_model_combo.addItem(self.tr["env_openai_model_combo"])
        self.env_openai_model_combo.addItems([
            "gpt-4.1-mini",
            "gpt-4.1",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo-0125",
        ])
        self.env_openai_model_combo.currentTextChanged.connect(
            self.on_env_model_combo_changed
        )
        model_row_layout.addWidget(self.env_openai_model_combo)

        self.env_openai_model_edit = QLineEdit()
        self.env_openai_model_edit.setPlaceholderText("Select your model (e.g. gpt-4.1-mini)")
        model_row_layout.addWidget(self.env_openai_model_edit)

        api_form.addRow(openai_model_label_widget, model_row_widget)

        env_layout.addLayout(api_form)

        # surowy edytor .env
        self.env_edit = QTextEdit()
        env_layout.addWidget(self.env_edit)


        # AUTO TAB
        self.auto_tab = QWidget()

        self.tabs.addTab(self.auto_tab, self.tr["tab_auto"])
        auto_layout = QFormLayout(self.auto_tab)

        auto_profile_row = QHBoxLayout()
        self.auto_profiles_label = QLabel(self.tr["auto_profiles_label"])
        auto_profile_row.addWidget(self.auto_profiles_label)
        self.auto_profile_combo = QComboBox()
        self.auto_profile_combo.setMinimumWidth(180)
        self.auto_profile_combo.currentIndexChanged.connect(
            self.on_auto_profile_selected
        )
        auto_profile_row.addWidget(self.auto_profile_combo)
        self.auto_profile_name_edit = QLineEdit()
        self.auto_profile_name_edit.setPlaceholderText(
            self.tr["ph_auto_profile_name"]
        )
        self.auto_profile_name_edit.setMinimumWidth(260)
        auto_profile_row.addWidget(self.auto_profile_name_edit)
        self.auto_profile_save_button = QPushButton(self.tr["auto_profile_save"])
        self.auto_profile_delete_button = QPushButton(
            self.tr["auto_profile_delete"]
        )
        self.auto_profile_save_button.clicked.connect(self.save_auto_profile)
        self.auto_profile_delete_button.clicked.connect(self.delete_auto_profile)
        auto_profile_row.addWidget(self.auto_profile_save_button)
        auto_profile_row.addWidget(self.auto_profile_delete_button)
        auto_layout.addRow(auto_profile_row)

        self.auto_agent_name_edit = QLineEdit()
        self.auto_agent_name_edit.setPlaceholderText(
            self.tr["ph_auto_agent_name"]
        )
        self.auto_agent_name_edit.textChanged.connect(self.update_auto_description)
        auto_layout.addRow(self.tr["auto_agent_name"], self.auto_agent_name_edit)

        self.auto_base_interval_edit = QLineEdit("35")
        self.auto_base_interval_edit.setPlaceholderText(
            self.tr["ph_auto_base_interval"]
        )
        self.auto_base_interval_edit.textChanged.connect(
            self.update_auto_description
        )
        auto_layout.addRow(
            self.tr["auto_base_interval"], self.auto_base_interval_edit
        )

        self.auto_min_interval_edit = QLineEdit("1")
        self.auto_min_interval_edit.setPlaceholderText(
            self.tr["ph_auto_min_interval"]
        )
        self.auto_min_interval_edit.textChanged.connect(
            self.update_auto_description
        )
        auto_layout.addRow(
            self.tr["auto_min_interval"], self.auto_min_interval_edit
        )

        self.auto_error_backoff_edit = QLineEdit("31")
        self.auto_error_backoff_edit.setPlaceholderText(
            self.tr["ph_auto_error_backoff"]
        )
        self.auto_error_backoff_edit.textChanged.connect(
            self.update_auto_description
        )
        auto_layout.addRow(
            self.tr["auto_error_backoff"], self.auto_error_backoff_edit
        )

        self.auto_max_runs_edit = QLineEdit("0")
        self.auto_max_runs_edit.setPlaceholderText(
            self.tr["ph_auto_max_runs"]
        )
        self.auto_max_runs_edit.textChanged.connect(self.update_auto_description)
        auto_layout.addRow(self.tr["auto_max_runs"], self.auto_max_runs_edit)

        auto_btn_layout = QHBoxLayout()
        self.auto_start_btn = QPushButton(self.tr["auto_start"])
        self.auto_stop_btn = QPushButton(self.tr["auto_stop"])
        self.auto_start_btn.clicked.connect(self.start_auto_mint)
        self.auto_stop_btn.clicked.connect(self.stop_auto_mint)
        auto_btn_layout.addWidget(self.auto_start_btn)
        auto_btn_layout.addWidget(self.auto_stop_btn)
        auto_layout.addRow(auto_btn_layout)

        self.auto_desc_label = QLabel()
        self.auto_desc_label.setWordWrap(True)
        auto_layout.addRow(self.auto_desc_label)

        # NEW: checkbox for Auto‑Mint solver behavior
        self.auto_use_only_llm_checkbox = QCheckBox(
            "Use only LLM for Auto‑Mint (skip rules/cache)"
        )
        self.auto_use_only_llm_checkbox.setChecked(False)
        auto_layout.addRow(self.auto_use_only_llm_checkbox)

        self.update_fields_visibility(self.op_combo.currentText())

        
    # ---------- language ----------

    def on_language_changed(self, index: int):
        self.current_lang = "en" if index == 0 else "pl"
        self.tr = LANG_STRINGS[self.current_lang]

        self.setWindowTitle(self.tr["window_title"])
        self.post_button.setText(self.tr["create_btn"])
        self.log_label.setText(self.tr["log"])
        self.random_title_button.setText(self.tr["random_title"])
        self.test_button.setText(self.tr["test_ai"])
        self.history_reload_button.setText(self.tr["history_reload"])
        self.env_load_button.setText(self.tr["env_load"])
        self.env_save_button.setText(self.tr["env_save"])
        self.profile_label.setText(self.tr["profiles_label"])
        self.profile_save_button.setText(self.tr["profile_save"])
        self.profile_delete_button.setText(self.tr["profile_delete"])
        self.lang_label.setText(self.tr["lang_label"])
        self.tabs.setTabText(0, self.tr["tab_main"])
        self.tabs.setTabText(1, self.tr["tab_history"])
        self.tabs.setTabText(2, self.tr["tab_env"])
        self.tabs.setTabText(3, self.tr["tab_auto"])
        self.submolt_label.setText(self.tr["submolt"])
        self.title_label.setText(self.tr["title"])
        self.operation_label.setText(self.tr["operation"])
        self.tick_label.setText(self.tr["tick"])
        self.amount_label.setText(self.tr["amount"])
        self.max_label.setText(self.tr["max"])
        self.lim_label.setText(self.tr["lim"])
        self.to_label.setText(self.tr["to"])
        self.addr_label.setText(self.tr["addr"])
        self.postdesc_label.setText(self.tr["postdesc"])

        self.auto_profiles_label.setText(self.tr["auto_profiles_label"])
        self.auto_profile_save_button.setText(self.tr["auto_profile_save"])
        self.auto_profile_delete_button.setText(self.tr["auto_profile_delete"])
        self.auto_start_btn.setText(self.tr["auto_start"])
        self.auto_stop_btn.setText(self.tr["auto_stop"])
        self.auto_agent_name_edit.setPlaceholderText(self.tr["ph_auto_agent_name"])
        self.auto_base_interval_edit.setPlaceholderText(
            self.tr["ph_auto_base_interval"]
        )
        self.auto_min_interval_edit.setPlaceholderText(
            self.tr["ph_auto_min_interval"]
        )
        self.auto_error_backoff_edit.setPlaceholderText(
            self.tr["ph_auto_error_backoff"]
        )
        self.auto_max_runs_edit.setPlaceholderText(self.tr["ph_auto_max_runs"])
        self.auto_profile_name_edit.setPlaceholderText(
            self.tr["ph_auto_profile_name"]
        )
        # NOWE: teksty checkboxów solvera
        if hasattr(self, "use_enhanced_lobster_solver"):
            self.use_enhanced_lobster_solver.setText(self.tr["use_enhanced_solver"])
        if hasattr(self, "use_only_llm_checkbox"):
            self.use_only_llm_checkbox.setText(self.tr["use_only_llm"])

        # nowe labelki Moltbook auto‑retry
        if hasattr(self, "molt_auto_retry_checkbox"):
            self.molt_auto_retry_checkbox.setText(self.tr["molt_auto_retry"])
        if hasattr(self, "molt_retry_interval_label"):
            self.molt_retry_interval_label.setText(self.tr["molt_retry_interval"])
        if hasattr(self, "molt_retry_attempts_label"):
            self.molt_retry_attempts_label.setText(self.tr["molt_retry_attempts"])

        # ENV tab labels
        if hasattr(self, "env_api_group_label"):
            self.env_api_group_label.setText(self.tr["env_api_config"])
        if hasattr(self, "env_openai_model_combo") and self.env_openai_model_combo.count() > 0:
            self.env_openai_model_combo.setItemText(0, self.tr["env_openai_model_combo"])
        if hasattr(self, "env_multi_key_checkbox"):
            self.env_multi_key_checkbox.setText(self.tr["env_multi_key_label"])

        self.update_auto_description()


    # ---------- helpers / logging ----------

    def getenv(self, key: str, required: bool = True, default=None):
        val = os.getenv(key, default)
        if required and not val:
            raise RuntimeError(f"Missing key in environment: {key} (.env)")
        return val

    def _format_log_line_html(self, line: str) -> str:
        """
        Kolorowanie linii logu na podstawie tagów / treści.
        Priorytet: ERROR > TIMEOUT > AUTO-MINT/INDEXER > LLM/DEBUG/AI TEST > CACHE > reszta.
        """
        lower = line.lower()

        # 1. Krytyczne błędy
        if ("[error" in lower or " error" in lower or "exception" in lower
                or "traceback" in lower):
            color = "#ff5555"   # czerwony – krytyczne

        # 2. Timeout / problemy sieci
        elif "timeout" in lower or "readtimeout" in lower or "timed out" in lower:
            color = "#ffb86c"   # jasny pomarańcz – problemy sieciowe

        # 3. AUTO-MINT
        elif "[auto-mint]" in lower:
            color = "#00bcd4"   # morski – auto-mint / agent

        # 4. INDEXER
        elif "[indexer]" in lower:
            if "error" in lower:
                color = "#ff8c00"  # mocniejszy pomarańcz dla błędów indexera
            else:
                color = "#ffd54f"  # żółty – info indexera

        # 5. AI TEST
        elif "ai test" in lower:
            color = "#bd93f9"   # fiolet – testy AI

        # 6. OpenAI / LLM / DEBUG
        elif "[openai]" in lower or "[llm" in lower or "[debug]" in lower:
            color = "#a6e22e"   # jasnozielony – LLM/DEBUG

        # 7. CACHE (LLM CACHE / KNOWN CACHE)
        elif "cache" in lower:
            color = "#8be9fd"   # cyjan – cache

        # 8. Verify / weryfikacja
        elif "verify" in lower or "verification" in lower:
            color = "#ffc107"   # żółty – weryfikacja odpowiedzi

        # 9. Sukcesy / OK
        elif " test ok" in lower or "sukces" in lower or " ok " in lower:
            color = "#4caf50"   # zielony – sukces / poprawna odpowiedź

        # 11. moltbook_client
        elif "moltbook_client" in lower:
            color = "#e01b24"   # czerwień - Moltbook Client

        # 10. Domyślne info
        else:
            color = "#dddddd"   # jasnoszary – zwykłe logi

        return f'<span style="color:{color}">{line}</span>'


    def log(self, text: str):
        """
        Log do widgetu log_edit + zapis do pliku.
        Kolorowanie przez HTML, auto-scroll na dół.
        """
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        html_line = self._format_log_line_html(line)

        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if self.log_edit.toPlainText():
            cursor.insertHtml("<br>" + html_line)
        else:
            cursor.insertHtml(html_line)

        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()

        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

        if hasattr(self, "status_label"):
            if "Retrying in" in text:
                self.status_label.setText(text)
            elif text.startswith("Creating post"):
                self.status_label.setText(self.tr.get("molt_auto_retry", "Working..."))
            elif text.startswith("[INDEXER]"):
                self.status_label.setText(text)

    def log_post_published(self, post_id: str):
        """
        Zielony komunikat o opublikowanym poście z linkiem, w PL/EN.
        Tutaj wstawiamy już HTML z <a href="...">, żeby QTextBrowser zrobił klikalny link.
        """
        post_url = moltbook_client.get_post_url(post_id)

        if self.current_lang == "pl":
            text = "SUKCES: Post został pomyślnie opublikowany pod linkiem: "
        else:
            text = "SUCCESS: The post was successfully published at: "

        # HTML: zielony tekst + klikalny <a href=...>
        html = (
            f'<span style="color:#4caf50;">'
            f'{text}<a href="{post_url}">{post_url}</a>'
            f"</span>"
        )

        from PyQt6.QtGui import QTextCursor  # upewniamy się, że jest import

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_html = f"[{timestamp}] {html}<br>"

        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_edit.setTextCursor(cursor)
        self.log_edit.insertHtml(full_html)
        self.log_edit.moveCursor(QTextCursor.MoveOperation.End)


    def append_log_from_thread(self, text: str):
        """
        Slot dla sygnału z wątku Auto-Mint.
        Qt wywołuje to w wątku GUI – możemy bezpiecznie dotykać log_edit.
        """
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        html_line = self._format_log_line_html(line)

        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if self.log_edit.toPlainText():
            cursor.insertHtml("<br>" + html_line)
        else:
            cursor.insertHtml(html_line)

        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()

        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

        if hasattr(self, "status_label") and "AUTO-MINT" in text:
            self.status_label.setText(text)


    def log_to_file_only(self, text: str):
        # Bezpieczne do użycia z wątku workera (brak Qt).
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def update_fields_visibility(self, op_display: str):
        op = self.normalize_op(op_display)
        show_tick = op in ("deploy", "mint", "transfer")
        show_amt = op in ("mint", "transfer")
        show_max_lim = op == "deploy"
        show_to = op == "transfer"
        show_addr = op == "link"

        self.tick_edit.setVisible(show_tick)
        self.tick_label.setVisible(show_tick)
        self.amt_edit.setVisible(show_amt)
        self.amount_label.setVisible(show_amt)
        self.max_edit.setVisible(show_max_lim)
        self.max_label.setVisible(show_max_lim)
        self.lim_edit.setVisible(show_max_lim)
        self.lim_label.setVisible(show_max_lim)
        self.to_edit.setVisible(show_to)
        self.to_label.setVisible(show_to)
        self.addr_edit.setVisible(show_addr)
        self.addr_label.setVisible(show_addr)

    def generate_random_suffix(self, length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choice(alphabet) for _ in range(length))

    def normalize_op(self, op_display: str) -> str:
        return op_display.strip().lower()

    def on_randomize_title(self):
        base_title = (self.title_edit.text().split("[")[0].strip()
                      or "MBC-20 inscription")
        suffix = self.generate_random_suffix(10)
        self.title_edit.setText(f"{base_title} [{suffix}]")

    # ---------- OpenAI solve + verify (delegacja do lobster_solver.py) ----------

    def solve_challenge_with_openai(
        self,
        challenge: str,
        verification_code: Optional[str] = None,
        *,
        is_automint: bool = False,
    ) -> str:
        """
        Rozwiązuje zagadkę przez lobster_solver z trybem enhanced/LLM i auto‑retry.
        log_fn loguje tylko do pliku (bez Qt z wątku workera).

        is_automint:
            False  -> używa ustawień z głównej zakładki (checkboxy solvera).
            True   -> może wymusić "only LLM" dla Auto‑Mint, jeśli zaznaczono
                      auto_use_only_llm_checkbox.
        """
        # domyślnie: enhanced (reguły + cache)
        force_llm = False

        if is_automint and hasattr(self, "auto_use_only_llm_checkbox"):
            # dla Auto‑Mint: jeżeli zaznaczono "Use only LLM for Auto‑Mint"
            if self.auto_use_only_llm_checkbox.isChecked():
                force_llm = True
        else:
            # tryb ręczny – jak wcześniej
            if hasattr(self, "use_only_llm_checkbox") and self.use_only_llm_checkbox.isChecked():
                force_llm = True
            elif hasattr(self, "use_enhanced_lobster_solver"):
                # jeśli odznaczysz enhanced, przełącz na classic LLM
                force_llm = not self.use_enhanced_lobster_solver.isChecked()

        # tylko log do pliku – żadnego self.log (Qt)
        def log_fn(msg: str) -> None:
            self.log_to_file_only(msg)

        answer = solve_lobster_challenge(
            challenge=challenge,
            log_fn=log_fn,
            force_llm=force_llm,
            retry_on_fail=True,
            verify_fn=self.send_verification,
            verification_code=verification_code,
        )
        return answer

    def send_verification(self, verification_code: str, answer: str):
        """
        Wysyła odpowiedź do Moltbook /verify.
        Zanim wyślemy, wyciągamy z answer samą liczbę z 2 miejscami po przecinku,
        bo API wymaga formatu np. "42.00".
        """
        import re

        # 1) Spróbuj wyciągnąć liczbę (z kropką lub przecinkiem) z tekstu odpowiedzi
        #    np. "Total force = 70 × 3 = 210.00" -> 210.00
        num_match = re.search(r"([-+]?\d+(?:[.,]\d+)?)", answer)
        if num_match:
            raw_num = num_match.group(1).replace(",", ".")
            try:
                num_val = float(raw_num)
                # 2) Sformatuj dokładnie jako XX.00
                answer_clean = f"{num_val:.2f}"
            except ValueError:
                # nie udało się sparsować – wyślij oryginalne answer (fallback)
                answer_clean = answer
        else:
            # brak liczby w tekście – wyślij oryginalne answer (fallback)
            answer_clean = answer

        api_key = self.getenv("MOLTBOOK_API_KEY")
        url = f"{MOLTBOOK_BASE_URL}/api/v1/verify"
        payload = {
            "verification_code": verification_code,
            "answer": answer_clean,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        self.log_to_file_only(
            f"DEBUG Sending verification code={verification_code} answer={answer_clean}"
        )

        r = requests.post(url, json=payload, headers=headers, timeout=15)
        text = r.text
        ok_http = 200 <= r.status_code < 300

        ok_logic = False
        try:
            data = r.json()
            ok_logic = bool(data.get("success"))
        except Exception:
            pass

        return ok_http and ok_logic, f"Status {r.status_code} {text}"


    # ---------- AI test ----------

    def run_ai_test(self):
        try:
            challenge_obj = random.choice(self.test_challenges)
            problem = challenge_obj["problem"]
            expected = challenge_obj["answer"]
            self.log(f"AI TEST: Problem: {problem}")
            got = self.solve_challenge_with_openai(problem)
            self.log(f"AI TEST: OpenAI answer: {got}, expected: {expected}")
            if got.strip() == expected:
                msg = f"Test OK, AI answer matches expected: {got}."
            else:
                msg = (
                    f"Test FAIL, AI answer={got} "
                    f"!= expected={expected}."
                )
            self.log(f"AI TEST: {msg}")
            QMessageBox.information(self, "Test AI Brain", msg)
        except Exception as e:
            QMessageBox.critical(self, "Test AI Brain", str(e))
            self.log(f"AI TEST ERROR: {e!r}")

    # ---------- validation ----------

    def validate_int(self, value: str, key_tr: str) -> str:
        if not value:
            raise ValueError(self.tr[key_tr + "_required"])
        if not value.isdigit():
            raise ValueError(self.tr[key_tr + "_int"])
        return value

    def validate_tick(self, tick: str) -> str:
        tick = tick.strip()
        if not (1 <= len(tick) <= 8):
            raise ValueError(self.tr["tick_len"])
        return tick

    def validate_addr(self, addr: str) -> str:
        addr = addr.strip()
        if not addr.startswith("0x") or len(addr) != 42:
            raise ValueError(self.tr["addr_format"])
        return addr

    # ---------- inscription JSON ----------

    def build_inscription_json(self, op_display: str) -> dict:
        op = self.normalize_op(op_display)
        if op == "deploy":
            tick = self.validate_tick(self.tick_edit.text())
            max_val = self.validate_int(self.max_edit.text(), "max")
            lim_val = self.validate_int(self.lim_edit.text(), "lim")
            return {"p": "mbc-20", "op": "deploy", "tick": tick,
                    "max": max_val, "lim": lim_val}
        if op == "mint":
            tick = self.validate_tick(self.tick_edit.text())
            amt = self.validate_int(self.amt_edit.text(), "amt")
            return {"p": "mbc-20", "op": "mint", "tick": tick, "amt": amt}
        if op == "transfer":
            tick = self.validate_tick(self.tick_edit.text())
            amt = self.validate_int(self.amt_edit.text(), "amt")
            to = self.to_edit.text().strip()
            if not to:
                raise ValueError(self.tr["to_required"])
            return {
                "p": "mbc-20",
                "op": "transfer",
                "tick": tick,
                "amt": amt,
                "to": to,
            }
        if op == "link":
            wallet = self.validate_addr(self.addr_edit.text())
            return {"p": "mbc-20", "op": "link", "wallet": wallet}
        raise ValueError(f"Unsupported op: {op}")

    # ---------- profiles (manual) ----------

    def load_profiles(self):
        self.profiles = {}
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception:
                self.profiles = {}
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("")
        for name in sorted(self.profiles.keys()):
            self.profile_combo.addItem(name)
        self.profile_combo.blockSignals(False)

    def on_profile_selected(self, index: int):
        name = self.profile_combo.currentText().strip()
        if not name:
            return
        data = self.profiles.get(name)
        if not data:
            return
        self.submolt_edit.setText(data.get("submolt", "mbc20"))
        self.title_edit.setText(data.get("title", "MBC-20 inscription"))
        op = data.get("op", "mint")
        for i in range(self.op_combo.count()):
            if self.normalize_op(self.op_combo.itemText(i)) == op:
                self.op_combo.setCurrentIndex(i)
                break
        self.tick_edit.setText(data.get("tick", ""))
        self.amt_edit.setText(data.get("amt", ""))
        self.max_edit.setText(data.get("max", ""))
        self.lim_edit.setText(data.get("lim", ""))
        self.to_edit.setText(data.get("to", ""))
        self.addr_edit.setText(data.get("addr", ""))
        self.description_edit.setPlainText(data.get("description", ""))

    def save_current_profile(self):
        name = self.profile_name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, self.tr["error"], self.tr["profile_name_required"]
            )
            return
        op = self.normalize_op(self.op_combo.currentText())
        data = {
            "submolt": self.submolt_edit.text().strip() or "mbc20",
            "title": self.title_edit.text().strip() or "MBC-20 inscription",
            "op": op,
            "tick": self.tick_edit.text().strip(),
            "amt": self.amt_edit.text().strip(),
            "max": self.max_edit.text().strip(),
            "lim": self.lim_edit.text().strip(),
            "to": self.to_edit.text().strip(),
            "addr": self.addr_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
        }
        self.profiles[name] = data
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))
            return
        self.load_profiles()
        for i in range(self.profile_combo.count()):
            if self.profile_combo.itemText(i) == name:
                self.profile_combo.setCurrentIndex(i)
                break
        QMessageBox.information(self, "Profiles", self.tr["profile_saved"])

    def delete_current_profile(self):
        name = self.profile_combo.currentText().strip()
        if not name:
            return
        if name in self.profiles:
            del self.profiles[name]
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))
            return
        self.load_profiles()
        QMessageBox.information(self, "Profiles", self.tr["profile_deleted"])

    # ---------- auto-profiles ----------

    def load_auto_profiles(self):
        self.auto_profiles = {}
        if os.path.exists(AUTO_PROFILES_FILE):
            try:
                with open(AUTO_PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.auto_profiles = json.load(f)
            except Exception:
                self.auto_profiles = {}
        self.auto_profile_combo.blockSignals(True)
        self.auto_profile_combo.clear()
        self.auto_profile_combo.addItem("")
        for name in sorted(self.auto_profiles.keys()):
            self.auto_profile_combo.addItem(name)
        self.auto_profile_combo.blockSignals(False)

    def on_auto_profile_selected(self, index: int):
        name = self.auto_profile_combo.currentText().strip()
        if not name:
            return
        data = self.auto_profiles.get(name)
        if not data:
            return
        self.auto_agent_name_edit.setText(data.get("agent_name", ""))
        self.auto_base_interval_edit.setText(
            str(data.get("base_interval_min", 35))
        )
        self.auto_min_interval_edit.setText(
            str(data.get("min_interval_min", 10))
        )
        self.auto_error_backoff_edit.setText(
            str(data.get("error_backoff_min", 125))
        )
        self.auto_max_runs_edit.setText(str(data.get("max_runs", 0)))
        self.update_auto_description()

    def save_auto_profile(self):
        name = self.auto_profile_name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, self.tr["error"], self.tr["auto_profile_name_required"]
            )
            return
        try:
            base_interval_min = float(
                self.auto_base_interval_edit.text().strip() or "35"
            )
            min_interval_min = float(
                self.auto_min_interval_edit.text().strip() or "10"
            )
            error_backoff_min = float(
                self.auto_error_backoff_edit.text().strip() or "125"
            )
            max_runs = int(self.auto_max_runs_edit.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(
                self, self.tr["error"], self.tr["auto_invalid_numbers"]
            )
            return
        data = {
            "agent_name": self.auto_agent_name_edit.text().strip(),
            "base_interval_min": base_interval_min,
            "min_interval_min": min_interval_min,
            "error_backoff_min": error_backoff_min,
            "max_runs": max_runs,
        }
        self.auto_profiles[name] = data
        try:
            with open(AUTO_PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.auto_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))
            return
        self.load_auto_profiles()
        for i in range(self.auto_profile_combo.count()):
            if self.auto_profile_combo.itemText(i) == name:
                self.auto_profile_combo.setCurrentIndex(i)
                break
        QMessageBox.information(
            self, "Auto Profiles", self.tr["auto_profile_saved"]
        )

    def delete_auto_profile(self):
        name = self.auto_profile_combo.currentText().strip()
        if not name:
            return
        if name in self.auto_profiles:
            del self.auto_profiles[name]
        try:
            with open(AUTO_PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.auto_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))
            return
        self.load_auto_profiles()
        QMessageBox.information(
            self, "Auto Profiles", self.tr["auto_profile_deleted"]
        )

    # ---------- auto-mint control ----------

    def start_auto_mint(self):
        if self.autominter_thread is not None:
            QMessageBox.information(
                self, "Auto Mint", self.tr["auto_running"]
            )
            return
        try:
            base_interval_min = float(
                self.auto_base_interval_edit.text().strip() or "35"
            )
            min_interval_min = float(
                self.auto_min_interval_edit.text().strip() or "10"
            )
            error_backoff_min = float(
                self.auto_error_backoff_edit.text().strip() or "125"
            )
            max_runs = int(self.auto_max_runs_edit.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(
                self, self.tr["error"], self.tr["auto_invalid_numbers"]
            )
            return

        base_interval = base_interval_min * 60.0
        min_interval = min_interval_min * 60.0
        error_backoff = error_backoff_min * 60.0

        submolt = self.submolt_edit.text().strip() or "mbc20"
        if submolt.startswith("m"):
            submolt = submolt[1:]

        tick = self.tick_edit.text().strip()
        amt = self.amt_edit.text().strip()
        if not tick or not amt:
            QMessageBox.warning(
                self, self.tr["error"], self.tr["auto_need_tick_amt"]
            )
            return

        agent_name = self.auto_agent_name_edit.text().strip()

        config = AutoMintConfig(
            submolt=submolt,
            tick=tick,
            amt=amt,
            base_interval=base_interval,
            min_interval=min_interval,
            error_backoff=error_backoff,
            max_runs=max_runs,
            agent_name=agent_name,
        )

        self.autominter_thread = QThread()
        self.autominter_worker = AutoMintWorker(self, config)
        self.autominter_worker.moveToThread(self.autominter_thread)
        self.autominter_thread.started.connect(self.autominter_worker.run)
        self.autominter_worker.finished.connect(self.autominter_thread.quit)
        self.autominter_worker.finished.connect(
            self.autominter_worker.deleteLater
        )
        self.autominter_thread.finished.connect(self.automint_thread_finished)
        self.autominter_worker.log_signal.connect(self.append_log_from_thread)

        self.autominter_thread.start()
        self.log("AUTO-MINT Started.")

    def automint_thread_finished(self):
        self.log("AUTO-MINT Thread finished.")
        if self.autominter_thread is not None:
            self.autominter_thread.deleteLater()
        self.autominter_thread = None
        self.autominter_worker = None

    def stop_auto_mint(self):
        if self.autominter_worker is None:
            return
        self.autominter_worker.stop()
        self.log("AUTO-MINT Stop requested.")

    # ---------- auto-mint helpers ----------

    def build_auto_title(self) -> str:
        base_title = (self.title_edit.text().split("[")[0].strip()
                      or "MBC-20 inscription")
        agent = self.auto_agent_name_edit.text().strip()
        if agent:
            base_title = f"{base_title} ({agent})"
        suffix = self.generate_random_suffix(10)
        return f"{base_title} [{suffix}]"

    def get_post_description(self) -> str:
        return self.description_edit.toPlainText()

    def update_auto_description(self):
        try:
            base_min = float(
                self.auto_base_interval_edit.text().strip() or "35"
            )
            error_min = float(
                self.auto_error_backoff_edit.text().strip() or "125"
            )
            max_runs_val = self.auto_max_runs_edit.text().strip()
            max_runs = int(max_runs_val or "0")
        except Exception:
            base_min = 0
            error_min = 0
            max_runs = 0

        agent_name = self.auto_agent_name_edit.text().strip()
        agent = (
            agent_name
            if agent_name
            else self.tr["auto_desc_agent_unnamed"]
        )
        backoff1 = error_min
        backoff2 = error_min * 2
        backoff3 = error_min * 4
        if max_runs == 0:
            max_runs_str = self.tr["auto_desc_max_infinite"]
        else:
            max_runs_str = str(max_runs)
        txt = self.tr["auto_desc_template"].format(
            agent=agent,
            baseint=int(base_min),
            backoff1=int(backoff1),
            backoff2=int(backoff2),
            backoff3=int(backoff3),
            maxruns=max_runs_str,
        )
        self.auto_desc_label.setText(txt)
    # ---------- history / env ----------

    def load_history_to_widget(self):
        if not os.path.exists(HISTORY_LOG_FILE):
            self.history_edit.setPlainText(self.tr["history_empty"])
            return
        try:
            with open(HISTORY_LOG_FILE, "r", encoding="utf-8") as f:
                self.history_edit.setPlainText(f.read())
        except Exception as e:
            self.history_edit.setPlainText(str(e))
    def index_all_posts_from_history(self):
        """
        Wywołuje indexer_client.index_all_posts_from_history i pokazuje prosty status.
        Jeśli zaznaczone są checkboxy:
        - 'Skip already indexed'  -> pomija [INDEXER] OK post_id=...
        - 'Skip previous errors'  -> pomija posty, które wcześniej miały ERROR post_id=...
        """
        self.history_index_status_label.setText("Indexing...")
        QApplication.processEvents()

        skip_indexed = self.history_skip_indexed_checkbox.isChecked()
        skip_errors = self.history_skip_errors_checkbox.isChecked()

        indexed, errors, total, log_lines = indexer_client.index_all_posts_from_history(
            skip_already_indexed=skip_indexed,
            skip_previous_errors=skip_errors,
        )

        # log hurtowego indeksowania tylko do pliku
        for line in log_lines:
            self.log_to_file_only(f"[INDEXER] {line}")

        if any("SERVER BUSY" in line for line in log_lines):
            self.history_index_status_label.setText(
                f"Stopped: server https://mbc20.xyz/ is busy. "
                f"Indexed {indexed}/{total} posts. Errors={errors}"
            )
        else:
            self.history_index_status_label.setText(
                f"Indexing finished. Indexed {indexed}/{total} posts. Errors={errors}"
            )

    def parse_env_api_slots(self, text: str):
        """
        Parsuje .env i zwraca:
        - slots_moltbook: lista slotów MOLTBOOK_API_KEY
          z labelami:
            * z komentarzy '#N - nazwa' lub '#N nazwa' NAD kluczem,
            * albo, jeśli brak komentarza, czysta numeracja '1', '2', '3', ...
        - other_lines: wszystkie pozostałe linie.
        """
        lines = text.splitlines()
        slots_moltbook = []
        other_lines = []

        # mapowanie: indeks linii z kluczem -> nazwa z komentarza
        name_by_index: dict[int, str] = {}

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue

            body = stripped[1:].strip()

            # przypadek "#1 - serafinus"
            if "-" in body:
                left, right = body.split("-", 1)
                if left.strip().isdigit():
                    name_by_index[idx + 1] = right.strip()
                    continue

            # przypadek "#1 serafinus"
            parts = body.split(" ", 1)
            if len(parts) == 2 and parts[0].isdigit():
                name_by_index[idx + 1] = parts[1].strip()

        # licznik do automatycznej numeracji
        auto_counter = 1

        for idx, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("#MOLTBOOK_API_KEY") or stripped.startswith("MOLTBOOK_API_KEY"):
                active = not stripped.startswith("#")
                body = stripped.lstrip("#")
                _, _, rhs = body.partition("=")
                value = rhs.strip()

                # najpierw spróbuj wziąć nazwę z komentarza
                label = name_by_index.get(idx, "")
                if not label:
                    # BRAK komentarza: ustaw prostą numerację '1', '2', '3', ...
                    label = str(auto_counter)
                auto_counter += 1

                slots_moltbook.append(
                    {
                        "line_index": idx,
                        "raw_line": line,
                        "active": active,
                        "label": label,
                        "value": value,
                    }
                )
            else:
                other_lines.append(line)

        return slots_moltbook, other_lines

    def rebuild_moltbook_slots_ui(self, slots_moltbook):
        """
        Buduje UI slotów Moltbook dokładnie na podstawie slots_moltbook
        (label/value/active z pliku .env), bez prób zgadywania / przenoszenia
        nazw pomiędzy slotami.
        """
        layout = self.env_moltbook_slots_layout
        if layout is None:
            return

        # wyczyść layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.env_moltbook_slots_widgets = []
        multi_enabled = self.env_multi_key_checkbox.isChecked()

        # single‑mode: wymuś dokładnie jeden active
        if not multi_enabled and slots_moltbook:
            first_active_index = None
            for i, slot in enumerate(slots_moltbook):
                if slot["active"]:
                    first_active_index = i
                    break
            if first_active_index is None:
                first_active_index = 0
            for i in range(len(slots_moltbook)):
                slots_moltbook[i]["active"] = (i == first_active_index)

        # buduj UI 1:1 z slots_moltbook
        for slot in slots_moltbook:
            value = slot["value"]
            label = slot.get("label", "").strip()

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            cb = QCheckBox()
            cb.setChecked(slot["active"])
            row_layout.addWidget(cb)

            label_edit = QLineEdit(label)
            label_edit.setPlaceholderText("API description (e.g. Key 1)")
            label_edit.setMinimumWidth(140)
            row_layout.addWidget(label_edit)

            key_edit = QLineEdit(value)
            key_edit.setPlaceholderText("moltbook_sk_...")
            row_layout.addWidget(key_edit)

            row_layout.addStretch()
            layout.addWidget(row_widget)

            self.env_moltbook_slots_widgets.append(
                {
                    "checkbox": cb,
                    "label_edit": label_edit,
                    "key_edit": key_edit,
                    "slot_meta": slot,
                }
            )

            cb.stateChanged.connect(self.on_moltbook_slot_checkbox_changed)

        self.apply_moltbook_slots_editability()

    def on_moltbook_slot_checkbox_changed(self, state: int):
        """
        Reakcja na kliknięcie checkboxa przy konkretnym slocie.
        W trybie single wybór jednego odznacza pozostałe.
        """
        multi_enabled = self.env_multi_key_checkbox.isChecked()

        if not multi_enabled:
            # single – tylko jeden zaznaczony
            sender_cb = self.sender()
            if not isinstance(sender_cb, QCheckBox):
                return
            if state:  # zaznaczony
                for w in self.env_moltbook_slots_widgets:
                    cb = w["checkbox"]
                    if cb is not sender_cb:
                        cb.setChecked(False)
            else:
                # nie pozwól wyłączyć wszystkich – jeśli wszystko się odznaczyło, włącz z powrotem
                any_checked = any(
                    w["checkbox"].isChecked()
                    for w in self.env_moltbook_slots_widgets
                )
                if not any_checked:
                    sender_cb.setChecked(True)

        # po zmianie checkboxów przeliczyć edytowalność + style
        self.apply_moltbook_slots_editability()


    def apply_moltbook_slots_editability(self):
        """
        Ustawia read-only i zaciemnienie 50% dla nieaktywnych slotów.
        Aktywne sloty – normalne, edytowalne.
        """
        multi_enabled = self.env_multi_key_checkbox.isChecked()

        for w in self.env_moltbook_slots_widgets:
            cb: QCheckBox = w["checkbox"]
            label_edit: QLineEdit = w["label_edit"]
            key_edit: QLineEdit = w["key_edit"]

            active = cb.isChecked()

            editable = active  # tylko zaznaczone sloty edytowalne
            label_edit.setReadOnly(not editable)
            key_edit.setReadOnly(not editable)

            if editable:
                # normalny wygląd
                label_edit.setStyleSheet("")
                key_edit.setStyleSheet("")
            else:
                # zaciemnienie 50% – tło ciemniejsze, tekst jaśniejszy
                label_edit.setStyleSheet(
                    "background-color: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4);"
                )
                key_edit.setStyleSheet(
                    "background-color: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4);"
                )

        # gdy multi OFF – upewnij się, że dokładnie jeden jest zaznaczony (jeśli jakikolwiek jest)
        if not multi_enabled and self.env_moltbook_slots_widgets:
            checked_indices = [
                i for i, w in enumerate(self.env_moltbook_slots_widgets)
                if w["checkbox"].isChecked()
            ]
            if len(checked_indices) == 0:
                # wymuś pierwszy jako aktywny
                self.env_moltbook_slots_widgets[0]["checkbox"].setChecked(True)
            elif len(checked_indices) > 1:
                # zostaw tylko pierwszy
                first = checked_indices[0]
                for i, w in enumerate(self.env_moltbook_slots_widgets):
                    w["checkbox"].setChecked(i == first)

    def on_env_model_combo_changed(self, value: str):
        """
        Wybrany model z listy wpisuje do pola manualnego (bez 'OPENAI_MODEL=').
        """
        if not value or value == self.tr.get("env_openai_model_combo"):
            return
        self.env_openai_model_edit.setText(value)

    def on_env_multi_key_toggled(self, state: int):
        """
        Kliknięcie 'Unlock multi key support'.
        - gdy wyłączasz multi: wymuś tylko jeden aktywny slot
        - gdy włączasz: nie zmieniaj zaznaczeń, jedynie pozwól na wiele
        """
        multi_enabled = bool(state)

        if not self.env_moltbook_slots_widgets:
            return

        if not multi_enabled:
            # przejście do single – zostaw tylko pierwszy zaznaczony,
            # albo jeśli żaden nie był, zaznacz pierwszy slot
            checked_indices = [
                i for i, w in enumerate(self.env_moltbook_slots_widgets)
                if w["checkbox"].isChecked()
            ]
            if not checked_indices:
                # zaznacz pierwszy
                self.env_moltbook_slots_widgets[0]["checkbox"].setChecked(True)
            else:
                first = checked_indices[0]
                for i, w in enumerate(self.env_moltbook_slots_widgets):
                    w["checkbox"].setChecked(i == first)

        # zaktualizuj read-only + style
        self.apply_moltbook_slots_editability()

    def save_env_from_widget(self):
        try:
            raw_text = self.env_edit.toPlainText()
            lines = raw_text.splitlines()

            header = "### Edited by Moltbook MBC-20 Inscription GUI ### Repo: https://github.com/hattimon/auto-minter-gui ###"

            # 0) Usuń wszystkie istniejące nagłówki GUI z wejścia
            lines = [line for line in lines if line.strip() != header]

            # 1) Usuń WSZYSTKIE linie z MOLTBOOK_API_KEY
            #    oraz komentarze "#N - Nazwa" i stare "#N nazwa"
            other_lines: list[str] = []
            for line in lines:
                stripped = line.strip()

                # linie z kluczem Moltbook
                if stripped.startswith("MOLTBOOK_API_KEY") or stripped.startswith("#MOLTBOOK_API_KEY"):
                    continue

                # nowe komentarze "#N - Nazwa"
                if stripped.startswith("#") and "-" in stripped:
                    left, _ = stripped[1:].split("-", 1)
                    if left.strip().isdigit():
                        continue

                # stare komentarze "#N nazwa"
                if stripped.startswith("#"):
                    body = stripped[1:].strip()
                    first_token = body.split(" ", 1)[0]
                    if first_token.isdigit():
                        continue

                other_lines.append(line)

            # 2) Z GUI zczytujemy sloty
            multi_enabled = self.env_multi_key_checkbox.isChecked()
            gui_slots = []
            for w in self.env_moltbook_slots_widgets:
                cb: QCheckBox = w["checkbox"]
                label_edit: QLineEdit = w["label_edit"]
                key_edit: QLineEdit = w["key_edit"]

                gui_slots.append(
                    {
                        "label": label_edit.text().strip(),
                        "value": key_edit.text().strip(),
                        "active": cb.isChecked(),
                    }
                )

            # single‑mode: wymuś dokładnie jeden active
            if not multi_enabled and gui_slots:
                checked_indices = [i for i, s in enumerate(gui_slots) if s["active"]]
                if len(checked_indices) == 0:
                    gui_slots[0]["active"] = True
                elif len(checked_indices) > 1:
                    first = checked_indices[0]
                    for i in range(len(gui_slots)):
                        gui_slots[i]["active"] = i == first

            # 3) Zbuduj blok Moltbook
            molt_lines: list[str] = []
            counter = 1
            for slot in gui_slots:
                label = slot["label"].strip()
                value = slot["value"].strip()
                if not value:
                    continue

                if label:
                    comment_text = f"#{counter} - {label}"
                else:
                    comment_text = f"#{counter} - Moltbook API key"
                molt_lines.append(comment_text)

                if slot["active"]:
                    molt_lines.append(f"MOLTBOOK_API_KEY={value}")
                else:
                    molt_lines.append(f"#MOLTBOOK_API_KEY={value}")

                molt_lines.append("")
                counter += 1

            if molt_lines and molt_lines[-1] == "":
                molt_lines.pop()

            # 4) OpenAI z pól GUI – nadpisz/uzupełnij
            env_map: dict[str, str] = {}
            for line in other_lines:
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    continue
                k, v = stripped.split("=", 1)
                env_map[k.strip()] = v.strip()

            key = self.env_openai_key_edit.text().strip()
            if key:
                env_map["OPENAI_API_KEY"] = key
            model = self.env_openai_model_edit.text().strip()
            if model:
                env_map["OPENAI_MODEL"] = model

            new_other_lines: list[str] = []
            for line in other_lines:
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    new_other_lines.append(line)
                    continue
                k, _ = stripped.split("=", 1)
                k = k.strip()
                if k in ("OPENAI_API_KEY", "OPENAI_MODEL"):
                    continue
                new_other_lines.append(line)

            for k in ("OPENAI_API_KEY", "OPENAI_MODEL"):
                if k in env_map:
                    new_other_lines.append(f"{k}={env_map[k]}")

            # 5) Finalny tekst: JEDEN nagłówek na górze, potem reszta i blok Moltbook
            final_lines: list[str] = []
            final_lines.append(header)
            final_lines.append("")  # odstęp po nagłówku
            final_lines.extend(new_other_lines)

            if molt_lines:
                if final_lines and final_lines[-1].strip() != "":
                    final_lines.append("")
                final_lines.extend(molt_lines)

            # 6) Usunięcie nadmiarowych pustych linii
            compact_lines: list[str] = []
            blank_streak = 0
            for line in final_lines:
                if line.strip() == "":
                    blank_streak += 1
                    if blank_streak > 1:
                        continue
                else:
                    blank_streak = 0
                compact_lines.append(line)

            final_text = "\n".join(compact_lines) + "\n"

            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(final_text)

            reload_env()
            self.load_env_to_widget()
            QMessageBox.information(self, ".env", "Saved and reloaded .env.")

        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))


    def load_env_to_widget(self):
        """
        Wczytuje ENV_FILE do surowego edytora + buduje sloty Moltbook + OpenAI pola.
        Bez dokładania extra pustych linii.
        """
        if not os.path.exists(ENV_FILE):
            self.env_edit.setPlainText("")
            self.rebuild_moltbook_slots_ui([])
            self.env_openai_key_edit.setText("")
            self.env_openai_model_edit.setText("")
            return

        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                text = f.read()

            # surowy tekst 1:1
            self.env_edit.setPlainText(text)

            # sloty Moltbook (z nazwami z komentarzy, jeśli są)
            slots_moltbook, _ = self.parse_env_api_slots(text)
            self.rebuild_moltbook_slots_ui(slots_moltbook)

            # OpenAI – proste mapowanie
            env_lines = [
                l.strip()
                for l in text.splitlines()
                if l.strip() and not l.strip().startswith("#")
            ]
            env_dict: dict[str, str] = {}
            for line in env_lines:
                if "=" in line:
                    k, v = line.split("=", 1)
                    env_dict[k.strip()] = v.strip()

            self.env_openai_key_edit.setText(env_dict.get("OPENAI_API_KEY", ""))
            self.env_openai_model_edit.setText(env_dict.get("OPENAI_MODEL", ""))

        except Exception as e:
            self.env_edit.setPlainText(str(e))


    # ---------- main manual action ----------

    def create_inscription_post(self):
        try:
            submolt = self.submolt_edit.text().strip() or "mbc20"

            # jeśli ktoś wpisze m/mbc20 → zostaw samo mbc20
            if submolt.lower().startswith("m/"):
                submolt = submolt[2:]

            # autokorekta typowej literówki
            if submolt.lower() == "bc20":
                submolt = "mbc20"

            base_title = (
                self.title_edit.text().split("[")[0].strip()
                or "MBC-20 inscription"
            )
            suffix = self.generate_random_suffix(10)
            title = f"{base_title} [{suffix}]"

            op_display = self.op_combo.currentText().strip()
            inscription_obj = self.build_inscription_json(op_display)
            inscription_json = json.dumps(
                inscription_obj,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            description = self.description_edit.toPlainText().strip()
            parts = []
            if description:
                parts.append(description)
            parts.append(inscription_json)
            parts.append("mbc20.xyz")
            full_content = "\n\n".join(parts)

            self.log(
                f"Creating post in submolt '{submolt}' with title '{title}' "
                f"and inscription: {inscription_json}"
            )

            # --- Moltbook auto‑retry na timeout/5xx ---

            max_attempts = 1
            interval_sec = 0.0

            if getattr(self, "molt_auto_retry_checkbox", None) and self.molt_auto_retry_checkbox.isChecked():
                try:
                    interval_sec = float(self.molt_retry_interval_edit.text().strip() or "60")
                except ValueError:
                    interval_sec = 60.0
                try:
                    max_attempts = int(self.molt_retry_attempts_edit.text().strip() or "3")
                    if max_attempts < 1:
                        max_attempts = 1
                except ValueError:
                    max_attempts = 3

            attempt = 0
            resp = None
            last_error = None

            while attempt < max_attempts:
                attempt += 1
                try:
                    self.log(f"Creating post (attempt {attempt}/{max_attempts})...")
                    resp = moltbook_client.post_to_moltbook(
                        submolt=submolt,
                        title=title,
                        content=full_content,
                        log_fn=self.log,
                    )
                    break  # sukces
                except requests.exceptions.ReadTimeout as e:
                    last_error = e
                    self.log(f"Timeout when creating post (attempt {attempt}): {e!r}")
                except requests.exceptions.HTTPError as e:
                    status = getattr(e.response, "status_code", None)
                    if status is not None and 500 <= status < 600:
                        last_error = e
                        self.log(
                            f"Server error {status} when creating post "
                            f"(attempt {attempt}): {e!r}"
                        )
                    else:
                        # 4xx (np. 400, 401, 429) – nie ma sensu retry
                        raise
                if attempt < max_attempts and interval_sec > 0:
                    self.log(f"Retrying in {interval_sec:.0f} seconds...")
                    QApplication.processEvents()
                    time.sleep(interval_sec)

            if resp is None:
                # po wszystkich próbach – pokaż błąd użytkownikowi
                raise RuntimeError(
                    f"Failed to create post after {max_attempts} attempts: {last_error!r}"
                )

            self.log(
                f"Post response: {json.dumps(resp, indent=2, ensure_ascii=False)}"
            )

            # --- pobranie POST + VERIFICATION ---

            post_obj = resp.get("post") or {}
            post_id = post_obj.get("id")
            if not post_id:
                QMessageBox.warning(
                    self,
                    self.tr["post_created_no_ver"],
                    self.tr["post_error_no_id"],
                )
                return

            # zielony log z linkiem do posta (PL/EN)
            self.log_post_published(post_id)

            post_url = moltbook_client.get_post_url(post_id)
            QGuiApplication.clipboard().setText(post_url)
            self.log(f"Clipboard: {post_url}")

            verification = post_obj.get("verification") or {}
            verification_code = verification.get("verification_code")
            challenge_text = verification.get("challenge_text")
            expires_at = verification.get("expires_at")

            if not verification_code or not challenge_text:
                QMessageBox.information(
                    self,
                    self.tr["post_created_no_ver"],
                    self.tr["post_id_url"].format(
                        postid=post_id,
                        posturl=post_url,
                    ),
                )
                return

            self.log(
                "Verification required.\n"
                f"Code: {verification_code}\n"
                f"Expires at: {expires_at}\n"
                f"Challenge:\n{challenge_text}"
            )

            # here: solver with verification_code → internal auto-retry
            answer = self.solve_challenge_with_openai(
                challenge_text,
                verification_code=verification_code,
                is_automint=True,
            )

            self.log(f"LLM answer (after a possible retry): {answer}")

            ok, verify_log = self.send_verification(verification_code, answer)
            self.log(f"Verify result: {verify_log}")

            # specjalne traktowanie 409 Already answered jako „soft success”
            is_already_answered = (
                "Status 409" in verify_log and "Already answered" in verify_log
            )

            if ok or is_already_answered:
                if is_already_answered:
                    self.log(
                        "Verification info: code already used – post is already verified "
                        "or the challenge was solved earlier."
                    )

                QMessageBox.information(
                    self,
                    self.tr["post_verified"],
                    self.tr["post_id_url"].format(
                        postid=post_id,
                        posturl=post_url,
                    ),
                )

                # po poprawnej / soft-poprawnej weryfikacji – poczekaj 10 s i zindeksuj
                self.log(
                    f"[INDEXER] Will index post_id={post_id} in 10 seconds "
                    f"after verification (ok or already answered)."
                )
                QApplication.processEvents()
                time.sleep(10.0)

                try:
                    idx_resp = indexer_client.index_single_post(post_id)
                    self.log(f"[INDEXER] OK post_id={post_id}: {idx_resp}")
                    self.log_to_file_only(
                        f"[INDEXER] OK post_id={post_id}: {idx_resp}"
                    )
                except Exception as e:
                    self.log(
                        f"[INDEXER] ERROR post_id={post_id}: {e!r}"
                    )
                    self.log_to_file_only(
                        f"[INDEXER] ERROR post_id={post_id}: {e!r}"
                    )
            else:
                QMessageBox.warning(
                    self,
                    self.tr["post_ver_failed"],
                    self.tr["post_id_url_fail"].format(
                        postid=post_id,
                        posturl=post_url,
                    ),
                )

        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))
            self.log(f"Error: {e!r}")

    def on_add_moltbook_slot(self):
        """
        Dodaje nowy pusty slot API do listy (domyślnie nieaktywny).
        """
        # obecne sloty z GUI
        slots = []
        for w in self.env_moltbook_slots_widgets:
            cb: QCheckBox = w["checkbox"]
            label_edit: QLineEdit = w["label_edit"]
            key_edit: QLineEdit = w["key_edit"]
            meta = w["slot_meta"]

            slots.append(
                {
                    "line_index": meta.get("line_index", -1),
                    "raw_line": meta.get("raw_line", ""),
                    "active": cb.isChecked(),
                    "label": label_edit.text().strip(),
                    "value": key_edit.text().strip(),
                }
            )

        # nowy pusty slot
        new_slot = {
            "line_index": -1,
            "raw_line": "",
            "active": False,
            "label": "",
            "value": "",
        }
        slots.append(new_slot)

        self.rebuild_moltbook_slots_ui(slots)

    def on_remove_moltbook_slot(self):
        """
        Usuwa zaznaczony slot API (albo ostatni, jeśli żaden nie jest zaznaczony).
        """
        if not self.env_moltbook_slots_widgets:
            return

        # znajdź zaznaczony slot
        checked_indices = [
            i for i, w in enumerate(self.env_moltbook_slots_widgets)
            if w["checkbox"].isChecked()
        ]

        if checked_indices:
            remove_index = checked_indices[0]
        else:
            remove_index = len(self.env_moltbook_slots_widgets) - 1

        # zbuduj nową listę slotów bez tego jednego
        slots = []
        for idx, w in enumerate(self.env_moltbook_slots_widgets):
            if idx == remove_index:
                continue

            cb: QCheckBox = w["checkbox"]
            label_edit: QLineEdit = w["label_edit"]
            key_edit: QLineEdit = w["key_edit"]
            meta = w["slot_meta"]

            slots.append({
                "line_index": meta.get("line_index", -1),
                "raw_line": meta.get("raw_line", ""),
                "active": cb.isChecked(),
                "label": label_edit.text().strip(),
                "value": key_edit.text().strip(),
            })

        self.rebuild_moltbook_slots_ui(slots)

def main():
    app = QApplication(sys.argv)
    gui = Mbc20InscriptionGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
