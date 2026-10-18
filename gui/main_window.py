"""
Main Assistant Window — JARVIS Sci-Fi Arc Reactor HUD Edition.
Matches the high-tech Iron Man cyberpunk interface with 5 swappable pages:
- Page 0: CORE HUD (360-degree dynamic radial audio waveform & glowing J core, CPU/RAM telemetry)
- Page 1: PREDEFINED CONTROLS (Apps, System/Media, Automations & Macros)
- Page 2: COMMAND HISTORY & ACTION RECALL (Click any command to re-run / recall!)
- Page 3: MOBILE REMOTE & NETWORK (HTTPS Remote access, QR/Link, mobile microphone guide)
- Page 4: DIAGNOSTICS & AI PIPELINE (Live system audit, voice pipeline controls)
"""
import math
import time
import os
import threading
import psutil
import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QSizePolicy, QStackedWidget,
    QGridLayout, QApplication, QScrollArea
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
        speed = 2.4 if self._processing else (1.4 if self._listening else 0.4)
        self._rot_angle = (self._rot_angle + speed) % 360.0

        phase_speed = 0.16 if self._listening else (0.10 if self._processing else 0.035)
        self._phase = (self._phase + phase_speed) % (math.pi * 2)

        self._pulse_val = 0.5 + 0.5 * math.sin(self._phase * 1.5)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        cyan_neon = QColor(0, 242, 254)
        glow_cyan = QColor(0, 242, 254, int(45 + 50 * self._pulse_val))

        # 1. Outer Deep Cosmic Glow Halo
        halo = QRadialGradient(cx, cy, 175)
        halo.setColorAt(0.0, glow_cyan)
        halo.setColorAt(0.65, QColor(0, 150, 255, int(20 + 20 * self._pulse_val)))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(halo))
        painter.drawEllipse(QPointF(cx, cy), 175, 175)

        # 2. 360-Degree Radial Audio Equalizer Bars (Waveform)
        base_r = 104.0
        for i in range(self._bars_count):
            angle_rad = (2.0 * math.pi * i) / self._bars_count
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            cardinal_weight = math.pow(math.sin(angle_rad * 2.0), 4)
            wave1 = math.sin(angle_rad * 6.0 + self._phase * 2.0)
            wave2 = math.cos(angle_rad * 4.0 - self._phase)

            if self._listening:
                h = 10.0 + 38.0 * cardinal_weight * (0.6 + 0.4 * wave1) + 8.0 * abs(wave2)
                alpha = int(180 + 75 * cardinal_weight)
            elif self._processing:
                rot_offset = (i + int(self._rot_angle / 4)) % self._bars_count
                h = 12.0 + 24.0 * math.sin((rot_offset / self._bars_count) * math.pi * 4.0)
                alpha = 200
            else:
                h = 4.0 + 14.0 * cardinal_weight * (0.5 + 0.5 * math.sin(self._phase + i * 0.1))
                alpha = int(90 + 90 * cardinal_weight)

            h = max(3.0, h)
            r_start = base_r
            r_end = base_r + h

            x1 = cx + r_start * cos_a
            y1 = cy + r_start * sin_a
            x2 = cx + r_end * cos_a
            y2 = cy + r_end * sin_a

            bar_color = QColor(0, 242, 254, alpha)
            bar_pen = QPen(bar_color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(bar_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # 3. Rotating Outer Dashed Tech HUD Ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._rot_angle)
        dash_pen = QPen(QColor(0, 242, 254, 160), 1.5, Qt.PenStyle.CustomDashLine)
        dash_pen.setDashPattern([3.0, 7.0])
        painter.setPen(dash_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 101.0, 101.0)

        # 4 Tech Ring Ticks at 90-degree points
        tick_pen = QPen(cyan_neon, 2.5)
        painter.setPen(tick_pen)
        for deg in [0, 90, 180, 270]:
            painter.save()
            painter.rotate(deg)
            painter.drawLine(QPointF(96, 0), QPointF(106, 0))
            painter.restore()
        painter.restore()

        # 4. Concentric Luminous Inner Tech Circles
        rim_pen = QPen(cyan_neon, 2.8)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 94.0, 94.0)

        mid_pen = QPen(QColor(0, 180, 255, 110), 1.2)
        painter.setPen(mid_pen)
        painter.drawEllipse(QPointF(cx, cy), 88.0, 88.0)

        # 5. Core Glass Reactor Center
        core_grad = QRadialGradient(cx, cy, 86)
        core_grad.setColorAt(0.0, QColor(8, 28, 52, 245))
        core_grad.setColorAt(0.7, QColor(4, 15, 30, 250))
        core_grad.setColorAt(1.0, QColor(1, 8, 18, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QPointF(cx, cy), 86.0, 86.0)

        # 6. Central Stylized "J" Tech Emblem
        painter.save()
        j_glow_pen = QPen(QColor(0, 242, 254, int(120 + 80 * self._pulse_val)), 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        j_core_pen = QPen(QColor(230, 250, 255), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

        j_path = QPainterPath()
        j_path.moveTo(cx + 8, cy - 36)
        j_path.lineTo(cx + 8, cy + 10)
        j_path.cubicTo(cx + 8, cy + 30, cx - 18, cy + 30, cx - 18, cy + 14)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(j_glow_pen)
        painter.drawPath(j_path)
        painter.setPen(j_core_pen)
        painter.drawPath(j_path)
        painter.restore()

        # 7. "J A R V I S" Lettering Below Core
        font = QFont("Segoe UI", 11, QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4.0)
        painter.setFont(font)
        painter.setPen(QColor(241, 245, 249))
        text_rect = QRectF(cx - 70, cy + 40, 140, 22)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "JARVIS")


# ==========================================
# 2. CPU SPEEDOMETER ARC GAUGE
# ==========================================
class CpuGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 48)
        self._value = 3.2

    def set_value(self, val: float):
        self._value = max(0.0, min(100.0, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(6, 6, 58, 58)
        bg_pen = QPen(QColor(255, 255, 255, 25), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0 * 16, 180 * 16)

        active_span = int((self._value / 100.0) * 180.0)
        arc_pen = QPen(QColor(0, 242, 254), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(rect, 180 * 16, -active_span * 16)

        cx = 35.0
        cy = 35.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 242, 254)))
        painter.drawEllipse(QPointF(cx, cy), 2.2, 2.2)


# ==========================================
# 3. RAM PROGRESS GLOW BAR
# ==========================================
class RamBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self._percent = 38.0

    def set_percent(self, pct: float):
        self._percent = max(0.0, min(100.0, pct))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        r = h / 2.0

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(0, 1, w, h - 2), r, r)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 22)))
        painter.drawPath(bg_path)

        fill_w = max(h, (self._percent / 100.0) * w)
        fill_path = QPainterPath()
        fill_path.addRoundedRect(QRectF(0, 1, fill_w, h - 2), r, r)

        grad = QLinearGradient(0, 0, fill_w, 0)
        grad.setColorAt(0.0, QColor(0, 180, 255))
        grad.setColorAt(1.0, QColor(0, 242, 254))
        painter.setBrush(QBrush(grad))
        painter.drawPath(fill_path)

        head_pen = QPen(QColor(255, 255, 255), 2.0)
        painter.setPen(head_pen)
        painter.drawPoint(QPointF(fill_w - r, r + 0.5))


