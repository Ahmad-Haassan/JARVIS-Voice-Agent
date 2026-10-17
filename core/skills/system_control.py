"""
System Control Skill — launch/close applications, volume, brightness,
screenshots, power management, and 'work mode' routine.
"""
import os
import subprocess
import webbrowser
import psutil
from core.utils.logger import get_logger

logger = get_logger("skills.system")

APP_MAP = {
    "whatsapp": "start whatsapp:",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "terminal": "powershell",
    "cmd": "cmd",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "spotify": "spotify",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "settings": "start ms-settings:",
}

class SystemControl:
    def open_app(self, app_name: str) -> bool:
        app_clean = (app_name or "").lower().strip()
        logger.info(f"Opening app: '{app_clean}'")

        if not app_clean:
            return False

        # Specific handler for YouTube
        if "youtube" in app_clean:
            webbrowser.open("https://www.youtube.com")
            return True

        # Check known shortcuts
        for name, cmd in APP_MAP.items():
            if name in app_clean or app_clean in name:
                try:
                    if cmd.startswith("start "):
                        os.system(cmd)
                    else:
                        subprocess.Popen(cmd, shell=True)
                    return True
                except Exception as e:
                    logger.warning(f"Error launching {name} with command {cmd}: {e}")

        # Fallback: try direct launch via Windows shell
        try:
            os.system(f'start "" "{app_clean}"')
            return True
        except Exception as e:
            logger.error(f"Failed to open '{app_clean}': {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        app_clean = (app_name or "").lower().strip()
        logger.info(f"Closing app: '{app_clean}'")
        killed = False
        try:
            for proc in psutil.process_iter(['name']):
                pname = (proc.info['name'] or '').lower()
                if app_clean in pname:
                    proc.kill()
                    killed = True
            if killed:
                return True
        except Exception as e:
            logger.warning(f"psutil process termination error: {e}")

        # Fallback to taskkill
        try:
            subprocess.run(f"taskkill /F /IM {app_clean}*.exe", shell=True, capture_output=True)
            return True
        except Exception:
            return False

    def take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            import datetime
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(desktop, filename)
            img = ImageGrab.grab()
            img.save(path)
            logger.info(f"Screenshot saved to: {path}")
            return path
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return ""

    def work_mode(self) -> bool:
        """Launches work setup: VS Code, Terminal, and Chrome."""
        logger.info("Initiating Work Mode routine...")
        try:
            subprocess.Popen("code", shell=True)
            subprocess.Popen("powershell", shell=True)
            webbrowser.open("https://github.com")
            return True
        except Exception as e:
            logger.error(f"Work mode launch error: {e}")
            return False

    def get_system_diagnostics(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            bat_str = f", Battery: {battery.percent}%" if battery else ""
            return f"CPU Usage: {cpu}%, RAM Usage: {ram}%{bat_str}."
        except Exception as e:
            return f"System info unavailable: {e}"

    def system_power(self, action: str) -> bool:
        action = action.lower()
        if "lock" in action:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return True
        elif "sleep" in action:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return True
        elif "restart" in action:
            os.system("shutdown /r /t 5")
            return True
        elif "shutdown" in action:
            os.system("shutdown /s /t 5")
            return True
        return False

_sys_instance = None

def get_system_control() -> SystemControl:
    global _sys_instance
    if _sys_instance is None:
        _sys_instance = SystemControl()
    return _sys_instance
