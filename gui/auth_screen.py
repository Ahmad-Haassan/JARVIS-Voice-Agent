"""
AuthScreen — PC Wide-Screen Premium Edition.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush, QRadialGradient
import math

class PremiumAuthOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self._pulse = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(20)

    def paintEvent(self, event):
        self._pulse += 0.04
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.rect().center())
        base_color = QColor(99, 102, 241)
        glow_rad = 60 + 10 * math.sin(self._pulse)
        outer_glow = QRadialGradient(center, glow_rad)
        c_glow = QColor(base_color)
        c_glow.setAlphaF(0.2)
        outer_glow.setColorAt(0, c_glow)
        outer_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(outer_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, glow_rad, glow_rad)
        core_rad = 35 + 3 * math.cos(self._pulse * 0.8)
        core_grad = QRadialGradient(center, core_rad)
        core_grad.setColorAt(0, QColor(255, 255, 255, 200))
        core_grad.setColorAt(1, base_color)
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(center, core_rad, core_rad)

class AuthScreen(QWidget):
    login_success  = pyqtSignal()
    setup_complete = pyqtSignal()

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._auth = auth_manager
        self.setFixedSize(1000, 650) # MATCH MAIN WINDOW SIZE
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame()
        container.setObjectName("AuthContainer")
        container.setFixedSize(1000, 650)
        container.setStyleSheet("background-color: #020617; border-radius: 20px;")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left Side (Visual)
        left_side = QFrame()
        left_side.setFixedWidth(450)
        left_side.setStyleSheet("background-color: #0f172a; border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
        ls_layout = QVBoxLayout(left_side)
        self.orb = PremiumAuthOrb()
        ls_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(left_side)

        # Right Side (Login Form)
        right_side = QFrame()
        rs_layout = QVBoxLayout(right_side)
        rs_layout.setContentsMargins(60, 40, 60, 40)
        rs_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Top Bar (Close button)
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("color: #475569; font-size: 24px; background: transparent; border: none;")
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        rs_layout.addLayout(top_bar)

        title = QLabel("JARVIS OS")
        title.setStyleSheet("color: white; font-size: 32px; font-weight: 900; letter-spacing: 10px;")
        rs_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("System Access Required" if not self._auth.is_first_run() else "New System Initialization")
        subtitle.setStyleSheet("color: #6366f1; font-size: 14px; margin-bottom: 20px;")
        rs_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self._pwd_input = QLineEdit()
        self._pwd_input.setPlaceholderText("Access Password")
        self._pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pwd_input.setFixedWidth(350)
        self._pwd_input.setStyleSheet("background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 15px; color: white; font-size: 16px;")
        self._pwd_input.returnPressed.connect(self._on_login)
        rs_layout.addWidget(self._pwd_input, alignment=Qt.AlignmentFlag.AlignCenter)

        if self._auth.is_first_run():
            self._confirm_input = QLineEdit()
            self._confirm_input.setPlaceholderText("Confirm Access Password")
            self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._confirm_input.setFixedWidth(350)
            self._confirm_input.setStyleSheet(self._pwd_input.styleSheet())
            rs_layout.addWidget(self._confirm_input, alignment=Qt.AlignmentFlag.AlignCenter)

        rs_layout.addSpacing(20)
        self._login_btn = QPushButton("INITIALIZE ACCESS" if not self._auth.is_first_run() else "SETUP SYSTEM")
        self._login_btn.setFixedWidth(350)
        self._login_btn.setStyleSheet("QPushButton{background: #6366f1; color: white; border-radius: 10px; padding: 15px; font-weight: 900;} QPushButton:hover{background: #4f46e5;}")
        self._login_btn.clicked.connect(self._on_login)
        rs_layout.addWidget(self._login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rs_layout.addWidget(self._status)

        layout.addWidget(right_side)
        root.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(10, 10, 30))
        grad.setColorAt(1, QColor(2, 6, 23))
        painter.fillRect(self.rect(), grad)

    def _on_login(self):
        pwd = self._pwd_input.text()
        if self._auth.is_first_run():
            if pwd == self._confirm_input.text() and len(pwd) >= 4:
                self._auth.setup_password(pwd)
                self.setup_complete.emit()
            else: self._show_status("Invalid setup", True)
        else:
            if self._auth.login_password(pwd): self.login_success.emit()
            else: self._show_status("ACCESS DENIED", True)

    def _show_status(self, msg, err):
        self._status.setStyleSheet(f"color: {'#f87171' if err else '#34d399'}; font-size: 13px; font-weight: bold;")
        self._status.setText(msg)
