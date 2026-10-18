"""
Main Assistant Window — JARVIS Sci-Fi Arc Reactor HUD Edition.
Matches the high-tech Iron Man cyberpunk interface with:
- 360-degree dynamic radial audio waveform & glowing J core
- Live CPU semi-circular speedometer gauge & RAM glow bar
- HUD status card (Wake-Word & Local STT engine)
- Recent voice commands live telemetry card
- Tech bracket chamfered frame and animated pulsing status
"""
import math
import time
import os
import threading
import psutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QFrame, 
    QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QIcon, QPainter, QRadialGradient, QBrush, QFont, 
    QLinearGradient, QPen, QPainterPath, QPolygonF
)

from core.utils.logger import get_logger
from core.utils import config as cfg

logger = get_logger("gui.main")

# ==========================================
# 1. 360-DEGREE RADIAL AUDIO WAVE REACTOR
# ==========================================
class ArcReactorWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 360)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._listening = False
        self._processing = False
        self._phase = 0.0
        self._rot_angle = 0.0
        self._pulse_val = 0.0
        self._bars_count = 84

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(20)  # 50 FPS smooth animation

    def set_listening(self, listening: bool):
        self._listening = listening
        if listening:
            self._processing = False
        self.update()

    def set_processing(self, processing: bool):
        self._processing = processing
        self.update()

    def _tick(self):
        speed = 0.08 if self._listening else (0.12 if self._processing else 0.035)
        self._phase += speed
        self._rot_angle = (self._rot_angle + (2.8 if self._listening else 0.8)) % 360
        self._pulse_val = (math.sin(self._phase * 2.2) + 1.0) * 0.5
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        base_r = 82.0  # Core radius

        # 1. Soft atmospheric glow behind the reactor
        glow_r = 180.0 if self._listening else 150.0
        glow_alpha = 65 if self._listening else (85 if self._processing else 35)
        glow_col = QColor(168, 85, 247, glow_alpha) if self._processing else QColor(0, 242, 254, glow_alpha)
        glow_grad = QRadialGradient(QPointF(cx, cy), glow_r)
        glow_grad.setColorAt(0.0, glow_col)
        glow_grad.setColorAt(0.55, QColor(0, 242, 254, int(glow_alpha * 0.35)))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # 2. 360-Degree Radial Audio Waveform (Equalizer Bars)
        # Quad-peak wave shape matching the screenshot (crests at top, bottom, left, right)
        bars = self._bars_count
        for i in range(bars):
            ang_deg = i * 360.0 / bars
            ang_rad = math.radians(ang_deg)

            # Prominent crests at cardinal points (0, 90, 180, 270)
            q_factor = abs(math.cos(ang_rad * 2.0)) ** 1.8
            harm1 = math.sin(ang_rad * 4.0 - self._phase * 3.0) * 0.35
            harm2 = math.cos(ang_rad * 6.0 + self._phase * 2.0) * 0.2

            if self._listening:
                amp = 18.0 + 38.0 * q_factor + 16.0 * math.sin(self._phase * 6.0 + i * 0.5)
            elif self._processing:
                amp = 14.0 + 28.0 * abs(math.sin(ang_rad * 3.0 + self._phase * 4.0))
            else:
                amp = 8.0 + 30.0 * q_factor + 8.0 * harm1 + 4.0 * harm2
                amp += self._pulse_val * 5.0

            amp = max(4.0, min(amp, 58.0))

            r_start = base_r + 4.0
            r_end = r_start + amp

            x1 = cx + r_start * math.cos(ang_rad)
            y1 = cy + r_start * math.sin(ang_rad)
            x2 = cx + r_end * math.cos(ang_rad)
            y2 = cy + r_end * math.sin(ang_rad)

            # Dynamic neon color along ray
            if self._listening:
                bar_col = QColor(0, 242, 254, int(190 + 65 * q_factor))
                pen_w = 2.4
            elif self._processing:
                bar_col = QColor(192, 132, 252, int(180 + 75 * q_factor))
                pen_w = 2.2
            else:
                alpha = int(150 + 105 * (amp / 50.0))
                bar_col = QColor(0, 230, 255, min(255, alpha))
                pen_w = 2.0

            painter.setPen(QPen(bar_col, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # 3. Outer Rotating Dashed Sci-Fi Tech Ring
        outer_pen = QPen(QColor(0, 242, 254, 85), 1.2)
        outer_pen.setDashPattern([3, 5, 8, 5])
        painter.setPen(outer_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._rot_angle)
        painter.drawEllipse(QPointF(0, 0), base_r + 7.5, base_r + 7.5)

        # Tick marks on the rotating outer tech ring
        painter.setPen(QPen(QColor(0, 242, 254, 140), 1.5))
        for t in range(0, 360, 45):
            trad = math.radians(t)
            tx1 = (base_r + 7.5) * math.cos(trad)
            ty1 = (base_r + 7.5) * math.sin(trad)
            tx2 = (base_r + 13.5) * math.cos(trad)
            ty2 = (base_r + 13.5) * math.sin(trad)
            painter.drawLine(QPointF(tx1, ty1), QPointF(tx2, ty2))
        painter.restore()

        # 4. Main Luminous Cyan Ring (Reactor Rim)
        main_ring_pen = QPen(QColor(0, 242, 254, 255), 2.8)
        painter.setPen(main_ring_pen)
        painter.drawEllipse(QPointF(cx, cy), base_r, base_r)

        # Soft glowing rim halo
        painter.setPen(QPen(QColor(0, 242, 254, 50), 7.0))
        painter.drawEllipse(QPointF(cx, cy), base_r, base_r)

        # 5. Core Disc (Deep Dark Cosmic Glass)
        core_grad = QRadialGradient(QPointF(cx - 20, cy - 20), base_r - 2)
        core_grad.setColorAt(0.0, QColor(7, 26, 48, 245))
        core_grad.setColorAt(0.65, QColor(3, 13, 27, 250))
        core_grad.setColorAt(1.0, QColor(2, 6, 14, 255))
        painter.setPen(QPen(QColor(0, 242, 254, 110), 1.0))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QPointF(cx, cy), base_r - 2, base_r - 2)

        # 6. Stylized "J" Emblem in Center
        self._draw_j_emblem(painter, cx, cy - 14)

        # 7. "JARVIS" Text
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(240, 249, 255, 235)))
        painter.drawText(QRectF(cx - 70, cy + 24, 140, 26), Qt.AlignmentFlag.AlignCenter, "J A R V I S")

    def _draw_j_emblem(self, painter: QPainter, cx: float, cy: float):
        """Draws the crisp stylized J neon logo from the screenshot."""
        painter.save()
        painter.translate(cx, cy)

        # Outer glowing path for J
        path = QPainterPath()
        path.moveTo(6, -26)
        path.lineTo(6, 6)
        path.cubicTo(6, 18, -4, 24, -14, 24)
        path.cubicTo(-24, 24, -28, 16, -28, 10)

        # Halo glow
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 242, 254, 90), 8.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

        # Outer cyan stroke
        painter.setPen(QPen(QColor(0, 242, 254, 255), 4.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

        # Inner white bright core
        painter.setPen(QPen(QColor(240, 253, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

        # Top horizontal serif bar
        painter.setPen(QPen(QColor(0, 242, 254, 255), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(-2, -26), QPointF(14, -26))

        painter.restore()


# ==========================================
# 2. CPU SPEEDOMETER SEMI-GAUGE
# ==========================================
class CpuGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 44)
        self._val = 3.2

    def set_value(self, val: float):
        self._val = max(0.0, min(100.0, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0 + 4.0
        cy = self.height() - 4.0
        r = 24.0

        # 1. Background semi-circle track
        track_pen = QPen(QColor(255, 255, 255, 28), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2), 0 * 16, 180 * 16)

        # 2. Active cyan arc (proportional to CPU %)
        span = int((self._val / 100.0) * 180.0)
        span = max(6, span)
        gauge_pen = QPen(QColor(0, 242, 254, 255), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(gauge_pen)
        painter.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2), 180 * 16, -span * 16)

        # 3. Glowing needle/tip pointer
        tip_angle_deg = 180.0 - (self._val / 100.0) * 180.0
        tip_rad = math.radians(tip_angle_deg)
        tx = cx + r * math.cos(tip_rad)
        ty = cy - r * math.sin(tip_rad)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.drawEllipse(QPointF(tx, ty), 2.5, 2.5)

        # Center small pivot dot
        painter.setBrush(QBrush(QColor(0, 242, 254, 180)))
        painter.drawEllipse(QPointF(cx, cy - 2), 2.0, 2.0)


# ==========================================
# 3. RAM GLOWING PROGRESS BAR
# ==========================================
class RamBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._pct = 37.6

    def set_percent(self, pct: float):
        self._pct = max(0.0, min(100.0, pct))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 22)))
        painter.drawRoundedRect(QRectF(0, 1, w, h - 2), 3, 3)

        # Active cyan fill
        fill_w = max(6.0, (self._pct / 100.0) * w)
        grad = QLinearGradient(0, 0, fill_w, 0)
        grad.setColorAt(0.0, QColor(0, 242, 254, 160))
        grad.setColorAt(1.0, QColor(0, 242, 254, 255))
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(QRectF(0, 1, fill_w, h - 2), 3, 3)

        # Illuminated rounded head
        painter.setBrush(QBrush(QColor(224, 247, 250, 240)))
        painter.drawEllipse(QPointF(fill_w - 2.5, h / 2.0), 2.5, 2.5)


# ==========================================
# 4. ANIMATED 4-DOT STATUS INDICATOR
# ==========================================
class PulseDotsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 14)
        self._active_idx = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(230)

    def _step(self):
        self._active_idx = (self._active_idx + 1) % 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        spacing = 15.0
        start_x = 11.0
        cy = self.height() / 2.0

        for i in range(4):
            cx = start_x + i * spacing
            if i == self._active_idx:
                # Active glowing dot
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 242, 254, 255)))
                painter.drawEllipse(QPointF(cx, cy), 3.8, 3.8)
                painter.setBrush(QBrush(QColor(0, 242, 254, 60)))
                painter.drawEllipse(QPointF(cx, cy), 6.5, 6.5)
            else:
                # Dim dot
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 45)))
                painter.drawEllipse(QPointF(cx, cy), 2.8, 2.8)


