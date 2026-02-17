#!/usr/bin/env python3
import os
import sys
import json
import random
import string
import time

from lobster_solver import solve_lobster_challenge

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
    QPushButton,
    QMessageBox,
    QComboBox,
    QTabWidget,
    QCheckBox,
)
from PyQt6.QtGui import QGuiApplication
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
        "ph_auto_agent_name": "e.g. AgentName",
        "ph_auto_base_interval": "Minutes between successful mints, e.g. 35",
        "ph_auto_min_interval": "Minimal gap between runs, safety limit",
        "ph_auto_error_backoff": "Backoff after error, e.g. 65 or 125 (2h05)",
        "ph_auto_max_runs": "Total mints in this session, 0 = no limit",
        "ph_auto_profile_name": "Auto profile name e.g. AgentName-125m",
        "auto_desc_template":
            "Agent '{agent}' will mint immediately, then every {baseint} minutes on success. "
            "On errors: backoff {backoff1} / {backoff2} / {backoff3} minutes until success. "
            "Max runs: {maxruns}.",
        "auto_desc_agent_unnamed": "Agent (no name)",
        "auto_desc_max_infinite": "infinite",
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
        "ph_auto_agent_name": "np. NazwaAgenta",
        "ph_auto_base_interval": "Minuty między udanymi mintami, np. 35",
        "ph_auto_min_interval": "Minimalna przerwa między runami, limit bezpieczeństwa",
        "ph_auto_error_backoff": "Backoff po błędzie, np. 65 lub 125 (2h05)",
        "ph_auto_max_runs": "Łączna liczba mintów w sesji, 0 = bez limitu",
        "ph_auto_profile_name": "Nazwa profilu auto, np. NazwaAgenta-125m",
        "auto_desc_template":
            "Agent '{agent}' wystartuje od razu, potem co {baseint} minut przy sukcesach. "
            "Przy błędach backoff {backoff1} / {backoff2} / {backoff3} minut aż do udanego mintu. "
            "Maks. runów: {maxruns}.",
        "auto_desc_agent_unnamed": "Agent (bez nazwy)",
        "auto_desc_max_infinite": "bez limitu",
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
            # centralne logowanie z dopiskiem AUTO-MINT
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
            logfn(f"EXCEPTION in AutoMintWorker.run: {e!r}")
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
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
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
        env_buttons = QHBoxLayout()
        self.env_load_button = QPushButton(self.tr["env_load"])
        self.env_save_button = QPushButton(self.tr["env_save"])
        self.env_load_button.clicked.connect(self.load_env_to_widget)
        self.env_save_button.clicked.connect(self.save_env_from_widget)
        env_buttons.addWidget(self.env_load_button)
        env_buttons.addWidget(self.env_save_button)
        env_buttons.addStretch()
        env_layout.addLayout(env_buttons)
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

        self.auto_min_interval_edit = QLineEdit("10")
        self.auto_min_interval_edit.setPlaceholderText(
            self.tr["ph_auto_min_interval"]
        )
        self.auto_min_interval_edit.textChanged.connect(
            self.update_auto_description
        )
        auto_layout.addRow(
            self.tr["auto_min_interval"], self.auto_min_interval_edit
        )

        self.auto_error_backoff_edit = QLineEdit("125")
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

        self.update_auto_description()
    # ---------- helpers / logging ----------

    def getenv(self, key: str, required: bool = True, default=None):
        val = os.getenv(key, default)
        if required and not val:
            raise RuntimeError(f"Missing key in environment: {key} (.env)")
        return val

    def log(self, text: str):
        # Używane w głównym wątku GUI.
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        existing = self.log_edit.toPlainText()
        if existing:
            self.log_edit.setPlainText(existing + "\n" + line)
        else:
            self.log_edit.setPlainText(line)
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def append_log_from_thread(self, text: str):
        # Slot dla sygnału z wątku Auto-Mint – Qt wywołuje to w wątku GUI.
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        existing = self.log_edit.toPlainText()
        if existing:
            self.log_edit.setPlainText(existing + "\n" + line)
        else:
            self.log_edit.setPlainText(line)
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

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

    # ---------- OpenAI solve + retry (delegacja do lobster_solver.py) ----------

    def solve_challenge_with_openai(self, challenge: str) -> str:
        """
        Używa zewnętrznego modułu lobster_solver do rozwiązania zagadki.
        log_fn loguje tylko do pliku (bez wywołań Qt z wątku workera).
        """
        def log_fn(msg: str) -> None:
            self.log_to_file_only(msg)

        answer = solve_lobster_challenge(challenge, log_fn=log_fn)
        return answer

    def send_verification(self, verification_code: str, answer: str):
        api_key = self.getenv("MOLTBOOK_API_KEY")
        url = f"{MOLTBOOK_BASE_URL}/api/v1/verify"
        payload = {"verification_code": verification_code, "answer": answer}
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        self.log_to_file_only(
            f"[DEBUG] Sending verification code={verification_code} answer={answer}"
        )
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        text = r.text
        success = 200 <= r.status_code < 300
        self.log_to_file_only(
            f"Verify response: Status: {r.status_code}, Body: {text}"
        )
        return success, f"Status {r.status_code} {text}"

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


    def load_env_to_widget(self):
        if not os.path.exists(ENV_FILE):
            self.env_edit.setPlainText("")
            return
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                self.env_edit.setPlainText(f.read())
        except Exception as e:
            self.env_edit.setPlainText(str(e))

    def save_env_from_widget(self):
        try:
            text = self.env_edit.toPlainText()
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(text)

            reload_env()
            QMessageBox.information(self, ".env", "Saved and reloaded .env.")
        except Exception as e:
            QMessageBox.critical(self, self.tr["error"], str(e))

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
            resp = moltbook_client.post_to_moltbook(
                submolt=submolt,
                title=title,
                content=full_content,
                log_fn=self.log,
            )
            self.log(
                f"Post response: {json.dumps(resp, indent=2, ensure_ascii=False)}"
            )

            post_obj = resp.get("post") or {}
            post_id = post_obj.get("id")
            if not post_id:
                QMessageBox.warning(
                    self,
                    self.tr["post_created_no_ver"],
                    self.tr["post_error_no_id"],
                )
                return

            post_url = moltbook_client.get_post_url(post_id)
            QGuiApplication.clipboard().setText(post_url)

            verification = resp.get("verification") or {}
            verification_required = (
                resp.get("verification_required") or verification.get("required")
            )

            if not verification or not verification_required:
                QMessageBox.information(
                    self,
                    self.tr["post_created_no_ver"],
                    self.tr["post_id_url"].format(
                        postid=post_id,
                        posturl=post_url,
                    ),
                )
                return

            challenge = verification.get("challenge")
            code = verification.get("code")
            expires_at = verification.get("expires_at")
            self.log(
                f"Verification required.\nCode: {code}\nExpires at: {expires_at}\n"
                f"Challenge:\n{challenge}"
            )

            if not code or not challenge:
                QMessageBox.warning(
                    self,
                    self.tr["post_ver_failed"],
                    self.tr["ver_error_missing"],
                )
                return

            answer = self.solve_challenge_with_openai(challenge)
            self.log(f"LLM answer: {answer}")

            ok, verify_log = self.send_verification(code, answer)
            self.log(f"Verify result: {verify_log}")

            if ok:
                QMessageBox.information(
                    self,
                    self.tr["post_verified"],
                    self.tr["post_id_url"].format(
                        postid=post_id,
                        posturl=post_url,
                    ),
                )

                # dopiero po poprawnej weryfikacji – poczekaj 10 s i zindeksuj
                self.log(
                    f"[INDEXER] Will index post_id={post_id} in 10 seconds "
                    f"after successful verification."
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

def main():
    app = QApplication(sys.argv)
    gui = Mbc20InscriptionGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
