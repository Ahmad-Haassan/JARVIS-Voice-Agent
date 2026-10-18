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
        r"C:\Users\Ahmad\Desktop\Antigravity IDE\Antigravity IDE.exe",
        os.path.expandvars(r"%USERPROFILE%\Desktop\Antigravity IDE\Antigravity IDE.exe"),
        os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\Antigravity IDE\Antigravity IDE.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\antigravity.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\antigravity\antigravity.exe"),
        os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity-ide\bin\antigravity.cmd")
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def shell_execute(target: str, args: str = "") -> bool:
    """Launches an application or URL directly on the user's interactive Windows desktop using Windows Shell."""
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        import win32com.client
        shell = win32com.client.Dispatch("Shell.Application")
        shell.ShellExecute(target, args, "", "open", 1)
        logger.info(f"ShellExecute invoked: target='{target}', args='{args}'")
        return True
    except Exception as e:
        logger.warning(f"Shell.Application error ({e}), falling back to cmd start...")
        try:
            if args:
                os.system(f'start "" "{target}" "{args}"')
            else:
                os.system(f'start "" "{target}"')
            return True
        except Exception as se:
            logger.error(f"Fallback start error: {se}")
            return False

APP_MAP = {
    "whatsapp": "whatsapp:",
    "edge": "msedge",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "terminal": "powershell.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "spotify": "spotify",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
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
                return shell_execute(ag)
            return shell_execute("antigravity")

        # 2. Chrome
        if "chrome" in app_clean or "google chrome" in app_clean:
            cp = get_chrome_path()
            if cp:
                return shell_execute(cp, "https://www.google.com")
            return shell_execute("chrome.exe", "https://www.google.com")

        # 3. YouTube (opens directly in Chrome or default browser)
        if "youtube" in app_clean:
            cp = get_chrome_path()
            if cp:
                return shell_execute(cp, "https://www.youtube.com")
            return shell_execute("https://www.youtube.com")

        # 4. WhatsApp
        if "whatsapp" in app_clean:
            return shell_execute("whatsapp:")

        # 5. Check known map
        for name, cmd in APP_MAP.items():
            if name in app_clean or app_clean in name:
                return shell_execute(cmd)

        # Fallback
        return shell_execute(app_clean)

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
        """Captures the real active user desktop screenshot by attaching to WinSta0\\default."""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "screenshot.png")

        # Ensure thread is attached to the user's interactive desktop WinSta0\default
        h_desk = None
        try:
            import ctypes
            user32 = ctypes.windll.user32
            h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
            if h_desk:
                user32.SetThreadDesktop(h_desk)
        except Exception as de:
            logger.warning(f"Could not attach to desktop default: {de}")

        # Method 1: PIL ImageGrab (high-res capture on active desktop)
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            if img and img.size[0] > 100:
                img.save(path)
                try:
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_screenshot.png")
                    img.save(desktop_path)
                except Exception:
                    pass
                logger.info(f"Screenshot successfully saved to: {path} ({img.size})")
                if h_desk:
                    try:
                        ctypes.windll.user32.CloseDesktop(h_desk)
                    except Exception:
                        pass
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
                if h_desk:
                    try:
                        ctypes.windll.user32.CloseDesktop(h_desk)
                    except Exception:
                        pass
                return path
        except Exception as pe:
            logger.warning(f"PowerShell capture error: {pe}")

        if h_desk:
            try:
                ctypes.windll.user32.CloseDesktop(h_desk)
            except Exception:
                pass
        return ""

    def work_mode(self) -> bool:
        """Launches work setup: Antigravity IDE, Google Chrome, Terminal, and VS Code on user desktop."""
        logger.info("Initiating Work Mode routine via Shell.Application...")
        ag = get_antigravity_path()
        cp = get_chrome_path()

        # 1. Launch Antigravity IDE
        if ag:
            shell_execute(ag)
        else:
            shell_execute("antigravity")

        # 2. Launch Google Chrome with developer resources
        if cp:
            shell_execute(cp, "https://github.com")
        else:
            shell_execute("https://github.com")

        # 3. Launch Terminal & VS Code
        shell_execute("powershell.exe")
        shell_execute("code")

        return True

    def get_system_diagnostics(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            bat_str = f", Battery: {battery.percent}%" if battery else ""
            return f"CPU Usage: {cpu}%, RAM Usage: {ram}%{bat_str}."
        except Exception as e:
            return f"System info unavailable: {e}"

    def unlock_pc(self, pin: str = "") -> bool:
        """Wakes the display, dismisses the lock screen curtain, and enters PIN if provided."""
        logger.info("Attempting to unlock/wake PC...")
        try:
            import ctypes
            import time
            from core.utils import config as cfg
            user32 = ctypes.windll.user32

            # Wake up display
            user32.mouse_event(0x0001, 1, 1, 0, 0)
            user32.mouse_event(0x0001, -1, -1, 0, 0)
            time.sleep(0.3)

            # Dismiss lock screen curtain (Space key)
            VK_SPACE = 0x20
            VK_RETURN = 0x0D
            user32.keybd_event(VK_SPACE, 0, 0, 0)
            user32.keybd_event(VK_SPACE, 0, 2, 0)
            time.sleep(0.6)

            # If PIN is specified in config or passed in
            if not pin:
                pin = cfg.get("auth", "windows_pin", "")

            if pin:
                for c in str(pin):
                    vk = ord(c.upper())
                    user32.keybd_event(vk, 0, 0, 0)
                    user32.keybd_event(vk, 0, 2, 0)
                    time.sleep(0.04)
                time.sleep(0.2)
                user32.keybd_event(VK_RETURN, 0, 0, 0)
                user32.keybd_event(VK_RETURN, 0, 2, 0)

            return True
        except Exception as e:
            logger.error(f"Unlock error: {e}")
            return False

    def system_power(self, action: str, pin: str = "") -> bool:
        action = action.lower()
        if "unlock" in action:
            return self.unlock_pc(pin)
        elif "lock" in action:
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
