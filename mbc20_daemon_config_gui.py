#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
from pathlib import Path

import psutil
from PyQt6 import QtWidgets, QtCore, QtGui

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "mbc20_daemon_settings.json"
PROFILES_FILE = BASE_DIR / "mbc20_profiles.json"
HISTORY_LOG = BASE_DIR / "mbc20_history.log"
LOCK_FILE = BASE_DIR / "mbc20_daemon.lock"


STRINGS = {
    "en": {
        "title": "Moltbook MBC20 Daemon",
        "profile_label": "Token profile",
        "base_interval": "Base interval (minutes)",
        "first_start": "First start after (minutes)",
        "retry_5xx": "Retry Moltbook 5xx until success",
        "retry_5xx_interval": "Retry interval for Moltbook (minutes)",
        "fixed_backoff": "Use fixed backoff for other errors",
        "fixed_backoff_minutes": "Fixed backoff (minutes)",
        "fixed_backoff_help": "Constant pause after each non-5xx error (does not grow exponentially).",
        "llm_only": "Use LLM-only for puzzle solving",
        "language": "Language",
        "language_en": "English",
        "language_pl": "Polski",
        "enabled": "Enable the daemon at startup",
        "save": "Save settings",
        "start_daemon": "Start daemon",
        "stop_daemon": "Stop daemon",
        "close": "Close",
        "saved_msg": "Settings saved.",
        "log_view_title": "Daemon log preview",
        "log_empty": "(no log entries yet)",
        "daemon_start_ok": "Daemon started in background with current settings.",
        "daemon_start_fail": "Failed to start daemon:\n{error}",
        "daemon_not_found": "mbc20_auto_daemon.py not found in project directory.",
        "daemon_stop_ok": "Stopped {count} daemon process(es).",
        "daemon_stop_none": "No running daemon process found.",
        "no_profiles": "No token profiles found. Please add a profile first.",
    },
    "pl": {
        "title": "Moltbook MBC20 Daemon",
        "profile_label": "Profil tokena",
        "base_interval": "Podstawowy interwał (minuty)",
        "first_start": "Pierwszy start po (minutach)",
        "retry_5xx": "Ponawiaj błędy Moltbook 5xx do skutku",
        "retry_5xx_interval": "Interwał ponowień Moltbook (minuty)",
        "fixed_backoff": "Użyj stałego backoff dla innych błędów",
        "fixed_backoff_minutes": "Stały backoff (minuty)",
        "fixed_backoff_help": "Stała pauza po każdym błędzie innym niż 5xx (nie rośnie wykładniczo).",
        "llm_only": "Używaj tylko LLM do rozwiązywania zagadek",
        "language": "Język",
        "language_en": "English",
        "language_pl": "Polski",
        "enabled": "Włącz daemona przy starcie",
        "save": "Zapisz ustawienia",
        "start_daemon": "Start daemona",
        "stop_daemon": "Stop daemona",
        "close": "Zamknij",
        "saved_msg": "Ustawienia zapisane.",
        "log_view_title": "Podgląd logów daemona",
        "log_empty": "(brak wpisów w logu)",
        "daemon_start_ok": "Daemon uruchomiony w tle z bieżącymi ustawieniami.",
        "daemon_start_fail": "Nie udało się uruchomić daemona:\n{error}",
        "daemon_not_found": "Nie znaleziono mbc20_auto_daemon.py w katalogu projektu.",
        "daemon_stop_ok": "Zatrzymano {count} proces(ów) daemona.",
        "daemon_stop_none": "Nie znaleziono działającego daemona.",
        "no_profiles": "Brak profili tokenów. Najpierw dodaj profil.",
    },
}


def load_all_token_profiles():
    if not PROFILES_FILE.exists():
        return []
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        profiles = []
        for name, prof in data.items():
            if isinstance(prof, dict):
                prof_copy = prof.copy()
                prof_copy.setdefault("name", name)
                profiles.append(prof_copy)
        return profiles
    return []