# ==========================================
# 4. INTERACTIVE PULSE DOTS & PAGINATION
# ==========================================
class PulseDotsWidget(QWidget):
    page_selected = pyqtSignal(int)

    def __init__(self, parent=None, count=5):
        super().__init__(parent)
        self._count = count
        self.setFixedSize(count * 20 + 8, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active_idx = 0
        self._pulse_alpha = 255
        self._pulse_dir = -4

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(40)

    def set_active_page(self, idx: int):
        self._active_idx = max(0, min(self._count - 1, idx))
        self.update()

    def _step(self):
        self._pulse_alpha += self._pulse_dir
        if self._pulse_alpha <= 130:
            self._pulse_dir = 4
        elif self._pulse_alpha >= 255:
            self._pulse_dir = -4
        self.update()

    def mousePressEvent(self, event):
        x = event.position().x()
        spacing = 20.0
        start_x = 10.0
        idx = int(round((x - start_x) / spacing))
        idx = max(0, min(self._count - 1, idx))
        self.set_active_page(idx)
        self.page_selected.emit(idx)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        spacing = 20.0
        start_x = 10.0
        cy = self.height() / 2.0

        for i in range(self._count):
            cx = start_x + i * spacing
            if i == self._active_idx:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 242, 254, int(self._pulse_alpha * 0.25))))
                painter.drawEllipse(QPointF(cx, cy), 7.0, 7.0)

                painter.setBrush(QBrush(QColor(0, 242, 254, self._pulse_alpha)))
                painter.drawEllipse(QPointF(cx, cy), 3.8, 3.8)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
                painter.drawEllipse(QPointF(cx, cy), 2.8, 2.8)


# ==========================================
# 5. CYBER HUD BUTTONS (NAV & ACTIONS)
# ==========================================
class HudNavButton(QPushButton):
    """Top bar Cyber Navigation Tab Button."""
    def __init__(self, text: str, page_idx: int, parent=None):
        super().__init__(text, parent)
        self.page_idx = page_idx
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(28)
        self.set_active(False)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(0, 242, 254, 0.28), stop:1 rgba(0, 180, 216, 0.10));
                    border: 1px solid #00f2fe;
                    border-bottom: 2px solid #00f2fe;
                    border-radius: 6px;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 1.1px;
                    padding: 3px 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(10, 20, 35, 0.5);
                    border: 1px solid rgba(0, 242, 254, 0.18);
                    border-radius: 6px;
                    color: #94a3b8;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.8px;
                    padding: 3px 10px;
                }
                QPushButton:hover {
                    background: rgba(0, 242, 254, 0.14);
                    border-color: rgba(0, 242, 254, 0.5);
                    color: #f1f5f9;
                }
            """)


class HudActionButton(QPushButton):
    """Futuristic Grid Button for Predefined Controls Matrix."""
    def __init__(self, title: str, subtitle: str, icon_str: str, color_hex: str = "#00f2fe", parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: rgba(0, 242, 254, 0.08);
                border: 1px solid {color_hex};
                border-radius: 8px;
                color: {color_hex};
                font-size: 17px;
            }}
        """)
        layout.addWidget(icon_lbl)

        t_layout = QVBoxLayout()
        t_layout.setSpacing(2)
        t_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: 700; border: none; background: transparent;")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 500; border: none; background: transparent;")

        t_layout.addWidget(lbl_title)
        t_layout.addWidget(lbl_sub)
        layout.addLayout(t_layout)
        layout.addStretch()

        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.22);
                border-radius: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: rgba(0, 242, 254, 0.15);
                border: 1px solid {color_hex};
            }}
            QPushButton:pressed {{
                background: rgba(0, 242, 254, 0.32);
            }}
        """)


# ==========================================
# 6. HISTORY ROW WIDGET (CLICKABLE RECALL)
# ==========================================
class HistoryItemWidget(QFrame):
    recalled = pyqtSignal(dict)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.6);
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 8px;
            }
            QFrame:hover {
                background: rgba(0, 242, 254, 0.12);
                border: 1px solid #00f2fe;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        # Source badge
        source = data.get("source", "preset").upper()
        badge_color = "#38bdf8" if source == "VOICE" else ("#a78bfa" if source == "TYPED" else "#10b981")
        badge = QLabel(f"[{source}]")
        badge.setStyleSheet(f"color: {badge_color}; font-size: 9px; font-family: 'Consolas', monospace; font-weight: 700; border: none; background: transparent;")
        layout.addWidget(badge)

        # Title and response
        t_box = QVBoxLayout()
        t_box.setSpacing(1)
        t_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_title = QLabel(data.get("title", "Command"))
        lbl_title.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 700; border: none; background: transparent;")

        resp_text = data.get("response", "Executed successfully.")
        lbl_resp = QLabel(resp_text[:55] + ("..." if len(resp_text) > 55 else ""))
        lbl_resp.setStyleSheet("color: #7dd3fc; font-size: 9px; border: none; background: transparent;")

        t_box.addWidget(lbl_title)
        t_box.addWidget(lbl_resp)
        layout.addLayout(t_box)
        layout.addStretch()

        # Timestamp
        lbl_time = QLabel(data.get("timestamp", ""))
        lbl_time.setStyleSheet("color: #64748b; font-size: 9px; font-family: 'Consolas', monospace; border: none; background: transparent;")
        layout.addWidget(lbl_time)

        # Recall Action Button
        btn_recall = QPushButton("⟳ RECALL")
        btn_recall.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recall.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.12);
                border: 1px solid #00f2fe;
                border-radius: 5px;
                color: #00f2fe;
                font-size: 9px;
                font-weight: 800;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #00f2fe;
                color: #000000;
            }
        """)
        btn_recall.clicked.connect(lambda: self.recalled.emit(self.data))
        layout.addWidget(btn_recall)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.recalled.emit(self.data)
        super().mousePressEvent(event)