# ==========================================
# 5. SCI-FI HUD FRAME & BACKGROUND CONTAINER
# ==========================================
class HudFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        cut = 18.0  # Angled chamfer size

        # 1. Main Background Gradient
        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0.0, QColor(4, 9, 18, 255))
        bg_grad.setColorAt(0.5, QColor(6, 14, 26, 255))
        bg_grad.setColorAt(1.0, QColor(2, 6, 13, 255))

        # 2. Outer Chamfered Tech Border Path
        outer_path = QPainterPath()
        outer_path.moveTo(cut, 0)
        outer_path.lineTo(w - cut, 0)
        outer_path.lineTo(w, cut)
        outer_path.lineTo(w, h - cut)
        outer_path.lineTo(w - cut, h)
        outer_path.lineTo(cut, h)
        outer_path.lineTo(0, h - cut)
        outer_path.lineTo(0, cut)
        outer_path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawPath(outer_path)

        # 3. Outer Glowing Cyan Tech Border
        border_pen = QPen(QColor(0, 242, 254, 110), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(outer_path)

        # 4. Tech Corner Brackets & Accent Notches
        bracket_pen = QPen(QColor(0, 242, 254, 230), 2.2)
        painter.setPen(bracket_pen)

        # Top-left corner tech lines
        painter.drawLine(QPointF(0, cut + 14), QPointF(0, cut))
        painter.drawLine(QPointF(0, cut), QPointF(cut, 0))
        painter.drawLine(QPointF(cut, 0), QPointF(cut + 24, 0))
        # Top-left double slash decor
        painter.drawLine(QPointF(cut + 32, 2), QPointF(cut + 38, 9))
        painter.drawLine(QPointF(cut + 40, 2), QPointF(cut + 46, 9))

        # Top-right corner tech lines
        painter.drawLine(QPointF(w - cut - 24, 0), QPointF(w - cut, 0))
        painter.drawLine(QPointF(w - cut, 0), QPointF(w, cut))
        painter.drawLine(QPointF(w, cut), QPointF(w, cut + 14))

        # Bottom-left corner tech lines
        painter.drawLine(QPointF(0, h - cut - 14), QPointF(0, h - cut))
        painter.drawLine(QPointF(0, h - cut), QPointF(cut, h))
        painter.drawLine(QPointF(cut, h), QPointF(cut + 28, h))

        # Bottom-right corner tech lines
        painter.drawLine(QPointF(w - cut - 28, h), QPointF(w - cut, h))
        painter.drawLine(QPointF(w - cut, h), QPointF(w, h - cut))
        painter.drawLine(QPointF(w, h - cut), QPointF(w, h - cut - 14))

        # 5. Inner Inset Wire Guide Lines (Subtle HUD detailing)
        inner_pen = QPen(QColor(0, 242, 254, 25), 1.0)
        painter.setPen(inner_pen)
        inset = 6.0
        inner_path = QPainterPath()
        inner_path.moveTo(cut + inset, inset)
        inner_path.lineTo(w - cut - inset, inset)
        inner_path.lineTo(w - inset, cut + inset)
        inner_path.lineTo(w - inset, h - cut - inset)
        inner_path.lineTo(w - cut - inset, h - inset)
        inner_path.lineTo(cut + inset, h - inset)
        inner_path.lineTo(inset, h - cut - inset)
        inner_path.lineTo(inset, cut + inset)
        inner_path.closeSubpath()
        painter.drawPath(inner_path)


# ==========================================
# 6. VOICE WORKER THREAD
# ==========================================
class VoiceWorker(QThread):
    update_signal = pyqtSignal(str, bool)  # text, is_user
    listening_signal = pyqtSignal(bool)
    status_signal = pyqtSignal(str)

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self._running = True
        self._is_processing = False
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
            time.sleep(0.2)

        try:
            self._is_processing = True
            self._cancel_flag = False
            wake.pause()
            self.status_signal.emit("JARVIS LISTENING...")

            # 1. Wake Response Chime / Confirmation
            WAKE_POOL = ["Yes, sir?", "I'm listening.", "How can I help you?", "Yes, go ahead."]
            import random
            resp = random.choice(WAKE_POOL)
            self.tts.speak(resp, block=True)
            if self._cancel_flag:
                return

            # 2. Listen for Command
            self.listening_signal.emit(True)
            text = self.stt.listen(timeout=6.0)
            self.listening_signal.emit(False)

            if self._cancel_flag:
                return

            if text:
                self.update_signal.emit(text, True)
                self.status_signal.emit("PROCESSING...")

                # 3. Process Intent
                result = self.nlp.process(text)
                intent = result.get("intent", "unknown")
                nlp_resp = result.get("response", "")

                if self._cancel_flag:
                    return

                # 4. Immediate AI Feedback
                if nlp_resp:
                    self.tts.speak(nlp_resp, block=True)

                if self._cancel_flag:
                    return

                # 5. Execute Action
                exec_result = self.router.route({
                    "intent": intent,
                    "entities": result.get("entities"),
                    "response": nlp_resp
                })

                if self._cancel_flag:
                    return

                # 6. Final Spoken Feedback
                final_resp = exec_result.response or nlp_resp
                self.update_signal.emit(final_resp, False)

                if exec_result.response and exec_result.response != nlp_resp:
                    self.tts.speak(exec_result.response, block=True)
                elif not nlp_resp and final_resp:
                    self.tts.speak(final_resp, block=True)

                if self._cancel_flag:
                    return

                # 7. Task Confirmation
                TASK_INTENTS = [
                    "open_app", "close_app", "open_folder", "open_file",
                    "open_in", "system_control", "file_action", "write_content",
                    "send_whatsapp", "youtube_play", "work_mode"
                ]
                if exec_result.success and intent in TASK_INTENTS:
                    self.tts.speak("Command completed.", block=True)
            else:
                logger.info("No command detected.")
        except Exception as e:
            logger.error(f"Voice session error: {e}")
        finally:
            self._is_processing = False
            self.listening_signal.emit(False)
            self.status_signal.emit("STANDBY [ACTIVE]")
            wake.resume()

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

            self.status_signal.emit("STANDBY [ACTIVE]")

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
            while self._running:
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"VoiceWorker init failed: {e}")
            self.status_signal.emit("VOICE ENGINE ERROR")

    def stop(self):
        self._running = False
        if self.wake:
            self.wake.stop()
        self.wait()


