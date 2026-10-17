"""
System Control Skill — launch/close applications, volume, brightness,
screenshots, power management, Antigravity IDE, and 'work mode' routine.
"""
import os
import subprocess
import webbrowser
import psutil
from core.utils.logger import get_logger

logger = get_logger("skills.system")

def get_chrome_path():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def get_antigravity_path():
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\antigravity.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\antigravity\antigravity.exe"),
        os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity-ide\bin\antigravity.cmd")
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

APP_MAP = {
    "whatsapp": "start whatsapp:",
    "edge": "start msedge",
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

        # 1. Antigravity IDE
        if "antigravity" in app_clean:
            ag = get_antigravity_path()
            if ag:
                subprocess.Popen([ag])
                return True
            os.system("start antigravity")
            return True

        # 2. Chrome
        if "chrome" in app_clean or "google chrome" in app_clean:
            cp = get_chrome_path()
            if cp:
                subprocess.Popen([cp])
                return True
            os.system("start chrome")
            return True

        # 3. YouTube (opens directly in Chrome or browser)
        if "youtube" in app_clean:
            cp = get_chrome_path()
            url = "https://www.youtube.com"
            if cp:
                subprocess.Popen([cp, url])
                return True
            webbrowser.open(url)
            return True

        # 4. WhatsApp
        if "whatsapp" in app_clean:
            os.system("start whatsapp:")
            return True

        # 5. Check known map
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

        # Fallback
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

        try:
            subprocess.run(f"taskkill /F /IM {app_clean}*.exe", shell=True, capture_output=True)
            return True
        except Exception:
            return False

    def take_screenshot(self) -> str:
        """Captures Windows desktop screenshot and saves to data/screenshot.png."""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "screenshot.png")

        # Method 1: PIL ImageGrab
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(path)
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_screenshot.png")
                img.save(desktop_path)
            except Exception:
                pass
            logger.info(f"Screenshot successfully saved to: {path}")
            return path
        except Exception as e:
            logger.warning(f"PIL ImageGrab error ({e}), trying PowerShell capture...")

        # Method 2: PowerShell Drawing Capture
        try:
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $b = New-Object System.Drawing.Bitmap $s.Width, $s.Height
            $g = [System.Drawing.Graphics]::FromImage($b)
            $g.CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size)
            $b.Save('{path}', [System.Drawing.Imaging.ImageFormat]::Png)
            $g.Dispose()
            $b.Dispose()
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                try:
                    import shutil
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_screenshot.png")
                    shutil.copyfile(path, desktop_path)
                except Exception:
                    pass
                logger.info(f"PowerShell screenshot saved to: {path}")
                return path
        except Exception as pe:
            logger.warning(f"PowerShell capture error: {pe}")

        return ""

    def work_mode(self) -> bool:
        """Launches work setup: Antigravity IDE, Google Chrome, Terminal, and VS Code."""
        logger.info("Initiating Work Mode routine...")
        success = False

        # 1. Launch Antigravity IDE
        ag = get_antigravity_path()
        if ag:
            subprocess.Popen([ag])
            success = True
        else:
            os.system("start antigravity")
            success = True

        # 2. Launch Google Chrome with developer resources
        cp = get_chrome_path()
        if cp:
            subprocess.Popen([cp, "https://github.com"])
            success = True
        else:
            webbrowser.open("https://github.com")
            success = True

        # 3. Launch Terminal & VS Code
        try:
            subprocess.Popen("cmd.exe /c start powershell", shell=True)
            subprocess.Popen("cmd.exe /c code", shell=True)
            success = True
        except Exception:
            pass

        return success

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