# ==========================================
# 7. SCI-FI HUD FRAME & RESIZABLE CONTAINER
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
        cut = 18.0

        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0.0, QColor(4, 9, 18, 255))
        bg_grad.setColorAt(0.5, QColor(6, 14, 26, 255))
        bg_grad.setColorAt(1.0, QColor(2, 6, 13, 255))

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

        border_pen = QPen(QColor(0, 242, 254, 110), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(outer_path)

        bracket_pen = QPen(QColor(0, 242, 254, 230), 2.2)
        painter.setPen(bracket_pen)

        painter.drawLine(QPointF(0, cut + 14), QPointF(0, cut))
        painter.drawLine(QPointF(0, cut), QPointF(cut, 0))
        painter.drawLine(QPointF(cut, 0), QPointF(cut + 24, 0))
        painter.drawLine(QPointF(cut + 32, 2), QPointF(cut + 38, 9))
        painter.drawLine(QPointF(cut + 40, 2), QPointF(cut + 46, 9))

        painter.drawLine(QPointF(w - cut - 24, 0), QPointF(w - cut, 0))
        painter.drawLine(QPointF(w - cut, 0), QPointF(w, cut))
        painter.drawLine(QPointF(w, cut), QPointF(w, cut + 14))

        painter.drawLine(QPointF(0, h - cut - 14), QPointF(0, h - cut))
        painter.drawLine(QPointF(0, h - cut), QPointF(cut, h))
        painter.drawLine(QPointF(cut, h), QPointF(cut + 28, h))

        painter.drawLine(QPointF(w - cut - 28, h), QPointF(w - cut, h))
        painter.drawLine(QPointF(w - cut, h), QPointF(w, h - cut))
        painter.drawLine(QPointF(w, h - cut), QPointF(w, h - cut - 14))

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
# 8. VOICE WORKER THREAD
# ==========================================
class VoiceWorker(QThread):
    update_signal = pyqtSignal(str, bool)
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

    def _on_wake(self):
        from core.voice.wake_word import get_wake_detector
        wake = get_wake_detector()

        if not self.tts or not self.stt:
            logger.warning("Voice engine not ready.")
            return

        if self._is_processing:
            return

        self._is_processing = True
        try:
            wake.pause()
            self.listening_signal.emit(True)
            self.status_signal.emit("LISTENING...")
            # User requirement: Speak "Yes boss?" immediately on hearing wake word
            self.tts.speak("Yes boss?", block=True)
            time.sleep(0.12)

            text = self.stt.listen(timeout=7.0, phrase_time_limit=10.0)
            if not text:
                self.listening_signal.emit(False)
                self.status_signal.emit("STANDBY [ACTIVE]")
                return

            self.status_signal.emit("PROCESSING...")
            self.update_signal.emit(text, True)
            self._execute_pipeline(text)
        finally:
            self._is_processing = False
            self.listening_signal.emit(False)
            wake.resume()

    def _execute_pipeline(self, text: str):
        result = self.nlp.process(text)
        nlp_resp = result.get("response", "")
        if nlp_resp:
            self.tts.speak(nlp_resp, block=True)

        exec_result = self.router.route({
            "intent": result.get("intent"),
            "entities": result.get("entities"),
            "response": nlp_resp
        })

        final_resp = exec_result.response or nlp_resp
        if exec_result.response and exec_result.response != nlp_resp:
            self.tts.speak(exec_result.response, block=True)
        elif not nlp_resp and final_resp:
            self.tts.speak(final_resp, block=True)

        TASK_INTENTS = [
            "open_app", "close_app", "open_folder", "open_file",
            "open_in", "system_control", "file_action", "write_content",
            "send_whatsapp", "youtube_play", "work_mode", "volume_control",
            "clean_temp", "camera", "computer_agent", "custom"
        ]
        intent = result.get("intent", "")
        # User requirement: Say "Done boss." upon completing instructions
        if exec_result.success or intent in TASK_INTENTS or intent != "chat":
            self.tts.speak("Done boss.", block=True)
            if not final_resp:
                final_resp = "Done boss."
            elif "done boss" not in final_resp.lower():
                final_resp = f"{final_resp} Done boss."
        elif not final_resp:
            final_resp = "Done boss."
            self.tts.speak(final_resp, block=True)

        self.update_signal.emit(final_resp, False)
        self.status_signal.emit("STANDBY [ACTIVE]")

    def trigger(self):
        threading.Thread(target=self._on_wake, daemon=True).start()

    def run(self):
        try:
            from core.voice.stt import get_stt
            from core.ai.nlp_engine import get_nlp
            from core.ai.command_router import get_router
            from core.voice.tts import get_tts
            from core.voice.wake_word import get_wake_detector

            self.stt = get_stt()
            self.nlp = get_nlp()
            self.router = get_router()
            self.tts = get_tts()
            self.wake = get_wake_detector(on_detected=self._on_wake)

            self.tts.speak("Jarvis online. All systems nominal.", block=True)
            time.sleep(0.15)
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
# 9. MAIN SCI-FI HUD WINDOW WITH 5 PAGES
# ==========================================
class MainWindow(QMainWindow):
    PAGE_TITLES = [
        "PAGE 1/5: CORE HUD",
        "PAGE 2/5: CONTROLS",
        "PAGE 3/5: HISTORY & RECALL",
        "PAGE 4/5: REMOTE HUB",
        "PAGE 5/5: DIAGNOSTICS"
    ]

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
        self.resize(1020, 640)
        self.setMinimumSize(960, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.drag_pos = None
        self.nav_buttons = []
        self.history_records = []

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'frame'):
            self.frame.setGeometry(0, 0, self.width(), self.height())

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("▢")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")

    def _setup_ui(self):
        self.frame = HudFrame(self)
        self.frame.setGeometry(0, 0, self.width(), self.height())

        main_layout = QVBoxLayout(self.frame)
        main_layout.setContentsMargins(18, 14, 18, 12)
        main_layout.setSpacing(0)

        # ─── 1. TOP TITLE BAR & CYBER NAV TABS ───
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(12, 4, 12, 8)

        # Left Brand Emblem & Title
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)

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

        # Center Top Cyber Navigation Tabs (5 Pages)
        nav_tabs = QHBoxLayout()
        nav_tabs.setSpacing(6)

        tab_specs = [
            ("◈ CORE HUD", 0),
            ("⚡ CONTROLS", 1),
            ("📜 HISTORY", 2),
            ("📡 REMOTE", 3),
            ("⚙ DIAGNOSTICS", 4)
        ]
        for name, idx in tab_specs:
            btn = HudNavButton(name, idx)
            btn.clicked.connect(lambda checked, i=idx: self._set_page(i))
            self.nav_buttons.append(btn)
            nav_tabs.addWidget(btn)

        title_bar.addLayout(nav_tabs)
        title_bar.addStretch()

        # Window Controls (—  ▢  ✕)
        win_ctrls = QHBoxLayout()
        win_ctrls.setSpacing(4)

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

        self.btn_max = QPushButton("▢")
        self.btn_max.setFixedSize(28, 24)
        self.btn_max.setStyleSheet("""
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
        self.btn_max.clicked.connect(self._toggle_maximize)
        win_ctrls.addWidget(self.btn_max)

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

        # ─── GLOBAL LIVE FEEDBACK BANNER (Visible on all pages) ───
        self.feedback_banner = QFrame()
        self.feedback_banner.setFixedHeight(24)
        self.feedback_banner.setStyleSheet("background: transparent; border: none;")
        fb_layout = QHBoxLayout(self.feedback_banner)
        fb_layout.setContentsMargins(14, 0, 14, 0)

        self.global_feedback_lbl = QLabel("SYSTEM IDLE // STANDBY [ACTIVE] // CLICK CONTROLS OR SPEAK 'JARVIS'")
        self.global_feedback_lbl.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; border: none;")
        fb_layout.addWidget(self.global_feedback_lbl)
        main_layout.addWidget(self.feedback_banner)

        # ─── 2. MULTI-PAGE STACK (5 SWAPPABLE PAGES) ───
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_page_core_hud())       # Index 0
        self.stack.addWidget(self._build_page_controls())       # Index 1
        self.stack.addWidget(self._build_page_history())        # Index 2
        self.stack.addWidget(self._build_page_remote())         # Index 3
        self.stack.addWidget(self._build_page_diagnostics())    # Index 4

        main_layout.addWidget(self.stack, stretch=1)

        # ─── 3. BOTTOM DECORATION & INTERACTIVE PAGINATION BAR ───
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(14, 6, 14, 4)
        bottom_bar.setSpacing(12)

        telemetry_block = QLabel("//////  [SYS_V2.4.1] CORE NOMINAL\nSTREAM: 16KHZ MONO SYNCED")
        telemetry_block.setStyleSheet("color: #334155; font-family: 'Consolas', monospace; font-size: 9px; line-height: 1.2;")
        bottom_bar.addWidget(telemetry_block, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 5-Dot Pagination Controls (‹  ● ○ ○ ○ ○  › + Label)
        swapper_box = QHBoxLayout()
        swapper_box.setSpacing(6)

        btn_prev = QPushButton("‹")
        btn_prev.setFixedSize(22, 22)
        btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev.setStyleSheet("""
            QPushButton {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 4px;
                color: #00f2fe;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.25);
                color: #ffffff;
            }
        """)
        btn_prev.clicked.connect(self._prev_page)
        swapper_box.addWidget(btn_prev)

        self.dots = PulseDotsWidget(count=5)
        self.dots.page_selected.connect(self._set_page)
        swapper_box.addWidget(self.dots)

        btn_next = QPushButton("›")
        btn_next.setFixedSize(22, 22)
        btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next.setStyleSheet("""
            QPushButton {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 4px;
                color: #00f2fe;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.25);
                color: #ffffff;
            }
        """)
        btn_next.clicked.connect(self._next_page)
        swapper_box.addWidget(btn_next)

        self.page_indicator_lbl = QLabel("PAGE 1/5: CORE HUD")
        self.page_indicator_lbl.setFixedWidth(160)
        self.page_indicator_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        swapper_box.addWidget(self.page_indicator_lbl)

        bottom_bar.addLayout(swapper_box)
        bottom_bar.addSpacing(6)

        # Center Cyber Command Line Input
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type command (e.g. 'whatsapp', 'volume', 'weather', 'history')...")
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
            }
        """)
        self.cmd_input.returnPressed.connect(self._on_typed_command)
        bottom_bar.addWidget(self.cmd_input, stretch=1)

        # Quick Swap Button & Trigger Mic Button
        btn_swap = QPushButton("⚡ SWAP")
        btn_swap.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_swap.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.08);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 10px;
                padding: 6px 12px;
                color: #38bdf8;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.2);
                color: white;
            }
        """)
        btn_swap.clicked.connect(self._next_page)
        bottom_bar.addWidget(btn_swap)

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
        bottom_bar.addWidget(btn_trigger)

        main_layout.addLayout(bottom_bar)

        # Initialize default history entries
        self._seed_initial_history()
        self._set_page(0)

    # ─── PAGE 0: CORE HUD (ORIGINAL HERO INTERFACE) ───
    def _build_page_core_hud(self) -> QWidget:
        page = QWidget()
        body_layout = QHBoxLayout(page)
        body_layout.setContentsMargins(10, 0, 10, 0)
        body_layout.setSpacing(18)

        # 1. Left HUD Status Card
        self.left_card = self._build_left_hud_card()
        body_layout.addWidget(self.left_card, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 2. Center Hero Arc Reactor
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.reactor = ArcReactorWidget()
        self.reactor.clicked.connect(lambda: self.worker.trigger())
        center_layout.addWidget(self.reactor, alignment=Qt.AlignmentFlag.AlignCenter)

        assistant_lbl = QLabel("AI VOICE ASSISTANT")
        assistant_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 3px;")
        center_layout.addWidget(assistant_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.state_lbl = QLabel("STANDBY [ACTIVE]")
        self.state_lbl.setStyleSheet("color: #00f2fe; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        center_layout.addWidget(self.state_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.center_dots = PulseDotsWidget(count=5)
        self.center_dots.page_selected.connect(self._set_page)
        center_layout.addWidget(self.center_dots, alignment=Qt.AlignmentFlag.AlignCenter)

        body_layout.addWidget(center_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Right Telemetry & Recent Commands Stack
        right_container = QWidget()
        right_container.setFixedWidth(250)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.sys_card = self._build_system_card()
        right_layout.addWidget(self.sys_card)

        self.commands_card = self._build_commands_card()
        right_layout.addWidget(self.commands_card)

        body_layout.addWidget(right_container, alignment=Qt.AlignmentFlag.AlignVCenter)
        return page

    # ─── PAGE 1: PREDEFINED CONTROLS DASHBOARD ───
    def _build_page_controls(self) -> QWidget:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(14)

        # Column 1: Application Quick Launchers
        col_apps = self._create_hud_group("APPLICATIONS (QUICK LAUNCH)", [
            ("VS Code", "Code Editor", "💻", "#38bdf8", lambda: self._exec_action("VS Code", "open_app", {"app": "code"})),
            ("Google Chrome", "Web Browser", "🌐", "#00f2fe", lambda: self._exec_action("Chrome", "open_app", {"app": "chrome"})),
            ("Terminal", "PowerShell CLI", "⚡", "#a78bfa", lambda: self._exec_action("Terminal", "open_app", {"app": "powershell"})),
            ("File Explorer", "Downloads Folder", "📁", "#facc15", lambda: self._exec_action("File Explorer", "open_app", {"app": "downloads folder"})),
            ("Notepad", "Quick Notes", "📝", "#4ade80", lambda: self._exec_action("Notepad", "open_app", {"app": "notepad"})),
            ("WhatsApp", "Messaging Client", "💬", "#22c55e", lambda: self._exec_action("WhatsApp", "open_app", {"app": "whatsapp"}))
        ])
        page_layout.addWidget(col_apps)

        # Column 2: System & Audio Telemetry Controls
        col_sys = self._create_hud_group("SYSTEM & AUDIO CONTROLS", [
            ("Volume +10%", "Boost Master Sound", "🔊", "#00f2fe", lambda: self._exec_action("Volume +10%", "volume_control", {"action": "up"})),
            ("Volume -10%", "Lower Master Sound", "🔉", "#38bdf8", lambda: self._exec_action("Volume -10%", "volume_control", {"action": "down"})),
            ("Mute / Unmute", "Toggle Master Audio", "🔇", "#f87171", lambda: self._exec_action("Toggle Mute", "volume_control", {"action": "toggle"})),
            ("Screenshot", "Capture Display", "📸", "#38bdf8", lambda: self._exec_action("Screenshot", "system_control", {"action": "screenshot"})),
            ("Lock Workstation", "Secure Desktop Screen", "🔒", "#fb923c", lambda: self._exec_action("Lock PC", "system_control", {"action": "lock"})),
            ("Clean Temp Cache", "Free Memory & Disk", "🧹", "#ec4899", lambda: self._exec_action("Clean Temp", "system_control", {"action": "clean_temp"}))
        ])
        page_layout.addWidget(col_sys)

        # Column 3: AI Automations & Macros
        col_macro = self._create_hud_group("AUTOMATION & MACROS", [
            ("Work Mode", "Launch Dev Suite", "🚀", "#00f2fe", lambda: self._exec_action("Work Mode", "work_mode", {})),
            ("Play Lo-Fi Stream", "Autoplay First Result", "🎵", "#a855f7", lambda: self._exec_action("Lo-Fi Stream", "youtube_play", {"query": "lofi hip hop radio"})),
            ("Health Diagnostics", "CPU/RAM/Disk Audit", "🩺", "#34d399", lambda: self._exec_action("Health Diagnostics", "system_control", {"action": "diagnostics"})),
            ("Weather Report", "Local Forecast", "🌤️", "#38bdf8", lambda: self._exec_action("Weather Report", "weather", {})),
            ("Minimize All", "Show Clean Desktop", "🗔", "#94a3b8", lambda: self._exec_action("Minimize Windows", "window_control", {"action": "minimize_all"})),
            ("Voice Check", "Verify TTS Audio", "🎙️", "#00f2fe", lambda: self._test_voice())
        ])
        page_layout.addWidget(col_macro)

        return page

    # ─── PAGE 2: COMMAND HISTORY & ACTION RECALL HUB ───
    def _build_page_history(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(14, 8, 14, 8)
        page_layout.setSpacing(10)

        # Header Row
        h_row = QHBoxLayout()
        pill = QLabel()
        pill.setFixedSize(3, 14)
        pill.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t_lbl = QLabel("COMMAND EXECUTION HISTORY & RECALL (CLICK ANY ENTRY TO RE-RUN)")
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h_row.addWidget(pill)
        h_row.addWidget(t_lbl)
        h_row.addStretch()

        btn_clear_all = QPushButton("🧹 CLEAR HISTORY")
        btn_clear_all.setFixedHeight(26)
        btn_clear_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_all.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 5px;
                color: #f87171;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 10px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.28);
                color: white;
            }
        """)
        btn_clear_all.clicked.connect(self._clear_all_history)
        h_row.addWidget(btn_clear_all)
        page_layout.addLayout(h_row)

        # Scrollable History Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: rgba(10, 25, 45, 0.4);
                border: 1px solid rgba(0, 242, 254, 0.25);
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: rgba(15, 23, 42, 0.5);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #00f2fe;
                border-radius: 3px;
            }
        """)

        self.history_scroll_widget = QWidget()
        self.history_scroll_layout = QVBoxLayout(self.history_scroll_widget)
        self.history_scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.history_scroll_layout.setSpacing(6)
        self.history_scroll_layout.addStretch()

        scroll.setWidget(self.history_scroll_widget)
        page_layout.addWidget(scroll, stretch=1)

        return page

    # ─── PAGE 3: MOBILE REMOTE & NETWORK HUB ───
    def _build_page_remote(self) -> QWidget:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(12, 8, 12, 8)
        page_layout.setSpacing(16)

        # Left Card: Remote Telemetry & Links
        left_card = QFrame()
        left_card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 14px;
            }
        """)
        l_layout = QVBoxLayout(left_card)
        l_layout.setContentsMargins(20, 18, 20, 18)
        l_layout.setSpacing(12)

        h_box = QHBoxLayout()
        pill = QLabel()
        pill.setFixedSize(3, 14)
        pill.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t_lbl = QLabel("MOBILE REMOTE SERVER STATUS")
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h_box.addWidget(pill)
        h_box.addWidget(t_lbl)
        h_box.addStretch()
        l_layout.addLayout(h_box)

        status_box = QLabel("●  REMOTE ENGINE ONLINE [PORT 8443 / 8000]")
        status_box.setStyleSheet("""
            color: #10b981; 
            font-size: 12px; 
            font-weight: 800; 
            letter-spacing: 1.5px;
            padding: 8px 12px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 8px;
        """)
        l_layout.addWidget(status_box)

        l_layout.addSpacing(4)
        lbl_url_hdr = QLabel("LOCAL NETWORK ACCESS (HTTPS REQUIRED FOR MIC):")
        lbl_url_hdr.setStyleSheet("color: #7dd3fc; font-size: 10px; font-weight: 700; border: none; background: transparent;")
        l_layout.addWidget(lbl_url_hdr)

        self.remote_url_val = "https://192.168.0.115:8443"
        url_box = QLabel(self.remote_url_val)
        url_box.setStyleSheet("""
            color: #00f2fe;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            font-weight: 700;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(0, 242, 254, 0.35);
            border-radius: 8px;
        """)
        l_layout.addWidget(url_box)

        lbl_alt = QLabel("Local Loopback: http://localhost:8000")
        lbl_alt.setStyleSheet("color: #64748b; font-size: 11px; font-family: 'Consolas', monospace; border: none; background: transparent;")
        l_layout.addWidget(lbl_alt)

        l_layout.addSpacing(10)

        btn_open = QPushButton("🌐 OPEN MOBILE REMOTE IN BROWSER")
        btn_open.setFixedHeight(42)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.18);
                border: 1px solid #00f2fe;
                border-radius: 8px;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.32);
            }
        """)
        btn_open.clicked.connect(lambda: webbrowser.open(self.remote_url_val))
        l_layout.addWidget(btn_open)

        btn_copy = QPushButton("📋 COPY HTTPS REMOTE LINK")
        btn_copy.setFixedHeight(38)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 8px;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.15);
                color: #ffffff;
            }
        """)
        btn_copy.clicked.connect(self._copy_remote_link)
        l_layout.addWidget(btn_copy)

        l_layout.addStretch()
        page_layout.addWidget(left_card, stretch=1)

        # Right Card: Connection Guide
        right_card = QFrame()
        right_card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 14px;
            }
        """)
        r_layout = QVBoxLayout(right_card)
        r_layout.setContentsMargins(20, 18, 20, 18)
        r_layout.setSpacing(10)

        h_guide = QHBoxLayout()
        pill2 = QLabel()
        pill2.setFixedSize(3, 14)
        pill2.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t_guide = QLabel("MOBILE CONNECTIVITY & MIC SETUP")
        t_guide.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h_guide.addWidget(pill2)
        h_guide.addWidget(t_guide)
        h_guide.addStretch()
        r_layout.addLayout(h_guide)

        guide_steps = [
            "1. Connect Phone to Same Wi-Fi (192.168.0.x network).",
            "2. Open Chrome (Android) or Safari (iOS) on your phone.",
            "3. Navigate to: https://192.168.0.115:8443",
            "4. SSL Bypass: Tap 'Advanced' -> 'Proceed to 192.168.0.115 (unsafe)'.",
            "5. Microphone: Tap 'Allow' when the browser asks for audio permission.",
            "6. Speak 'Jarvis' or tap mic to trigger assistant from anywhere!"
        ]
        for step in guide_steps:
            lbl_step = QLabel(step)
            lbl_step.setStyleSheet("color: #e2e8f0; font-size: 11px; line-height: 1.4; border: none; background: transparent;")
            lbl_step.setWordWrap(True)
            r_layout.addWidget(lbl_step)

        r_layout.addStretch()

        btn_restart_srv = QPushButton("🔄 RESTART REMOTE DAEMON")
        btn_restart_srv.setFixedHeight(38)
        btn_restart_srv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restart_srv.setStyleSheet("""
            QPushButton {
                background: rgba(245, 158, 11, 0.15);
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 8px;
                color: #fbbf24;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(245, 158, 11, 0.28);
                color: #ffffff;
            }
        """)
        btn_restart_srv.clicked.connect(self._restart_mobile_server)
        r_layout.addWidget(btn_restart_srv)

        page_layout.addWidget(right_card, stretch=1)
        return page

    # ─── PAGE 4: SYSTEM DIAGNOSTICS & TELEMETRY ───
    def _build_page_diagnostics(self) -> QWidget:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(12, 8, 12, 8)
        page_layout.setSpacing(16)

        # Left Card: Hardware & OS Audit
        card_hw = QFrame()
        card_hw.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 14px;
            }
        """)
        l_layout = QVBoxLayout(card_hw)
        l_layout.setContentsMargins(20, 18, 20, 18)
        l_layout.setSpacing(12)

        h1 = QHBoxLayout()
        pill1 = QLabel()
        pill1.setFixedSize(3, 14)
        pill1.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t1 = QLabel("HARDWARE & OS TELEMETRY")
        t1.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h1.addWidget(pill1)
        h1.addWidget(t1)
        h1.addStretch()
        l_layout.addLayout(h1)

        cores = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')

        stats = [
            f"CPU Cores: {cores} Logical Processors @ {freq:.0f} MHz",
            f"Physical Memory: {mem.used / (1024**3):.1f} GB Used / {mem.total / (1024**3):.1f} GB Total ({mem.percent}%)",
            f"System Disk (C:): {disk.free / (1024**3):.1f} GB Free / {disk.total / (1024**3):.1f} GB Total",
            "Platform: Windows 11 Pro 64-Bit Architecture",
            "Process Engine: Python 3.14 (Virtual Environment)"
        ]
        for s in stats:
            lbl = QLabel(s)
            lbl.setStyleSheet("color: #e2e8f0; font-size: 11px; border: none; background: transparent;")
            l_layout.addWidget(lbl)

        l_layout.addStretch()
        btn_audit = QPushButton("🩺 RUN FULL SYSTEM HEALTH AUDIT")
        btn_audit.setFixedHeight(38)
        btn_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_audit.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.15);
                border: 1px solid #00f2fe;
                border-radius: 8px;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.3);
            }
        """)
        btn_audit.clicked.connect(lambda: self._exec_action("Health Diagnostics", "system_control", {"action": "diagnostics"}))
        l_layout.addWidget(btn_audit)

        page_layout.addWidget(card_hw, stretch=1)

        # Right Card: AI Voice Pipeline Stack
        card_ai = QFrame()
        card_ai.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 14px;
            }
        """)
        r_layout = QVBoxLayout(card_ai)
        r_layout.setContentsMargins(20, 18, 20, 18)
        r_layout.setSpacing(12)

        h2 = QHBoxLayout()
        pill2 = QLabel()
        pill2.setFixedSize(3, 14)
        pill2.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t2 = QLabel("AI & VOICE PIPELINE CONFIGURATION")
        t2.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h2.addWidget(pill2)
        h2.addWidget(t2)
        h2.addStretch()
        r_layout.addLayout(h2)

        ai_details = [
            "Speech-To-Text (STT): Faster-Whisper Large-v3 & Google Fallback",
            "Natural Language Parser (NLP): Gemini 3.8 Flash & Neural Intent Router",
            "Text-To-Speech (TTS): pyttsx3 Native SAPI5 @ 175 WPM",
            "Wake Word Detector: Vosk Acoustic Model + SpeechRecognition fallback",
            "Execution Engine: Desktop Automation (StartApps, UWP, ShellExecute)"
        ]
        for a in ai_details:
            lbl = QLabel(a)
            lbl.setStyleSheet("color: #e2e8f0; font-size: 11px; border: none; background: transparent;")
            r_layout.addWidget(lbl)

        r_layout.addStretch()
        btn_clear_log = QPushButton("🧹 CLEAR RECENT VOICE LOGS")
        btn_clear_log.setFixedHeight(38)
        btn_clear_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_log.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                color: #f87171;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.28);
                color: #ffffff;
            }
        """)
        btn_clear_log.clicked.connect(self._clear_commands_list)
        r_layout.addWidget(btn_clear_log)

        page_layout.addWidget(card_ai, stretch=1)
        return page

    # ─── HELPER HUD CARDS (CORE HUD) ───
    def _create_hud_group(self, title: str, button_specs: list) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(10, 25, 45, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(6)
        pill = QLabel()
        pill.setFixedSize(3, 14)
        pill.setStyleSheet("background: #00f2fe; border-radius: 1px; border: none;")
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        h_layout.addWidget(pill)
        h_layout.addWidget(t_lbl)
        h_layout.addStretch()
        layout.addLayout(h_layout)

        for b_title, b_sub, b_icon, b_color, b_handler in button_specs:
            btn = HudActionButton(b_title, b_sub, b_icon, b_color)
            btn.clicked.connect(b_handler)
            layout.addWidget(btn)

        layout.addStretch()
        return card

    def _build_left_hud_card(self) -> QFrame:
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

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255, 255, 255, 0.06); border: none;")
        layout.addWidget(div)

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

        t_cmds = QLabel("RECENT VOICE COMMANDS")
        t_cmds.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; border: none; background: transparent;")
        layout.addWidget(t_cmds)

        self.cmds_list_layout = QVBoxLayout()
        self.cmds_list_layout.setContentsMargins(0, 2, 0, 0)
        self.cmds_list_layout.setSpacing(4)

        layout.addLayout(self.cmds_list_layout)
        layout.addStretch()
        return card

    def _add_command_entry(self, text: str, timestamp: str):
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(0, 1, 0, 1)

        clean_text = text[:17] + ("..." if len(text) > 17 else "")
        lbl_text = QLabel(clean_text)
        lbl_text.setStyleSheet("color: #7dd3fc; font-size: 10px; font-weight: 600; border: none; background: transparent;")

        lbl_time = QLabel(timestamp)
        lbl_time.setStyleSheet("color: #64748b; font-size: 9px; font-family: 'Consolas', monospace; border: none; background: transparent;")

        r_layout.addWidget(lbl_text)
        r_layout.addStretch()
        r_layout.addWidget(lbl_time)

        if self.cmds_list_layout.count() >= 3:
            old_item = self.cmds_list_layout.takeAt(self.cmds_list_layout.count() - 1)
            if old_item.widget():
                old_item.widget().deleteLater()

        self.cmds_list_layout.insertWidget(0, row)

    def _seed_initial_history(self):
        now_time = datetime.now().strftime("%H:%M:%S")
        seeds = [
            {"title": "Open WhatsApp", "intent": "open_app", "entities": {"app": "whatsapp"}, "source": "voice", "timestamp": now_time, "response": "Opened WhatsApp client."},
            {"title": "Weather Report", "intent": "weather", "entities": {}, "source": "preset", "timestamp": now_time, "response": "Karachi weather retrieved."},
            {"title": "Play Lo-Fi Stream", "intent": "youtube_play", "entities": {"query": "lofi hip hop radio"}, "source": "preset", "timestamp": now_time, "response": "Autoplaying live Lo-Fi stream."},
            {"title": "Health Diagnostics", "intent": "system_control", "entities": {"action": "diagnostics"}, "source": "voice", "timestamp": now_time, "response": "All core system metrics nominal."},
            {"title": "VS Code", "intent": "open_app", "entities": {"app": "code"}, "source": "preset", "timestamp": now_time, "response": "Visual Studio Code launched."}
        ]
        for s in seeds:
            self._add_history_record(s)
            self._add_command_entry(s["title"], s["timestamp"])

    def _add_history_record(self, data: dict):
        self.history_records.insert(0, data)
        # Add widget to History page scroll area
        item_widget = HistoryItemWidget(data)
        item_widget.recalled.connect(self._recall_action)
        self.history_scroll_layout.insertWidget(0, item_widget)

    def _clear_all_history(self):
        self.history_records.clear()
        while self.history_scroll_layout.count() > 1:
            item = self.history_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._clear_commands_list()
        self.global_feedback_lbl.setText("COMMAND HISTORY PURGED")

    def _clear_commands_list(self):
        while self.cmds_list_layout.count():
            item = self.cmds_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.state_lbl.setText("LOGS CLEARED")

    def _recall_action(self, item_data: dict):
        title = item_data.get("title", "")
        intent = item_data.get("intent", "")
        entities = item_data.get("entities", {})
        self.global_feedback_lbl.setText(f"RECALLING ACTION: [{title.upper()}]...")
        self._exec_action(f"Recall: {title}", intent, entities, source="history")

    # ─── PAGE SWAPPING METHODS ───
    def _set_page(self, idx: int):
        idx = max(0, min(self.stack.count() - 1, idx))
        self.stack.setCurrentIndex(idx)

        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == idx)

        self.dots.set_active_page(idx)
        if hasattr(self, 'center_dots'):
            self.center_dots.set_active_page(idx)

        self.page_indicator_lbl.setText(self.PAGE_TITLES[idx])

    def _next_page(self):
        cur = self.stack.currentIndex()
        self._set_page((cur + 1) % self.stack.count())

    def _prev_page(self):
        cur = self.stack.currentIndex()
        self._set_page((cur - 1) % self.stack.count())

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_1:
            self._set_page(0)
        elif key == Qt.Key.Key_2:
            self._set_page(1)
        elif key == Qt.Key.Key_3:
            self._set_page(2)
        elif key == Qt.Key.Key_4:
            self._set_page(3)
        elif key == Qt.Key.Key_5:
            self._set_page(4)
        elif key in [Qt.Key.Key_Right, Qt.Key.Key_PageDown]:
            self._next_page()
        elif key in [Qt.Key.Key_Left, Qt.Key.Key_PageUp]:
            self._prev_page()
        else:
            super().keyPressEvent(event)

    # ─── TELEMETRY & ACTIONS ───
    def _update_telemetry(self):
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

    def _exec_action(self, title: str, intent: str, entities: dict, source: str = "preset"):
        cur_time = datetime.now().strftime("%H:%M:%S")
        self._add_command_entry(title, cur_time)

        self.reactor.set_processing(True)
        self.state_lbl.setText(f"CMD: [{title.upper()}]")
        self.global_feedback_lbl.setText(f"EXECUTING: [{title.upper()}]...")

        threading.Thread(target=self._run_routed_command, args=(title, intent, entities, source), daemon=True).start()

    def _run_routed_command(self, title: str, intent: str, entities: dict, source: str):
        from core.ai.command_router import get_router
        from core.voice.tts import get_tts

        router = get_router()
        tts = get_tts()

        exec_result = router.route({
            "intent": intent,
            "entities": entities,
            "response": ""
        })

        resp = exec_result.response or f"{title} completed."
        full_speech = f"{resp} Done boss." if "done boss" not in resp.lower() else resp
        tts.speak(full_speech, block=True)

        # Update feedback and history
        cur_time = datetime.now().strftime("%H:%M:%S")
        record = {
            "title": title,
            "intent": intent,
            "entities": entities,
            "source": source,
            "timestamp": cur_time,
            "response": full_speech
        }

        # Safely update GUI elements on Qt thread
        QTimer.singleShot(0, lambda: self._on_action_finished(record))

    def _on_action_finished(self, record: dict):
        self._add_history_record(record)
        resp = record.get("response", "")
        self.global_feedback_lbl.setText(f"DONE: {resp}")
        self.state_lbl.setText("STANDBY [ACTIVE]")
        self.reactor.set_processing(False)

    def _test_voice(self):
        cur_time = datetime.now().strftime("%H:%M:%S")
        self._add_command_entry("Voice Check", cur_time)
        self.global_feedback_lbl.setText("TESTING VOICE ENGINE...")
        self.reactor.set_processing(True)

        def _voice_run():
            from core.voice.tts import get_tts
            tts = get_tts()
            msg = "Jarvis voice and speech synthesis verified. All systems nominal and fully operational."
            tts.speak(msg, block=True)
            record = {
                "title": "Voice Check",
                "intent": "chat",
                "entities": {},
                "source": "preset",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "response": msg
            }
            QTimer.singleShot(0, lambda: self._on_action_finished(record))

        threading.Thread(target=_voice_run, daemon=True).start()

    def _copy_remote_link(self):
        QApplication.clipboard().setText(self.remote_url_val)
        self.global_feedback_lbl.setText("COPIED HTTPS REMOTE URL TO CLIPBOARD")

    def _restart_mobile_server(self):
        import subprocess, sys
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_script = os.path.join(root_dir, "server.py")
        DETACHED = 0x00000008 | 0x08000000
        subprocess.Popen([sys.executable, server_script], cwd=root_dir, creationflags=DETACHED)
        self.global_feedback_lbl.setText("MOBILE REMOTE DAEMON RESTARTED")

    def _on_command_update(self, text: str, is_user: bool):
        clean_lower = text.lower().strip()
        if is_user:
            if any(kw in clean_lower for kw in ["controls", "control page", "show controls", "open controls"]):
                self._set_page(1)
                return
            elif any(kw in clean_lower for kw in ["history", "history page", "show history", "recent commands"]):
                self._set_page(2)
                return
            elif any(kw in clean_lower for kw in ["remote page", "show remote", "open remote", "mobile remote"]):
                self._set_page(3)
                return
            elif any(kw in clean_lower for kw in ["diagnostics", "system page", "show settings"]):
                self._set_page(4)
                return
            elif any(kw in clean_lower for kw in ["core hud", "show hud", "open hud", "main page"]):
                self._set_page(0)
                return
            elif any(kw in clean_lower for kw in ["next page", "swap page"]):
                self._next_page()
                return
            elif any(kw in clean_lower for kw in ["previous page", "back page"]):
                self._prev_page()
                return

            cur_time = datetime.now().strftime("%H:%M:%S")
            self._add_command_entry(text, cur_time)
            self.state_lbl.setText(f"CMD: \"{text[:18]}\"")
            self.global_feedback_lbl.setText(f"VOICE INSTRUCTION: \"{text}\"")
        else:
            self.global_feedback_lbl.setText(f"JARVIS: {text}")
            self.state_lbl.setText("STANDBY [ACTIVE]")

    def _on_listening_state(self, is_listening: bool):
        self.reactor.set_listening(is_listening)
        if is_listening:
            self.state_lbl.setText("LISTENING...")
            self.state_lbl.setStyleSheet("color: #00f2fe; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.status_tag.setText("[LISTENING]")
            self.status_tag.setStyleSheet("color: #00f2fe; font-weight: 800; font-size: 13px;")
            self.global_feedback_lbl.setText("MICROPHONE ACTIVE // LISTENING FOR VOICE INSTRUCTION...")
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

        clean = text.lower()
        if clean in ["1", "hud", "core", "main"]:
            self._set_page(0)
            return
        elif clean in ["2", "controls", "ctrl", "predefined"]:
            self._set_page(1)
            return
        elif clean in ["3", "history", "log", "logs", "recent"]:
            self._set_page(2)
            return
        elif clean in ["4", "remote", "mobile", "network"]:
            self._set_page(3)
            return
        elif clean in ["5", "diag", "diagnostics", "settings"]:
            self._set_page(4)
            return
        elif clean in ["next", "swap"]:
            self._next_page()
            return
        elif clean in ["prev", "back"]:
            self._prev_page()
            return

        cur_time = datetime.now().strftime("%H:%M:%S")
        self._add_command_entry(text, cur_time)
        self.reactor.set_processing(True)
        self.state_lbl.setText("PROCESSING...")
        self.global_feedback_lbl.setText(f"PROCESSING: \"{text}\"")

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

        final_resp = exec_result.response or nlp_resp or "Instruction completed."
        if exec_result.response and exec_result.response != nlp_resp:
            tts.speak(exec_result.response, block=True)
        elif not nlp_resp and final_resp:
            tts.speak(final_resp, block=True)

        if exec_result.success or result.get("intent") != "chat":
            tts.speak("Done boss.", block=True)
            if "done boss" not in final_resp.lower():
                final_resp = f"{final_resp} Done boss."

        record = {
            "title": text,
            "intent": result.get("intent", "chat"),
            "entities": result.get("entities", {}),
            "source": "typed",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "response": final_resp
        }
        QTimer.singleShot(0, lambda: self._on_action_finished(record))

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