# ==========================================
# 7. MAIN SCI-FI HUD WINDOW
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, auth_manager=None):
        super().__init__()
        if auth_manager is None:
            try:
                from core.auth.auth_manager import get_auth_manager
                auth_manager = get_auth_manager()
            except Exception:
                auth_manager = None
        self.auth_manager = auth_manager
        self.setWindowTitle("JARVIS v2.4.1 [ACTIVE]")
        self.setFixedSize(1020, 640)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.drag_pos = None
        self._setup_ui()

        # Telemetry Timer (Updates CPU & RAM every second)
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._update_telemetry)
        self.telemetry_timer.start(1000)

        # Worker initialization
        self.worker = VoiceWorker(auth_manager)
        self.worker.update_signal.connect(self._on_command_update)
        self.worker.listening_signal.connect(self._on_listening_state)
        self.worker.status_signal.connect(self._on_status_change)
        self.worker.start()

    def _setup_ui(self):
        # Master Sci-Fi HUD Frame
        self.frame = HudFrame(self)
        self.frame.setGeometry(0, 0, 1020, 640)

        # Main Layout inside Frame
        main_layout = QVBoxLayout(self.frame)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(0)

        # ─── TOP TITLE BAR ───
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(12, 4, 12, 10)

        # Left Brand Emblem & Title
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)

        # Small neon J badge
        badge = QLabel("J")
        badge.setFixedSize(22, 22)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background: rgba(0, 242, 254, 0.15);
                border: 1px solid #00f2fe;
                border-radius: 5px;
                color: #00f2fe;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 900;
                font-size: 13px;
            }
        """)
        brand_layout.addWidget(badge)

        title_lbl = QLabel("JARVIS v2.4.1")
        title_lbl.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 13px; letter-spacing: 1px;")
        brand_layout.addWidget(title_lbl)

        self.status_tag = QLabel("[ACTIVE]")
        self.status_tag.setStyleSheet("color: #10b981; font-weight: 800; font-size: 13px; letter-spacing: 1px;")
        brand_layout.addWidget(self.status_tag)

        title_bar.addLayout(brand_layout)
        title_bar.addStretch()

        # Window Controls (—  ▢  ✕)
        win_ctrls = QHBoxLayout()
        win_ctrls.setSpacing(6)

        btn_min = QPushButton("—")
        btn_min.setFixedSize(28, 24)
        btn_min.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 13px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        btn_min.clicked.connect(self.showMinimized)
        win_ctrls.addWidget(btn_min)

        btn_max = QPushButton("▢")
        btn_max.setFixedSize(28, 24)
        btn_max.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 13px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        win_ctrls.addWidget(btn_max)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 24)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 13px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #ef4444;
                color: white;
            }
        """)
        btn_close.clicked.connect(self.close)
        win_ctrls.addWidget(btn_close)

        title_bar.addLayout(win_ctrls)
        main_layout.addLayout(title_bar)

        # ─── CORE BODY (THREE COLUMNS) ───
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(10, 0, 10, 0)
        body_layout.setSpacing(18)

        # 1. LEFT CARD: HUD STATUS
        self.left_card = self._build_left_hud_card()
        body_layout.addWidget(self.left_card, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 2. CENTER: ARC REACTOR & LISTENING HUD
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 360-degree Reactor
        self.reactor = ArcReactorWidget()
        self.reactor.clicked.connect(lambda: self.worker.trigger())
        center_layout.addWidget(self.reactor, alignment=Qt.AlignmentFlag.AlignCenter)

        # "AI VOICE ASSISTANT" Label
        assistant_lbl = QLabel("AI VOICE ASSISTANT")
        assistant_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 3px;")
        center_layout.addWidget(assistant_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Dynamic State Label ("LISTENING..." / "STANDBY [ACTIVE]")
        self.state_lbl = QLabel("STANDBY [ACTIVE]")
        self.state_lbl.setStyleSheet("color: #00f2fe; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        center_layout.addWidget(self.state_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Animated 4-dot status wave
        self.dots = PulseDotsWidget()
        center_layout.addWidget(self.dots, alignment=Qt.AlignmentFlag.AlignCenter)

        body_layout.addWidget(center_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. RIGHT COLUMN: TWO STACKED CARDS (System Telemetry & Recent Commands)
        right_container = QWidget()
        right_container.setFixedWidth(250)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # System Telemetry Card (CPU gauge & RAM bar)
        self.sys_card = self._build_system_card()
        right_layout.addWidget(self.sys_card)

        # Recent Voice Commands Card
        self.commands_card = self._build_commands_card()
        right_layout.addWidget(self.commands_card)

        body_layout.addWidget(right_container, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(body_layout)

        # ─── BOTTOM DECORATION & INTERACTIVE COMMAND BAR ───
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(14, 6, 14, 4)

        # Bottom-Left Technical Data Block
        telemetry_block = QLabel("//////  [SYS_V2.4.1] CORE NOMINAL\nSTREAM: 16KHZ MONO SYNCED")
        telemetry_block.setStyleSheet("color: #334155; font-family: 'Consolas', monospace; font-size: 9px; line-height: 1.2;")
        bottom_bar.addWidget(telemetry_block, alignment=Qt.AlignmentFlag.AlignBottom)

        bottom_bar.addSpacing(20)

        # Center Cyber Input Line (Allows typing commands anytime!)
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type a command or click reactor / say \"Jarvis\"...")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 12px;
                padding: 7px 14px;
                color: #e2e8f0;
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            QLineEdit:focus {
                border: 1px solid #00f2fe;
                background: rgba(15, 23, 42, 0.95);
                box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
            }
        """)
        self.cmd_input.returnPressed.connect(self._on_typed_command)
        bottom_bar.addWidget(self.cmd_input, stretch=1)

        bottom_bar.addSpacing(20)

        # Bottom-Right Quick Action Trigger
        btn_trigger = QPushButton("🎙️ TRIGGER MIC")
        btn_trigger.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.12);
                border: 1px solid rgba(0, 242, 254, 0.4);
                border-radius: 10px;
                padding: 6px 14px;
                color: #00f2fe;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.28);
                border-color: #00f2fe;
                color: white;
            }
        """)
        btn_trigger.clicked.connect(lambda: self.worker.trigger())
        bottom_bar.addWidget(btn_trigger, alignment=Qt.AlignmentFlag.AlignBottom)

        main_layout.addLayout(bottom_bar)

    def _build_left_hud_card(self) -> QFrame:
        """Constructs the left glassmorphic HUD Status Card."""
        card = QFrame()
        card.setFixedSize(240, 210)
        card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.35);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 1. Wake-Word Section
        sec1 = QVBoxLayout()
        sec1.setSpacing(4)
        h1 = QHBoxLayout()
        h1.setSpacing(6)
        bar1 = QLabel()
        bar1.setFixedSize(3, 14)
        bar1.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t1 = QLabel("WAKE-WORD:")
        t1.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h1.addWidget(bar1)
        h1.addWidget(t1)
        h1.addStretch()
        sec1.addLayout(h1)

        val1 = QLabel("Active (Vosk)")
        val1.setStyleSheet("color: #00f2fe; font-size: 13px; font-weight: 700; padding-left: 9px; border: none; background: transparent;")
        sec1.addWidget(val1)
        layout.addLayout(sec1)

        # Divider line
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255, 255, 255, 0.06); border: none;")
        layout.addWidget(div)

        # 2. Local STT Section
        sec2 = QVBoxLayout()
        sec2.setSpacing(4)
        h2 = QHBoxLayout()
        h2.setSpacing(6)
        bar2 = QLabel()
        bar2.setFixedSize(3, 14)
        bar2.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t2 = QLabel("LOCAL STT:")
        t2.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h2.addWidget(bar2)
        h2.addWidget(t2)
        h2.addStretch()
        sec2.addLayout(h2)

        val2_title = QLabel("Faster-Whisper")
        val2_title.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 700; padding-left: 9px; border: none; background: transparent;")
        val2_sub = QLabel("(Large-v3)")
        val2_sub.setStyleSheet("color: #7dd3fc; font-size: 11px; font-weight: 600; padding-left: 9px; border: none; background: transparent;")
        sec2.addWidget(val2_title)
        sec2.addWidget(val2_sub)
        layout.addLayout(sec2)

        return card

    def _build_system_card(self) -> QFrame:
        """Constructs the right top System Telemetry Card with Speedometer Gauge & RAM Bar."""
        card = QFrame()
        card.setFixedSize(250, 160)
        card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.35);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        # Header: SYSTEM:
        h_sys = QHBoxLayout()
        h_sys.setSpacing(6)
        bar_sys = QLabel()
        bar_sys.setFixedSize(3, 14)
        bar_sys.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t_sys = QLabel("SYSTEM:")
        t_sys.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h_sys.addWidget(bar_sys)
        h_sys.addWidget(t_sys)
        h_sys.addStretch()
        layout.addLayout(h_sys)

        # CPU Row (Label + % on left, Speedometer Semi-Gauge on right)
        cpu_row = QHBoxLayout()
        cpu_row.setContentsMargins(8, 0, 4, 0)
        cpu_text_layout = QVBoxLayout()
        cpu_text_layout.setSpacing(1)

        lbl_cpu = QLabel("CPU")
        lbl_cpu.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        self.cpu_val_lbl = QLabel("3.2%")
        self.cpu_val_lbl.setMinimumWidth(95)
        self.cpu_val_lbl.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        cpu_text_layout.addWidget(lbl_cpu)
        cpu_text_layout.addWidget(self.cpu_val_lbl)

        cpu_row.addLayout(cpu_text_layout)
        cpu_row.addStretch()

        self.cpu_gauge = CpuGaugeWidget()
        cpu_row.addWidget(self.cpu_gauge)
        layout.addLayout(cpu_row)

        # RAM Row (Label + GB info + Glow Bar)
        ram_layout = QVBoxLayout()
        ram_layout.setContentsMargins(8, 0, 8, 0)
        ram_layout.setSpacing(4)

        ram_header = QHBoxLayout()
        lbl_ram = QLabel("RAM")
        lbl_ram.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        self.ram_val_lbl = QLabel("24.1 GB / 64 GB")
        self.ram_val_lbl.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        ram_header.addWidget(lbl_ram)
        ram_header.addStretch()
        ram_header.addWidget(self.ram_val_lbl)
        ram_layout.addLayout(ram_header)

        self.ram_bar = RamBarWidget()
        ram_layout.addWidget(self.ram_bar)

        layout.addLayout(ram_layout)
        return card

    def _build_commands_card(self) -> QFrame:
        """Constructs the right bottom Recent Voice Commands Card."""
        card = QFrame()
        card.setFixedSize(250, 150)
        card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.35);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Title: RECENT VOICE COMMANDS
        t_cmds = QLabel("RECENT VOICE COMMANDS")
        t_cmds.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; border: none; background: transparent;")
        layout.addWidget(t_cmds)

        # Command list container
        self.cmds_list_layout = QVBoxLayout()
        self.cmds_list_layout.setContentsMargins(0, 2, 0, 0)
        self.cmds_list_layout.setSpacing(4)

        # Seed initial entries matching the screenshot
        now_time = datetime.now()
        initial_entries = [
            ("Open VS Code", now_time.strftime("%H:%M:%S")),
            ("Play Lo-Fi stream", (now_time).strftime("%H:%M:%S")),
            ("Check system diagnostics", (now_time).strftime("%H:%M:%S")),
        ]
        for cmd, ts in initial_entries:
            self._add_command_entry(cmd, ts)

        layout.addLayout(self.cmds_list_layout)
        layout.addStretch()
        return card

    def _add_command_entry(self, text: str, timestamp: str):
        """Adds or updates a voice command entry row in the card."""
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(0, 1, 0, 1)

        # Clean display text (truncate if needed)
        clean_text = text[:17] + ("..." if len(text) > 17 else "")
        lbl_text = QLabel(clean_text)
        lbl_text.setStyleSheet("color: #7dd3fc; font-size: 10px; font-weight: 600; border: none; background: transparent;")

        lbl_time = QLabel(timestamp)
        lbl_time.setStyleSheet("color: #64748b; font-size: 9px; font-family: 'Consolas', monospace; border: none; background: transparent;")

        r_layout.addWidget(lbl_text)
        r_layout.addStretch()
        r_layout.addWidget(lbl_time)

        # Prepend to layout (keep max 3 visible rows)
        if self.cmds_list_layout.count() >= 3:
            old_item = self.cmds_list_layout.takeAt(self.cmds_list_layout.count() - 1)
            if old_item.widget():
                old_item.widget().deleteLater()

        self.cmds_list_layout.insertWidget(0, row)

    def _update_telemetry(self):
        """Updates live CPU and RAM stats from psutil."""
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            self.cpu_val_lbl.setText(f"{cpu_pct:.1f}%")
            self.cpu_gauge.set_value(cpu_pct)

            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            self.ram_val_lbl.setText(f"{used_gb:.1f} GB / {total_gb:.0f} GB")
            self.ram_bar.set_percent(mem.percent)
        except Exception:
            pass

    def _on_command_update(self, text: str, is_user: bool):
        """Called when a user speaks or an assistant response arrives."""
        if is_user:
            cur_time = datetime.now().strftime("%H:%M:%S")
            self._add_command_entry(text, cur_time)
            self.state_lbl.setText(f"CMD: \"{text[:18]}\"")
        else:
            # Assistant response feedback
            self.state_lbl.setText("STANDBY [ACTIVE]")

    def _on_listening_state(self, is_listening: bool):
        self.reactor.set_listening(is_listening)
        if is_listening:
            self.state_lbl.setText("LISTENING...")
            self.state_lbl.setStyleSheet("color: #00f2fe; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.status_tag.setText("[LISTENING]")
            self.status_tag.setStyleSheet("color: #00f2fe; font-weight: 800; font-size: 13px;")
        else:
            self.state_lbl.setText("STANDBY [ACTIVE]")
            self.state_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.status_tag.setText("[ACTIVE]")
            self.status_tag.setStyleSheet("color: #10b981; font-weight: 800; font-size: 13px;")

    def _on_status_change(self, status: str):
        if "LISTENING" in status:
            self._on_listening_state(True)
        elif "PROCESSING" in status:
            self.reactor.set_processing(True)
            self.state_lbl.setText("PROCESSING...")
            self.state_lbl.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.status_tag.setText("[PROCESSING]")
            self.status_tag.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 13px;")
        else:
            self.reactor.set_processing(False)
            self._on_listening_state(False)

    def _on_typed_command(self):
        text = self.cmd_input.text().strip()
        if not text:
            return
        self.cmd_input.clear()

        cur_time = datetime.now().strftime("%H:%M:%S")
        self._add_command_entry(text, cur_time)

        self.reactor.set_processing(True)
        self.state_lbl.setText("PROCESSING...")

        threading.Thread(target=self._process_text_command, args=(text,), daemon=True).start()

    def _process_text_command(self, text: str):
        from core.ai.nlp_engine import get_nlp
        from core.ai.command_router import get_router
        from core.voice.tts import get_tts

        nlp = get_nlp()
        router = get_router()
        tts = get_tts()

        result = nlp.process(text)
        nlp_resp = result.get("response", "")
        if nlp_resp:
            tts.speak(nlp_resp, block=True)

        exec_result = router.route({
            "intent": result.get("intent"),
            "entities": result.get("entities"),
            "response": nlp_resp
        })

        final_resp = exec_result.response or nlp_resp
        if exec_result.response and exec_result.response != nlp_resp:
            tts.speak(exec_result.response)
        elif not nlp_resp and final_resp:
            tts.speak(final_resp)

        TASK_INTENTS = [
            "open_app", "close_app", "open_folder", "open_file",
            "open_in", "system_control", "file_action", "write_content",
            "send_whatsapp", "youtube_play", "work_mode"
        ]
        if exec_result.success and result.get("intent") in TASK_INTENTS:
            tts.speak("Command completed.")

        QTimer.singleShot(0, lambda: self._on_status_change("STANDBY [ACTIVE]"))

    # Window Dragging support for Frameless Window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)