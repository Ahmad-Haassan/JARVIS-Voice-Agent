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

def get_antigravity_cli_path():
    candidates = [
        r"C:\Users\Ahmad\Desktop\Antigravity IDE\bin\antigravity-ide.cmd",
        os.path.expandvars(r"%USERPROFILE%\Desktop\Antigravity IDE\bin\antigravity-ide.cmd"),
        os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\Antigravity IDE\bin\antigravity-ide.cmd"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\bin\antigravity-ide.cmd"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\bin\antigravity-ide.cmd"),
        os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity-ide\bin\antigravity.cmd"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    import shutil
    return shutil.which("antigravity-ide") or shutil.which("agy")

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

import threading
import json
import difflib

class AppCatalog:
    _instance = None

    def __init__(self):
        self._apps = []
        self._loaded = False
        self._load_lock = threading.Lock()
        self._start_async_load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AppCatalog()
        return cls._instance

    def _start_async_load(self):
        t = threading.Thread(target=self._load_installed_apps, daemon=True)
        t.start()

    def _load_installed_apps(self):
        with self._load_lock:
            try:
                cmd = ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", "Get-StartApps | ConvertTo-Json"]
                proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=12)
                if proc.returncode == 0 and proc.stdout.strip():
                    data = json.loads(proc.stdout)
                    if isinstance(data, list):
                        self._apps = data
                    elif isinstance(data, dict):
                        self._apps = [data]
                    logger.info(f"Loaded {len(self._apps)} Windows StartApps into catalog.")
            except Exception as e:
                logger.warning(f"Failed to load StartApps: {e}")
            self._loaded = True

    def find_and_launch(self, app_name: str) -> bool:
        if not self._loaded:
            self._load_installed_apps()

        clean = (app_name or "").lower().strip()
        for prefix in ["app ", "the ", "program ", "application ", "software ", "my "]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()

        # 1. Direct protocol URI mappings (UWP & Built-in Windows features)
        PROTOCOL_MAP = {
            "clock": "ms-clock:",
            "alarm": "ms-clock:",
            "alarms": "ms-clock:",
            "timer": "ms-clock:",
            "stopwatch": "ms-clock:",
            "microsoft store": "ms-windows-store:",
            "store": "ms-windows-store:",
            "app store": "ms-windows-store:",
            "settings": "ms-settings:",
            "system settings": "ms-settings:",
            "pc settings": "ms-settings:",
            "camera": "microsoft.windows.camera:",
            "webcam": "microsoft.windows.camera:",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "photos": "ms-photos:",
            "photo viewer": "ms-photos:",
            "weather": "bingweather:",
            "maps": "bingmaps:",
            "feedback": "feedback-hub:",
            "snipping tool": "snippingtool.exe",
            "snip": "snippingtool.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "control panel": "control.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "terminal": "powershell.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "whatsapp": "whatsapp:",
            "spotify": "spotify:"
        }
        if clean in PROTOCOL_MAP:
            target = PROTOCOL_MAP[clean]
            if target.startswith("ms-") or target.startswith("microsoft.") or target.startswith("bing"):
                try:
                    os.startfile(target)
                    return True
                except Exception:
                    subprocess.Popen(["explorer.exe", target])
                    return True
            return shell_execute(target)

        # 2. Check installed desktop & UWP apps via Get-StartApps catalog
        match = self._match_start_app(clean)
        if match:
            appid = match.get("AppID", "")
            if appid:
                logger.info(f"AppCatalog launching match: '{match.get('Name')}' ({appid})")
                if appid.endswith(".exe") and os.path.exists(appid):
                    try:
                        os.startfile(appid)
                        return True
                    except Exception:
                        subprocess.Popen([appid])
                        return True
                else:
                    try:
                        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{appid}"])
                        return True
                    except Exception as e:
                        logger.error(f"Failed to launch shell:AppsFolder\\{appid}: {e}")

        # 3. Web Services & AI assistants
        WEB_APPS = {
            "gemini": "https://gemini.google.com",
            "chatgpt": "https://chatgpt.com",
            "claude": "https://claude.ai",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "gmail": "https://mail.google.com",
            "google": "https://www.google.com",
            "reddit": "https://reddit.com",
            "netflix": "https://netflix.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "linkedin": "https://linkedin.com",
            "canva": "https://canva.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "deepseek": "https://chat.deepseek.com"
        }
        if clean in WEB_APPS:
            url = WEB_APPS[clean]
            cp = get_chrome_path()
            if cp:
                return shell_execute(cp, url)
            return shell_execute(url)

        return False

    def _match_start_app(self, clean: str):
        for a in self._apps:
            if a.get("Name", "").lower() == clean:
                return a
        for a in self._apps:
            name = a.get("Name", "").lower()
            if clean in name or name in clean:
                return a
        names = [a.get("Name", "") for a in self._apps]
        matches = difflib.get_close_matches(clean, names, n=1, cutoff=0.7)
        if matches:
            for a in self._apps:
                if a.get("Name") == matches[0]:
                    return a
        return None

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
        if app_clean in ["chrome", "google chrome", "browser"]:
            cp = get_chrome_path()
            if cp:
                return shell_execute(cp, "https://www.google.com")
            return shell_execute("chrome.exe", "https://www.google.com")

        # 3. Universal AppCatalog (matches any installed PC app, UWP app, or web service)
        if AppCatalog.get_instance().find_and_launch(app_clean):
            return True

        # 4. Check known map
        for name, cmd in APP_MAP.items():
            if name in app_clean or app_clean in name:
                return shell_execute(cmd)

        # 5. Check if target is a folder or directory
        try:
            from core.skills.file_manager import get_file_manager
            fm = get_file_manager()
            f_ok, _, _ = fm.open_folder(app_clean)
            if f_ok:
                return True
        except Exception as fe:
            logger.debug(f"Folder check skipped: {fe}")

        # 6. Fallback shell execute or URL
        res = shell_execute(app_clean)
        if not res:
            if "." in app_clean and " " not in app_clean:
                target_url = app_clean if app_clean.startswith("http") else f"https://{app_clean}"
                return shell_execute(target_url)
        return res

    def open_with_app(self, app_name: str, target_path: str) -> bool:
        """Launches an application and passes a specific file or folder path as its workspace/target."""
        app_clean = (app_name or "").lower().strip()
        logger.info(f"Opening target '{target_path}' with application '{app_clean}'")

        # 1. Antigravity IDE (Always use -n to open a separate, new window and preserve other workspaces)
        if "antigravity" in app_clean:
            cli = get_antigravity_cli_path()
            ag = get_antigravity_path()
            exe = cli or ag
            if exe:
                if target_path:
                    try:
                        if not os.path.exists(target_path) and "." not in os.path.basename(target_path):
                            os.makedirs(target_path, exist_ok=True)
                        if os.path.exists(target_path):
                            subprocess.Popen([exe, "-n", target_path], shell=True if exe.endswith(('.cmd', '.bat')) else False)
                            return True
                    except Exception as e:
                        logger.warning(f"Popen antigravity error: {e}")
                return shell_execute(exe, f'-n "{target_path}"' if target_path else "-n")
            return shell_execute("antigravity", f'-n "{target_path}"' if target_path else "-n")

        # 2. VS Code (Always use -n to open a separate, new window)
        if app_clean in ["code", "vscode", "vs code", "visual studio code"]:
            try:
                subprocess.Popen(f'code -n "{target_path}"', shell=True)
                return True
            except Exception:
                return shell_execute("code", f'-n "{target_path}"')

        # 3. Notepad
        if "notepad" in app_clean:
            try:
                subprocess.Popen(["notepad.exe", target_path])
                return True
            except Exception:
                return shell_execute("notepad.exe", f'"{target_path}"')

        # 4. Chrome
        if "chrome" in app_clean or "browser" in app_clean:
            cp = get_chrome_path() or "chrome.exe"
            try:
                subprocess.Popen([cp, target_path])
                return True
            except Exception:
                return shell_execute(cp, f'"{target_path}"')

        # 5. Explorer
        if "explorer" in app_clean:
            try:
                subprocess.Popen(["explorer.exe", target_path])
                return True
            except Exception:
                pass

        # 6. Generic shell execute with arguments
        return shell_execute(app_clean, f'"{target_path}"')

    def focus_window_by_name(self, name: str) -> bool:
        """Brings the matching window to the foreground."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            found_hwnd = [None]
            target_name = name.lower().strip()

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def enum_cb(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if target_name in buff.value.lower():
                            found_hwnd[0] = hwnd
                            return False
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            if found_hwnd[0]:
                hwnd = found_hwnd[0]
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
                return True
        except Exception as e:
            logger.debug(f"focus_window_by_name error: {e}")
        return False

    def open_with_app_and_prompt(self, app_name: str, target_path: str, prompt: str) -> bool:
        """
        Opens a target workspace/file in a separate, brand new window (-n) and autonomously
        injects and submits the user's prompt directly into the AI chat.
        Guarantees that existing workspaces and open files are NEVER closed or modified.
        """
        import time
        import threading
        import pyperclip
        import pyautogui
        import ctypes
        import ctypes.wintypes

        pyautogui.FAILSAFE = False
        app_clean = (app_name or "").lower().strip()
        logger.info(f"Opening '{target_path}' in '{app_clean}' (NEW WINDOW) with prompt: '{prompt}'")

        # 1. Launch the application in a separate, NEW window (-n)
        ok = self.open_with_app(app_clean, target_path) if target_path else self.open_app(app_clean)
        if not ok:
            return False

        if not prompt:
            return True

        # Determine target window title keyword (e.g. folder name 'testing' or 'dsa', or app name)
        window_keyword = ""
        if target_path:
            window_keyword = os.path.basename(target_path.rstrip(r'\/'))
        if not window_keyword:
            window_keyword = "Antigravity" if "antigravity" in app_clean else app_clean

        # 2. Copy prompt to system clipboard
        try:
            pyperclip.copy(prompt)
        except Exception as e:
            logger.warning(f"pyperclip error: {e}")

        # 3. Direct Win32 Injector in background thread
        def _dispatch_prompt():
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
            if h_desk:
                user32.SetThreadDesktop(h_desk)

            logger.info(f"Waiting for new window matching keyword: '{window_keyword}'...")
            target_hwnd = None
            target_title = ""

            # Poll for up to 12 seconds for the new window to be created and visible
            for attempt in range(24):
                time.sleep(0.5)
                found = []

                def cb(hwnd, _):
                    if user32.IsWindowVisible(hwnd):
                        l = user32.GetWindowTextLengthW(hwnd)
                        if l > 0:
                            buf = ctypes.create_unicode_buffer(l + 1)
                            user32.GetWindowTextW(hwnd, buf, l + 1)
                            title = buf.value
                            # Match target keyword specifically so other windows are NEVER touched
                            if window_keyword and window_keyword.lower() in title.lower():
                                found.append((hwnd, title))
                    return True

                W = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
                user32.EnumWindows(W(cb), 0)

                if found:
                    target_hwnd, target_title = found[0]
                    logger.info(f"Found target window [{target_hwnd}]: '{target_title}' after {attempt * 0.5:.1f}s")
                    break

            if not target_hwnd:
                logger.warning(f"Target window for '{window_keyword}' not found within timeout.")
                return

            # Bring target window to front and bypass Windows 11 foreground lock
            try:
                fg_hwnd = user32.GetForegroundWindow()
                fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
                cur_tid = kernel32.GetCurrentThreadId()

                if fg_tid != cur_tid:
                    user32.AttachThreadInput(cur_tid, fg_tid, True)

                # Tap Alt key to allow foreground switch
                user32.keybd_event(0x12, 0, 0, 0)
                user32.keybd_event(0x12, 0, 2, 0)

                user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
                user32.BringWindowToTop(target_hwnd)
                user32.SetForegroundWindow(target_hwnd)

                if fg_tid != cur_tid:
                    user32.AttachThreadInput(cur_tid, fg_tid, False)
            except Exception as e:
                logger.warning(f"Foreground attach error: {e}")

            time.sleep(0.6)

            # Click center of the target window to activate and trigger "Code with Agent"
            try:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
                cx = (rect.left + rect.right) // 2
                cy = (rect.top + rect.bottom) // 2
                pyautogui.click(cx, cy + 20)
                logger.info(f"Activated target window at ({cx}, {cy+20})")
            except Exception as e:
                logger.warning(f"Click window error: {e}")

            time.sleep(0.8)

            # Ensure AI chat / Agent panel is open and focused
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.6)

            # Paste prompt from clipboard
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.4)

            # Submit prompt to Agent
            pyautogui.press('enter')
            logger.info(f"Successfully injected prompt into '{target_title}': '{prompt}'")

        threading.Thread(target=_dispatch_prompt, daemon=True).start()
        return True

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
        """Captures the real active user desktop screenshot by attaching a dedicated thread to WinSta0\\default."""
        import threading
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "screenshot.png")

        captured = [False]

        def _worker():
            h_desk = None
            try:
                import ctypes
                user32 = ctypes.windll.user32
                h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
                if h_desk:
                    user32.SetThreadDesktop(h_desk)

                from PIL import ImageGrab
                img = ImageGrab.grab()
                if img and img.size[0] > 100:
                    img.save(path)
                    try:
                        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_screenshot.png")
                        img.save(desktop_path)
                    except Exception:
                        pass
                    captured[0] = True
            except Exception as e:
                logger.warning(f"PIL thread grab error: {e}")
            finally:
                if h_desk:
                    try:
                        ctypes.windll.user32.CloseDesktop(h_desk)
                    except Exception:
                        pass

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=3.0)

        if captured[0] and os.path.exists(path):
            logger.info(f"Screenshot successfully saved to: {path}")
            return path

        # Fallback: PowerShell Drawing Capture
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
                logger.info(f"PowerShell screenshot saved to: {path}")
                return path
        except Exception as pe:
            logger.warning(f"PowerShell capture error: {pe}")

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

    # ==========================================
    # VOLUME & AUDIO CONTROL (pycaw)
    # ==========================================
    def get_volume(self) -> int:
        try:
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            return int(round(speakers.volume_percent))
        except Exception as e:
            logger.warning(f"Error getting volume: {e}")
            return 50

    def set_volume(self, level: int) -> int:
        try:
            level = max(0, min(100, int(level)))
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            speakers.volume_percent = float(level)
            logger.info(f"Master volume set to {level}%")
            return level
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return self.get_volume()

    def change_volume(self, delta: int) -> int:
        cur = self.get_volume()
        target = max(0, min(100, cur + delta))
        return self.set_volume(target)

    def set_mute(self, mute: bool = True) -> bool:
        try:
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            speakers.EndpointVolume.SetMute(1 if mute else 0, None)
            logger.info(f"Master mute set to {mute}")
            return True
        except Exception as e:
            logger.error(f"Error toggling mute: {e}")
            return False

    def toggle_mute(self) -> bool:
        try:
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            current = speakers.EndpointVolume.GetMute()
            speakers.EndpointVolume.SetMute(0 if current else 1, None)
            return not current
        except Exception as e:
            logger.error(f"Error toggling mute: {e}")
            return False

    # ==========================================
    # MEDIA PLAYBACK CONTROLS
    # ==========================================
    def media_play_pause(self) -> bool:
        try:
            import ctypes
            VK_MEDIA_PLAY_PAUSE = 0xB3
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            return True
        except Exception as e:
            logger.error(f"Media play/pause error: {e}")
            return False

    def media_next(self) -> bool:
        try:
            import ctypes
            VK_MEDIA_NEXT_TRACK = 0xB0
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            return True
        except Exception as e:
            logger.error(f"Media next error: {e}")
            return False

    def media_prev(self) -> bool:
        try:
            import ctypes
            VK_MEDIA_PREV_TRACK = 0xB1
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
        except Exception as e:
            logger.error(f"Media prev error: {e}")
            return False

    # ==========================================
    # WINDOWS & DESKTOP MANAGEMENT
    # ==========================================
    def get_open_windows(self) -> list:
        """Returns list of all visible application window titles on user's interactive desktop."""
        import ctypes
        import threading
        titles = []

        def _worker():
            user32 = ctypes.windll.user32
            h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
            if not h_desk:
                return
            user32.SetThreadDesktop(h_desk)

            def cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        val = buff.value.replace("\u200b", "").strip()
                        val = val.encode("ascii", "ignore").decode("ascii")
                        if val and val not in ["Program Manager", "Windows Input Experience"]:
                            titles.append(val)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(WNDENUMPROC(cb), 0)
            user32.CloseDesktop(h_desk)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=2.0)
        return titles

    def focus_window(self, app_name: str) -> bool:
        """Brings the window matching app_name to the foreground."""
        import ctypes
        import threading
        found = [False]

        def _worker():
            user32 = ctypes.windll.user32
            h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
            if not h_desk:
                return
            user32.SetThreadDesktop(h_desk)

            matched_hwnd = [None]
            clean_name = app_name.lower().strip()

            def cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if clean_name in buff.value.lower():
                            matched_hwnd[0] = hwnd
                            return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(WNDENUMPROC(cb), 0)

            if matched_hwnd[0]:
                user32.ShowWindow(matched_hwnd[0], 9)  # SW_RESTORE
                user32.SetForegroundWindow(matched_hwnd[0])
                found[0] = True
            user32.CloseDesktop(h_desk)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=2.0)
        return found[0]

    def minimize_all(self) -> bool:
        """Minimizes all windows to show the desktop (Win + D)."""
        try:
            import ctypes
            VK_LWIN = 0x5B
            VK_D = 0x44
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_D, 0, 0, 0)
            user32.keybd_event(VK_D, 0, 2, 0)
            user32.keybd_event(VK_LWIN, 0, 2, 0)
            return True
        except Exception as e:
            logger.error(f"Minimize all error: {e}")
            return False

_sys_instance = None

def get_system_control() -> SystemControl:
    global _sys_instance
    if _sys_instance is None:
        _sys_instance = SystemControl()
    return _sys_instance
