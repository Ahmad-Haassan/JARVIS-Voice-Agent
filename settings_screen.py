"""
Settings Screen — Premium Glassmorphic Edition.
Modern configuration UI with cosmic theme.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QComboBox, QCheckBox,
    QFormLayout, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPalette
from core.utils import config as cfg

class SettingsScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jarvis Settings")
        self.setMinimumSize(750, 550)
        self.setStyleSheet(self._stylesheet())
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Background Container
        self.container = QFrame()
        self.container.setObjectName("MainFrame")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("SYSTEM CONFIG")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: 800; letter-spacing: 4px;")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Scroll Area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(25)

        # ─── Sections ──────────────────────────────────────────────────────

        # AI Section
        ai_group = self._create_group("AI INTELLIGENCE")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(15)
        
        self.gemini_key = QLineEdit(cfg.get("ai", "gemini_api_key", ""))
        self.gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key.setPlaceholderText("Paste your API Key...")
        ai_form.addRow("Gemini API Key", self.gemini_key)
        
        self.ai_model = QComboBox()
        self.ai_model.addItems(["gemini-1.5-flash", "gemini-1.5-pro"])
        self.ai_model.setCurrentText(cfg.get("ai", "model", "gemini-1.5-flash"))
        ai_form.addRow("Model Engine", self.ai_model)
        inner_layout.addWidget(ai_group)

        # Voice Section
        voice_group = self._create_group("VOICE & HEARING")
        voice_form = QFormLayout(voice_group)
        voice_form.setSpacing(15)
        
        self.wake_word = QLineEdit(cfg.get("app", "wake_word", "jarvis"))
        voice_form.addRow("Wake Word", self.wake_word)
        
        self.tts_rate = QLineEdit(str(cfg.get("voice", "tts_rate", 175)))
        voice_form.addRow("Speech Rate", self.tts_rate)
        inner_layout.addWidget(voice_group)

        # Skills Section
        skill_group = self._create_group("SKILL CONFIG")
        skill_form = QFormLayout(skill_group)
        skill_form.setSpacing(15)
        
        self.weather_city = QLineEdit(cfg.get("skills", "weather_city", "Karachi"))
        skill_form.addRow("Default City", self.weather_city)
        inner_layout.addWidget(skill_group)

        # System Section
        sys_group = self._create_group("SYSTEM PREFERENCES")
        sys_layout = QVBoxLayout(sys_group)
        self.min_to_tray = QCheckBox("Minimize to system tray")
        self.min_to_tray.setChecked(cfg.get("system", "minimize_to_tray", True))
        sys_layout.addWidget(self.min_to_tray)
        
        self.startup = QCheckBox("Start with Windows")
        self.startup.setChecked(cfg.get("system", "startup_with_windows", False))
        sys_layout.addWidget(self.startup)
        inner_layout.addWidget(sys_group)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        save_btn = QPushButton("APPLY CHANGES")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self._save)
        
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        main_layout.addWidget(self.container)

    def _create_group(self, title):
        group = QGroupBox(title)
        return group

    def _save(self):
        cfg.set_value("ai", "gemini_api_key", self.gemini_key.text())
        cfg.set_value("ai", "model", self.ai_model.currentText())
        cfg.set_value("app", "wake_word", self.wake_word.text().lower())
        cfg.set_value("voice", "tts_rate", int(self.tts_rate.text()))
        cfg.set_value("skills", "weather_city", self.weather_city.text())
        cfg.set_value("system", "minimize_to_tray", self.min_to_tray.isChecked())
        cfg.set_value("system", "startup_with_windows", self.startup.isChecked())
        self.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(15, 23, 42))
        grad.setColorAt(1, QColor(2, 6, 23))
        painter.fillRect(self.rect(), grad)

    def _stylesheet(self):
        return """
        QFrame#MainFrame {
            background-color: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(255, 255, 255, 10);
            border-radius: 20px;
        }
        QGroupBox {
            background: rgba(255, 255, 255, 5);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 15px;
            margin-top: 20px;
            padding: 20px;
            color: #818cf8;
            font-weight: 800;
            font-size: 11px;
            letter-spacing: 1px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        QLabel { color: #94a3b8; font-size: 13px; }
        QLineEdit, QComboBox {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 10px;
            color: white;
        }
        QLineEdit:focus { border: 1px solid #6366f1; }
        QCheckBox { color: #cbd5e1; spacing: 10px; }
        QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #6366f1; }
        QCheckBox::indicator:checked { background-color: #6366f1; }
        
        QPushButton#SaveBtn {
            background-color: #6366f1;
            color: white;
            border-radius: 10px;
            padding: 12px 25px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton#CancelBtn {
            background-color: rgba(255, 255, 255, 0.05);
            color: #94a3b8;
            border-radius: 10px;
            padding: 12px 25px;
            font-size: 12px;
        }
        """

from PyQt6.QtWidgets import QGroupBox
