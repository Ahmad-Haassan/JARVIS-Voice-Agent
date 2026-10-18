"""
Main Assistant Window — PC Wide-Screen Premium Edition.
Features: Side-by-Side Command Center, Neon Pulsing Orb, Glassmorphic Chat, Frameless.
"""
import math
import time
import os
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QFrame, 
    QGraphicsDropShadowEffect, QScrollArea, QSizePolicy, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QPointF
from PyQt6.QtGui import QColor, QIcon, QPainter, QRadialGradient, QBrush, QFont, QLinearGradient, QPen

from core.utils.logger import get_logger
from core.utils import config as cfg

logger = get_logger("gui.main")

class CyberRing(QWidget):
    """Multi-layered rotating rings with dynamic colors and speeds."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self._rotation = 0
        self._listening = False
        self._processing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    def set_listening(self, listening: bool):
        self._listening = listening
        if listening: self._processing = False

    def set_processing(self, processing: bool):
        self._processing = processing

    def paintEvent(self, event):
        self._rotation += 2 if self._listening else (4 if self._processing else 1)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        
        # Base colors
        c1 = QColor(0, 255, 255) if self._listening else (QColor(168, 85, 247) if self._processing else QColor(99, 102, 241))
        c2 = QColor(255, 215, 0) if self._processing else QColor(30, 64, 175)
        
        # 1. Outer Ring (Slow)
        pen = QPen(c1, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(center.x()-100, center.y()-100, 200, 200, int(self._rotation * 16), 120 * 16)
        painter.drawArc(center.x()-100, center.y()-100, 200, 200, int((self._rotation + 180) * 16), 120 * 16)

        # 2. Middle Ring (Reverse)
        pen.setColor(c2)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawArc(center.x()-80, center.y()-80, 160, 160, int(-self._rotation * 2 * 16), 90 * 16)
        painter.drawArc(center.x()-80, center.y()-80, 160, 160, int((-self._rotation * 2 + 180) * 16), 90 * 16)

        # 3. Inner Core Glow
        grad = QRadialGradient(QPointF(center), 60)
        alpha = 150 if self._listening else (200 if self._processing else 50)
        grad.setColorAt(0, QColor(c1.red(), c1.green(), c1.blue(), alpha))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 60, 60)

class GlassBubble(QFrame):
    """Horizontal Glassmorphic message bubble."""
    def __init__(self, text, is_user=True):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Segoe UI", 10))
        
        if is_user:
            self.setStyleSheet("background-color: rgba(64, 156, 255, 40); border: 1px solid rgba(255, 255, 255, 20); border-radius: 15px; color: white;")
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.setStyleSheet("background-color: rgba(255, 255, 255, 12); border: 1px solid rgba(255, 255, 255, 10); border-radius: 15px; color: #f0f0f0;")
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.label)

class VoiceWorker(QThread):
    update_signal = pyqtSignal(str, bool)
    listening_signal = pyqtSignal(bool)
    status_signal = pyqtSignal(str)
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self._running = True
        self._is_processing = False # Prevent session overlap
        self.stt = None
        self.nlp = None
        self.router = None
        self.tts = None
        self.wake = None
        self._cancel_flag = False

    def _on_wake(self):
        from core.voice.wake_word import get_wake_detector
        wake = get_wake_detector()
        
        if not self.tts or not self.stt:
            logger.warning("Voice engine not ready.")
            return
            
        if self._is_processing:
            logger.info("Session takeover: Stopping previous session.")
            self._cancel_flag = True
            self.tts.stop()
            time.sleep(0.3)

        try:
            self._is_processing = True
            self._cancel_flag = False
            
            # 1. Wake Response
            WAKE_POOL = ["Yes?", "I'm listening.", "How can I help?", "Hmm, yes?", "Go ahead, sir."]
            import random
            resp = random.choice(WAKE_POOL)
            self.tts.speak(resp, block=True)
            if self._cancel_flag: return
            
            # 2. Listen for Command
            self.listening_signal.emit(True)
            wake.stop()
            text = self.stt.listen(timeout=7.0) 
            wake.start()
            self.listening_signal.emit(False)
            
            if self._cancel_flag: return
            
            if text:
                self.update_signal.emit(text, True)
                
                # 3. Process Intent
                result = self.nlp.process(text)
                intent = result.get("intent", "unknown")
                nlp_resp = result.get("response", "")
                
                if self._cancel_flag: return
                
                # 4. Immediate AI Feedback
                if nlp_resp:
                    self.tts.speak(nlp_resp, block=True) 
                
                if self._cancel_flag: return
                
                # 5. Execute Action
                exec_result = self.router.route({
                    "intent": intent, 
                    "entities": result.get("entities"), 
                    "response": nlp_resp
                })
                
                if self._cancel_flag: return
                
                # 6. Final Spoken Feedback
                final_resp = exec_result.response or nlp_resp
                self.update_signal.emit(final_resp, False)
                
                # Speak if router added new info or if nothing was spoken yet
                if exec_result.response and exec_result.response != nlp_resp:
                    self.tts.speak(exec_result.response, block=True)
                elif not nlp_resp and final_resp:
                    self.tts.speak(final_resp, block=True)
                
                if self._cancel_flag: return
                
                # 7. Task Confirmation
                TASK_INTENTS = ["open_app", "close_app", "system_control", "file_action", "write_content", "send_whatsapp", "youtube_play", "work_mode"]
                if exec_result.success and intent in TASK_INTENTS:
                    self.tts.speak("Command completed.", block=True)
            else:
                logger.info("No command detected.")
        except Exception as e:
            logger.error(f"Voice session error: {e}")
        finally:
            self._is_processing = False
            self.listening_signal.emit(False)
            if not wake._running:
                wake.start()
            self.listening_signal.emit(False)
            if not wake._running:
                wake.start()

    def trigger(self):
        """Manually trigger listening."""
        if not self.tts or not self.stt:
            logger.warning("Voice engine not ready for manual trigger.")
            return
        threading.Thread(target=self._on_wake, daemon=True).start()

    def run(self):
        self.status_signal.emit("INITIALIZING VOICE ENGINE...")
        from core.voice.stt import get_stt
        from core.voice.tts import get_tts
        from core.voice.wake_word import get_wake_detector
        from core.ai.nlp_engine import get_nlp
        from core.ai.command_router import get_router
        
        try:
            self.stt = get_stt()
            self.tts = get_tts()
            self.nlp = get_nlp()
            self.wake = get_wake_detector(on_detected=self._on_wake)
            self.router = get_router()
            
            self.status_signal.emit("SYSTEM READY")
            
            # Startup Greeting
            GREETINGS = [
                "Hey! How can I help you?",
                "Jarvis online. What do you need?",
                "Good to see you. I'm ready.",
                "Hello! Say my name whenever you need me.",
            ]
            import random
            self.tts.speak(random.choice(GREETINGS))
            
            self.wake.start()
            while self._running: time.sleep(0.5)
        except Exception as e:
            logger.error(f"VoiceWorker init failed: {e}")
            self.status_signal.emit("VOICE ENGINE ERROR")
            
    def stop(self):
        self._running = False
        if self.wake:
            self.wake.stop()
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.setWindowTitle("Jarvis PC")
        self.setFixedSize(1000, 650) # PC SIZE
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()
        self.worker = VoiceWorker(auth_manager)
        self.worker.update_signal.connect(self.add_message)
        self.worker.listening_signal.connect(self.orb.set_listening)
        self.worker.status_signal.connect(self._on_status_change)
        self.worker.start()

    def _on_status_change(self, status: str):
        self.status.setText(status)
        if status == "SYSTEM READY":
            self.activate_btn.setEnabled(True)
        else:
            self.activate_btn.setEnabled(False)

    def _setup_ui(self):
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 1000, 650)
        self.container.setStyleSheet("background-color: #020617; border-radius: 20px; border: 1px solid rgba(255,255,255,10);")
        
        main_layout = QHBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── LEFT PANEL (ORB & STATUS) ───
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("background-color: rgba(15, 23, 42, 0.5); border-right: 1px solid rgba(255,255,255,5); border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(20, 40, 20, 40)

        title = QLabel("JARVIS SYSTEM")
        title.setStyleSheet("color: #6366f1; font-weight: 900; letter-spacing: 3px; font-size: 18px;")
        lp_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        lp_layout.addStretch()
        self.orb = CyberRing()
        lp_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        lp_layout.addStretch()

        self.status = QLabel("SYSTEM IDLE")
        self.status.setStyleSheet("color: #475569; font-size: 12px; font-weight: bold;")
        lp_layout.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignCenter)
        
        lp_layout.addSpacing(20)
        self.activate_btn = QPushButton("ACTIVATE JARVIS")
        self.activate_btn.setFixedSize(200, 50)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #a855f7);
                color: white;
                border-radius: 25px;
                font-weight: 900;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
        self.activate_btn.clicked.connect(lambda: self.worker.trigger())
        self.activate_btn.setEnabled(False) # Disabled until READY
        lp_layout.addWidget(self.activate_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(left_panel)

        # ─── RIGHT PANEL (CHAT & ACTIONS) ───
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(30, 30, 30, 30)

        # Top Bar
        top_bar = QHBoxLayout()
        
        # System Title
        sys_info = QLabel("ACTIVE SESSION")
        sys_info.setStyleSheet("color: #475569; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        top_bar.addWidget(sys_info)
        
        top_bar.addStretch()
        
        # Minimize Button
        min_btn = QPushButton("—")
        min_btn.setFixedSize(30, 30)
        min_btn.setStyleSheet("color: #475569; font-size: 16px; background: transparent;")
        min_btn.clicked.connect(self.showMinimized)
        top_bar.addWidget(min_btn)
        
        # Close Button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("color: #475569; font-size: 24px; background: transparent;")
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        rp_layout.addLayout(top_bar)

        # Chat
        self.chat_log = QListWidget()
        self.chat_log.setStyleSheet("background: transparent; border: none;")
        rp_layout.addWidget(self.chat_log)

        # Chat Input Area
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or ask Jarvis...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 15px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #6366f1;
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        self.input_field.returnPressed.connect(self._on_text_submitted)
        rp_layout.addWidget(self.input_field)

        # Quick Actions Grid
        qa_label = QLabel("QUICK COMMANDS")
        qa_label.setStyleSheet("color: #475569; font-size: 10px; font-weight: bold; margin-top: 10px;")
        rp_layout.addWidget(qa_label)
        
        self.qa_grid = QGridLayout()
        self.qa_grid.setSpacing(10)
        
        qa_btns = [
            ("⚡ Work Mode", "start work mode"), ("🚀 Antigravity", "open antigravity"),
            ("🌐 Chrome", "open chrome"), ("🎵 YouTube", "play lofi on youtube"),
            ("📸 Screenshot", "take screenshot"), ("💬 WhatsApp", "open whatsapp"),
            ("📁 Folder", "create desktop folder"), ("⚙️ Settings", "open settings")
        ]
        
        for i, (label, cmd) in enumerate(qa_btns):
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 10px;
                    color: #94a3b8;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: rgba(99, 102, 241, 0.1);
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, c=cmd: self._on_quick_action(c))
            self.qa_grid.addWidget(btn, i // 4, i % 4)
        
        rp_layout.addLayout(self.qa_grid)

        # Bottom Bar (Utility Actions)
        bottom_bar = QHBoxLayout()
        btns = [("Settings", "settings"), ("Screenshot", "screenshot"), ("Clear", "clear")]
        for label, cmd in btns:
            btn = QPushButton(label)
            btn.setStyleSheet("QPushButton{background: rgba(255,255,255,5); color: #94a3b8; border-radius: 10px; padding: 10px 20px;} QPushButton:hover{background: #6366f1; color: white;}")
            if cmd == "clear": btn.clicked.connect(self.chat_log.clear)
            else: btn.clicked.connect(lambda checked, c=cmd: self.manual_trigger(c))
            bottom_bar.addWidget(btn)
        rp_layout.addLayout(bottom_bar)
        main_layout.addWidget(right_panel)

    def add_message(self, text, is_user=True):
        bubble = GlassBubble(text, is_user)
        item = QListWidgetItem(self.chat_log)
        item.setSizeHint(bubble.sizeHint() + QSize(0, 10))
        self.chat_log.addItem(item)
        self.chat_log.setItemWidget(item, bubble)
        self.chat_log.scrollToBottom()

    def _on_text_submitted(self):
        text = self.input_field.text().strip()
        if not text: return
        self.input_field.clear()
        self.add_message(text, True)
        
        # UI state: Thinking
        self.orb.set_processing(True)
        self.status.setText("SYSTEM PROCESSING")
        
        # Run processing in a separate thread to avoid UI freeze
        threading.Thread(target=self._process_text_command, args=(text,), daemon=True).start()

    def _process_text_command(self, text):
        from core.ai.nlp_engine import get_nlp
        from core.ai.command_router import get_router
        from core.voice.tts import get_tts
        
        nlp = get_nlp()
        router = get_router()
        tts = get_tts()
        
        result = nlp.process(text)
        nlp_resp = result.get("response", "")
        if nlp_resp:
            logger.info(f"Speaking confirmation: {nlp_resp}")
            tts.speak(nlp_resp, block=True) # Confirm before action
            
        exec_result = router.route({
            "intent": result.get("intent"), 
            "entities": result.get("entities"), 
            "response": nlp_resp
        })
        
        # Update UI from main thread
        final_resp = exec_result.response or nlp_resp
        QTimer.singleShot(0, lambda: self.add_message(final_resp, False))
        QTimer.singleShot(0, lambda: self.orb.set_processing(False))
        QTimer.singleShot(0, lambda: self.status.setText("SYSTEM IDLE"))
        
        # Speak if the router response is different (e.g. it failed or added info)
        if exec_result.response and exec_result.response != nlp_resp:
            tts.speak(exec_result.response)
        elif not nlp_resp and exec_result.response:
            tts.speak(exec_result.response)
            
        # After completing a TASK (not a chat), say "Command completed"
        TASK_INTENTS = ["open_app", "close_app", "system_control", "file_action", "write_content", "send_whatsapp", "youtube_play", "work_mode"]
        if exec_result.success and result.get("intent") in TASK_INTENTS:
            logger.info(f"Task '{result.get('intent')}' successful, speaking completion feedback.")
            tts.speak("Command completed.")

    def manual_trigger(self, cmd):
        intent_map = {"screenshot": ("system_control", {"action": "screenshot"}), "settings": ("open_app", {"app": "settings"})}
        if cmd in intent_map:
            intent, entities = intent_map[cmd]
            from core.ai.command_router import get_router
            res = get_router().route({"intent": intent, "entities": entities, "response": "Action triggered."})
            self.add_message(res.response, False)

    def _on_quick_action(self, cmd_text):
        """Handle quick action button clicks by simulating text submission."""
        self.input_field.setText(cmd_text)
        self._on_text_submitted()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.drag_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
    def closeEvent(self, event): self.worker.stop(); super().closeEvent(event)