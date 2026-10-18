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
from core.utils import config as cfg

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
        self.ensure_mobile_server()
        require_login = cfg.get("auth", "require_login", False)
        if require_login and not self.auth_manager.is_authenticated():
            self.show_auth()
        else:
            self.launch_main()
        sys.exit(self.app.exec())

    def ensure_mobile_server(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            res = s.connect_ex(('127.0.0.1', 8000))
            s.close()
            if res != 0:
                import subprocess
                root_dir = os.path.dirname(os.path.abspath(__file__))
                server_script = os.path.join(root_dir, "server.py")
                DETACHED = 0x00000008 | 0x08000000
                subprocess.Popen([sys.executable, server_script], cwd=root_dir, creationflags=DETACHED)
                logger.info("Auto-launched background Mobile Remote server on port 8000.")
            else:
                logger.info("Mobile Remote server already active on port 8000.")
        except Exception as e:
            logger.warning(f"Failed to check/start mobile server: {e}")

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
