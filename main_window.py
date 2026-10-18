"""
Root export alias for JARVIS Sci-Fi Arc Reactor HUD MainWindow.
"""
from gui.main_window import (
    MainWindow, ArcReactorWidget, CpuGaugeWidget, RamBarWidget, 
    PulseDotsWidget, HudFrame, VoiceWorker, HudNavButton, HudActionButton,
    HistoryItemWidget
)

__all__ = [
    "MainWindow", "ArcReactorWidget", "CpuGaugeWidget", "RamBarWidget", 
    "PulseDotsWidget", "HudFrame", "VoiceWorker", "HudNavButton", "HudActionButton",
    "HistoryItemWidget"
]