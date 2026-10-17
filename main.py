"""
Main entry point for the Jarvis Desktop Assistant.
Handles application initialization, authentication flow, and main window launch.
"""
import sys
import os

# Suppress HuggingFace symlink warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.auth.auth_manager import get_auth_manager
from gui.auth_screen import AuthScreen
from gui.main_window import MainWindow
from core.utils.logger import get_logger

logger = get_logger("main")

class JarvisApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Jarvis Assistant")
        self.auth_manager = get_auth_manager()
        self.main_window = None
        self.auth_screen = None

    def start(self):
        logger.info("Starting Jarvis Assistant...")
        self.show_auth()
        sys.exit(self.app.exec())

    def show_auth(self):
        self.auth_screen = AuthScreen(self.auth_manager)
        self.auth_screen.login_success.connect(self.launch_main)
        self.auth_screen.setup_complete.connect(self.launch_main)
        
        # Make auth screen look nice and center on screen
        self.auth_screen.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.auth_screen.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        screen = self.app.primaryScreen().geometry()
        x = (screen.width() - self.auth_screen.width()) // 2
        y = (screen.height() - self.auth_screen.height()) // 2
        self.auth_screen.move(x, y)
        self.auth_screen.show()
        self.auth_screen.raise_()
        self.auth_screen.activateWindow()

    def launch_main(self):
        logger.info("Authentication successful. Launching main window...")
        if self.auth_screen:
            self.auth_screen.close()
        
        self.main_window = MainWindow(self.auth_manager)
        screen = self.app.primaryScreen().geometry()
        x = (screen.width() - self.main_window.width()) // 2
        y = (screen.height() - self.main_window.height()) // 2
        self.main_window.move(x, y)
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/voice_prints", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/wa_session", exist_ok=True)

    jarvis = JarvisApp()
    jarvis.start()