def load_daemon_settings():
    if not SETTINGS_FILE.exists():
        return {
            "profile_name": "",
            "use_llm_only": True,
            "base_interval_minutes": 1,
            "first_start_minutes": 0,
            "retry_moltbook_5xx": True,
            "retry_interval_minutes_5xx": 1,
            "use_fixed_backoff": True,
            "fixed_backoff_minutes": 31,
            "enabled": True,
            "language": "en",
        }
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("language", "en")
    if "base_interval_minutes" not in data and "base_interval_seconds" in data:
        data["base_interval_minutes"] = max(
            1, int(data["base_interval_seconds"] / 60)
        )
    if (
        "retry_interval_minutes_5xx" not in data
        and "retry_interval_seconds_5xx" in data
    ):
        data["retry_interval_minutes_5xx"] = max(
            1, int(data["retry_interval_seconds_5xx"] / 60)
        )
    data.setdefault("first_start_minutes", 0)
    return data


def save_daemon_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def load_log_tail(max_lines: int = 500) -> str:
    if not HISTORY_LOG.exists():
        return ""
    try:
        with open(HISTORY_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return ""
    if len(lines) <= max_lines:
        return "".join(lines)
    return "".join(lines[-max_lines:])


def stop_all_daemons() -> int:
    """
    Zatrzymuje wszystkie procesy, których cmdline zawiera
    'mbc20_auto_daemon.py' (case-insensitive). Zwraca liczbę zabitych.
    """
    procs = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = p.info.get("cmdline") or []
            text = " ".join(cmd).lower()
            if "mbc20_auto_daemon.py".lower() in text:
                procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not procs:
        return 0

    for p in procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    gone, alive = psutil.wait_procs(procs, timeout=3)

    for p in alive:
        try:
            p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return len(procs)


def remove_lockfile():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError:
        pass


class BubbleLabel(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor("#000000"))
        self.setPalette(palette)

        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(self.label)

        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #ff7f9f;
                border-radius: 8px;
                background-color: #000000;
            }
            QLabel {
                color: #00ff00;
                font-size: 11pt;
            }
            """
        )

    def setText(self, text: str):
        self.label.setText(text)


class DaemonSettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_daemon_settings()
        self.profiles = load_all_token_profiles()
        self.lang = self.settings.get("language", "en")
        if self.lang not in STRINGS:
            self.lang = "en"

        self._build_ui()
        self._load_values()
        self._apply_language()
        self._update_summary()
        self._update_log_view()

        self.log_timer = QtCore.QTimer(self)
        self.log_timer.setInterval(5000)
        self.log_timer.timeout.connect(self._update_log_view)
        self.log_timer.start()

        # AUTO-START DAEMONA PRZY STARCIE GUI, JEŚLI ZAZNACZONE "Włącz daemona przy starcie"
        if self.settings.get("enabled", True):
            save_daemon_settings(self.settings)
            self._start_daemon_background()

    def _build_ui(self):
        self.setWindowTitle(STRINGS[self.lang]["title"])

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        self.title_label = QtWidgets.QLabel("Moltbook MBC20 Daemon")
        title_font = QtGui.QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.title_label)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(form)

        self.profile_combo = QtWidgets.QComboBox()
        for p in self.profiles:
            name = p.get("name", "unnamed")
            self.profile_combo.addItem(name)
        form.addRow("Token profile", self.profile_combo)

        self.llm_only_checkbox = QtWidgets.QCheckBox()
        form.addRow("Use LLM-only for puzzle solving", self.llm_only_checkbox)

        self.first_start_spin = QtWidgets.QSpinBox()
        self.first_start_spin.setRange(0, 24 * 60)
        self.first_start_spin.valueChanged.connect(self._update_summary)
        form.addRow("First start after (minutes)", self.first_start_spin)

        self.base_interval_spin = QtWidgets.QSpinBox()
        self.base_interval_spin.setRange(1, 24 * 60)
        self.base_interval_spin.valueChanged.connect(self._update_summary)
        form.addRow("Base interval (minutes)", self.base_interval_spin)

        self.retry_5xx_checkbox = QtWidgets.QCheckBox()
        self.retry_5xx_checkbox.stateChanged.connect(self._update_summary)
        form.addRow("Retry Moltbook 5xx until success", self.retry_5xx_checkbox)

        self.retry_5xx_interval_spin = QtWidgets.QSpinBox()
        self.retry_5xx_interval_spin.setRange(1, 24 * 60)
        self.retry_5xx_interval_spin.valueChanged.connect(self._update_summary)
        form.addRow("Retry interval for Moltbook (minutes)", self.retry_5xx_interval_spin)

        self.fixed_backoff_checkbox = QtWidgets.QCheckBox()
        self.fixed_backoff_checkbox.stateChanged.connect(self._update_summary)
        form.addRow("Use fixed backoff for other errors", self.fixed_backoff_checkbox)

        self.fixed_backoff_spin = QtWidgets.QSpinBox()
        self.fixed_backoff_spin.setRange(1, 24 * 60)
        self.fixed_backoff_spin.valueChanged.connect(self._update_summary)
        form.addRow("Fixed backoff (minutes)", self.fixed_backoff_spin)

        self.fixed_backoff_help = QtWidgets.QLabel()
        self.fixed_backoff_help.setWordWrap(True)
        main_layout.addWidget(self.fixed_backoff_help)

        self.enabled_checkbox = QtWidgets.QCheckBox()
        self.enabled_checkbox.stateChanged.connect(self._update_summary)
        main_layout.addWidget(self.enabled_checkbox)

        self.summary_bubble = BubbleLabel()
        main_layout.addWidget(self.summary_bubble)

        lang_layout = QtWidgets.QHBoxLayout()
        self.language_label = QtWidgets.QLabel("Language")
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Polski", "pl")
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.language_label)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch(1)
        main_layout.addLayout(lang_layout)

        log_title_layout = QtWidgets.QHBoxLayout()
        self.log_title_label = QtWidgets.QLabel("Daemon log preview")
        log_title_layout.addWidget(self.log_title_label)
        log_title_layout.addStretch(1)
        main_layout.addLayout(log_title_layout)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        font = QtGui.QFont("Consolas", 8)
        if not font.exactMatch():
            font = QtGui.QFont("Courier New", 8)
        self.log_view.setFont(font)
        main_layout.addWidget(self.log_view, stretch=1)

        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.start_daemon_button = QtWidgets.QPushButton("Start daemon")
        self.start_daemon_button.clicked.connect(self.on_start_daemon_clicked)
        btn_layout.addWidget(self.start_daemon_button)

        self.stop_daemon_button = QtWidgets.QPushButton("Stop daemon")
        self.stop_daemon_button.clicked.connect(self.on_stop_daemon_clicked)
        btn_layout.addWidget(self.stop_daemon_button)

        self.save_button = QtWidgets.QPushButton("Save settings")
        self.save_button.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(self.save_button)

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        btn_layout.addWidget(self.close_button)

    def _load_values(self):
        profile_name = self.settings.get("profile_name", "")
        if profile_name:
            idx = self.profile_combo.findText(profile_name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

        self.llm_only_checkbox.setChecked(self.settings.get("use_llm_only", True))
        self.first_start_spin.setValue(self.settings.get("first_start_minutes", 0))
        self.base_interval_spin.setValue(self.settings.get("base_interval_minutes", 1))
        self.retry_5xx_checkbox.setChecked(self.settings.get("retry_moltbook_5xx", True))
        self.retry_5xx_interval_spin.setValue(
            self.settings.get("retry_interval_minutes_5xx", 1)
        )
        self.fixed_backoff_checkbox.setChecked(self.settings.get("use_fixed_backoff", True))
        self.fixed_backoff_spin.setValue(self.settings.get("fixed_backoff_minutes", 31))
        self.enabled_checkbox.setChecked(self.settings.get("enabled", True))

        lang_code = self.settings.get("language", "en")
        idx = self.language_combo.findData(lang_code)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

    def _apply_language(self):
        s = STRINGS[self.lang]
        self.setWindowTitle(s["title"])
        self.title_label.setText(s["title"])

        form: QtWidgets.QFormLayout = self.layout().itemAt(1).layout()
        labels = []
        for i in range(form.rowCount()):
            item = form.itemAt(i, QtWidgets.QFormLayout.ItemRole.LabelRole)
            if item is not None:
                labels.append(item.widget())

        texts = [
            s["profile_label"],
            s["llm_only"],
            s["first_start"],
            s["base_interval"],
            s["retry_5xx"],
            s["retry_5xx_interval"],
            s["fixed_backoff"],
            s["fixed_backoff_minutes"],
        ]
        for i, txt in enumerate(texts):
            if i < len(labels):
                labels[i].setText(txt)

        self.fixed_backoff_help.setText(s["fixed_backoff_help"])
        self.enabled_checkbox.setText(s["enabled"])
        self.language_label.setText(s["language"])
        self.save_button.setText(s["save"])
        self.start_daemon_button.setText(s["start_daemon"])
        self.stop_daemon_button.setText(s["stop_daemon"])
        self.close_button.setText(s["close"])
        self.log_title_label.setText(s["log_view_title"])

        self.language_combo.blockSignals(True)
        current_data = self.language_combo.currentData()
        self.language_combo.clear()
        self.language_combo.addItem(s["language_en"], "en")
        self.language_combo.addItem(s["language_pl"], "pl")
        idx = self.language_combo.findData(current_data or self.lang)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)
        self.language_combo.blockSignals(False)

        self._update_summary()
        self._update_log_view()

    def _update_summary(self):
        first_start = self.first_start_spin.value()
        base_interval = self.base_interval_spin.value()
        retry_5xx_enabled = self.retry_5xx_checkbox.isChecked()
        retry_5xx = self.retry_5xx_interval_spin.value()
        fixed_backoff_enabled = self.fixed_backoff_checkbox.isChecked()
        fixed_backoff = self.fixed_backoff_spin.value()

        self.start_daemon_button.setEnabled(self.enabled_checkbox.isChecked())

        if self.lang == "pl":
            if retry_5xx_enabled:
                retry_txt = (
                    f"Przy błędach Moltbook 5xx będzie ponawiać "
                    f"co {retry_5xx} minut do skutku."
                )
            else:
                retry_txt = (
                    "Przy błędach Moltbook 5xx nie będzie osobnych ponowień; "
                    "zostaną potraktowane jak zwykły błąd i daemon użyje "
                    "tej samej pauzy co dla innych błędów."
                )

            if fixed_backoff_enabled:
                backoff_txt = (
                    f"Przy innych błędach nastąpi stała pauza {fixed_backoff} minut, "
                    "która nie rośnie wykładniczo."
                )
            else:
                backoff_txt = (
                    "Przy innych błędach daemon użyje wyłącznie podstawowego interwału "
                    f"{base_interval} minut. Wewnętrzny backoff AutoMintera działa tylko "
                    "w jego własnej pętli run_loop, więc w tej konfiguracji praktycznie "
                    "masz zwykły cykl co podstawowy interwał."
                )

            text = (
                f"Pierwsze uruchomienie nastąpi po {first_start} minutach. "
                f"Potem pętla będzie działać co {base_interval} minut. "
                f"{retry_txt} {backoff_txt}"
            )
        else:
            if retry_5xx_enabled:
                retry_txt = (
                    f"On Moltbook 5xx errors it retries every {retry_5xx} minutes "
                    "until success."
                )
            else:
                retry_txt = (
                    "On Moltbook 5xx errors it will not retry separately; "
                    "they are treated as normal errors and the daemon uses the same "
                    "pause as for other errors."
                )

            if fixed_backoff_enabled:
                backoff_txt = (
                    f"On other errors it pauses for a fixed {fixed_backoff} minutes "
                    "without exponential growth."
                )
            else:
                backoff_txt = (
                    "On other errors the daemon only uses the base interval of "
                    f"{base_interval} minutes. AutoMinter’s internal exponential "
                    "backoff works only in its own run_loop, so in this setup you "
                    "effectively have a regular cycle with the base interval."
                )

            text = (
                f"First run will happen after {first_start} minutes. "
                f"Then the loop runs every {base_interval} minutes. "
                f"{retry_txt} {backoff_txt}"
            )

        if not self.profiles:
            text = STRINGS[self.lang].get("no_profiles", text)

        self.summary_bubble.setText(text)

    def _update_log_view(self):
        tail = load_log_tail()
        if not tail:
            self.log_view.setPlainText(STRINGS[self.lang]["log_empty"])
        else:
            self.log_view.setPlainText(tail)
            cursor = self.log_view.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.log_view.setTextCursor(cursor)
            self.log_view.ensureCursorVisible()

    def on_language_changed(self):
        data = self.language_combo.currentData()
        if data in STRINGS:
            self.lang = data
            self.settings["language"] = self.lang
            self._apply_language()

    def on_save_clicked(self):
        profile_name = self.profile_combo.currentText()
        self.settings["profile_name"] = profile_name
        self.settings["use_llm_only"] = self.llm_only_checkbox.isChecked()
        self.settings["first_start_minutes"] = self.first_start_spin.value()
        self.settings["base_interval_minutes"] = self.base_interval_spin.value()
        self.settings["retry_moltbook_5xx"] = self.retry_5xx_checkbox.isChecked()
        self.settings["retry_interval_minutes_5xx"] = self.retry_5xx_interval_spin.value()
        self.settings["use_fixed_backoff"] = self.fixed_backoff_checkbox.isChecked()
        self.settings["fixed_backoff_minutes"] = self.fixed_backoff_spin.value()
        self.settings["enabled"] = self.enabled_checkbox.isChecked()
        self.settings["language"] = self.lang

        save_daemon_settings(self.settings)

        QtWidgets.QMessageBox.information(
            self,
            STRINGS[self.lang]["title"],
            STRINGS[self.lang]["saved_msg"],
        )
        self._update_summary()
        self._update_log_view()

    def _start_daemon_background(self):
        """
        Startuje daemona w tle z aktualnymi ustawieniami, bez popupów.
        Używane przy auto-starcie GUI, gdy zaznaczone jest 'Włącz daemona przy starcie'.
        """
        daemon_path = BASE_DIR / "mbc20_auto_daemon.py"
        if not daemon_path.exists():
            return

        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            gui_pid = os.getpid()
            subprocess.Popen(
                [sys.executable, str(daemon_path), "--gui-pid", str(gui_pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except Exception:
            pass

    def on_start_daemon_clicked(self):
        self.on_save_clicked()

        daemon_path = BASE_DIR / "mbc20_auto_daemon.py"
        s = STRINGS[self.lang]
        if not daemon_path.exists():
            QtWidgets.QMessageBox.warning(
                self,
                s["title"],
                s["daemon_not_found"],
            )
            return

        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            gui_pid = os.getpid()
            subprocess.Popen(
                [sys.executable, str(daemon_path), "--gui-pid", str(gui_pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            QtWidgets.QMessageBox.information(
                self,
                s["title"],
                s["daemon_start_ok"],
            )
            self._update_log_view()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                s["title"],
                s["daemon_start_fail"].format(error=e),
            )

    def on_stop_daemon_clicked(self):
        s = STRINGS[self.lang]
        count = stop_all_daemons()
        remove_lockfile()
        if count > 0:
            msg = s["daemon_stop_ok"].format(count=count)
        else:
            msg = s["daemon_stop_none"]
        QtWidgets.QMessageBox.information(self, s["title"], msg)
        self._update_log_view()

    def closeEvent(self, event: QtGui.QCloseEvent):
        remove_lockfile()
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = DaemonSettingsWindow()
    w.resize(520, 620)
    w.move(100, 100)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
