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
import re
import glob

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

class AppCatalog:
    _instance = None

    def __init__(self):
        self._apps = []  # List of dicts: {"name": str, "clean": str, "type": str, "target": str}
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
            collected = []
            seen_names = set()

            # 1. Standard Built-in Windows Utilities & Aliases
            BUILTINS = [
                ("Snipping Tool", ["snipping tool", "snip tool", "snip", "screenshot tool"], "exe", "snippingtool.exe"),
                ("Calculator", ["calculator", "calc"], "exe", "calc.exe"),
                ("Notepad", ["notepad", "notes", "text editor"], "exe", "notepad.exe"),
                ("Paint", ["paint", "mspaint"], "exe", "mspaint.exe"),
                ("Task Manager", ["task manager", "taskmgr", "task"], "exe", "taskmgr.exe"),
                ("Command Prompt", ["cmd", "command prompt"], "exe", "cmd.exe"),
                ("PowerShell", ["powershell", "terminal"], "exe", "powershell.exe"),
                ("Control Panel", ["control panel", "control"], "exe", "control.exe"),
                ("File Explorer", ["file explorer", "explorer", "files"], "exe", "explorer.exe"),
                ("Device Manager", ["device manager"], "exe", "devmgmt.msc"),
                ("WordPad", ["wordpad"], "exe", "write.exe"),
                ("Registry Editor", ["regedit", "registry editor"], "exe", "regedit.exe"),
                ("Windows Settings", ["settings", "system settings", "pc settings"], "protocol", "ms-settings:"),
                ("Camera", ["camera", "webcam"], "protocol", "microsoft.windows.camera:"),
                ("Microsoft Store", ["store", "microsoft store", "app store"], "protocol", "ms-windows-store:"),
                ("Clock", ["clock", "alarm", "alarms", "timer", "stopwatch"], "protocol", "ms-clock:"),
            ]
            for disp_name, aliases, kind, tgt in BUILTINS:
                item = {"name": disp_name, "aliases": aliases, "type": kind, "target": tgt}
                collected.append(item)

            # 2. Modern Apps & UWP via PowerShell Get-StartApps
            try:
                cmd = ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", "Get-StartApps | ConvertTo-Json"]
                proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=8)
                if proc.returncode == 0 and proc.stdout.strip():
                    raw = json.loads(proc.stdout)
                    items = raw if isinstance(raw, list) else [raw]
                    for it in items:
                        name = it.get("Name", "").strip()
                        appid = it.get("AppID", "").strip()
                        if name and appid:
                            clean_n = name.lower()
                            if clean_n not in seen_names:
                                seen_names.add(clean_n)
                                if appid.endswith(".exe") and os.path.exists(appid):
                                    collected.append({"name": name, "aliases": [clean_n], "type": "exe", "target": appid})
                                else:
                                    collected.append({"name": name, "aliases": [clean_n], "type": "appid", "target": appid})
            except Exception as e:
                logger.warning(f"Get-StartApps load warning: {e}")

            # 3. Recursive Start Menu Shortcuts (.lnk files across all users)
            start_dirs = [
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
            ]
            for sdir in start_dirs:
                if os.path.exists(sdir):
                    for root, _, files in os.walk(sdir):
                        for f in files:
                            if f.lower().endswith(".lnk"):
                                name = f[:-4].strip()
                                clean_n = name.lower()
                                if clean_n not in seen_names:
                                    seen_names.add(clean_n)
                                    collected.append({
                                        "name": name,
                                        "aliases": [clean_n],
                                        "type": "lnk",
                                        "target": os.path.join(root, f)
                                    })

            self._apps = collected
            logger.info(f"AppCatalog dynamically indexed {len(self._apps)} applications across Windows.")
            self._loaded = True

    def find_and_launch(self, app_name: str) -> bool:
        if not self._loaded or not self._apps:
            self._load_installed_apps()

        clean = (app_name or "").lower().strip()
        for prefix in ["open ", "launch ", "start ", "run ", "the ", "app ", "application ", "program ", "software ", "my "]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()

        if not clean:
            return False

        # 1. Check Web Services & Sites
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
            "deepseek": "https://chat.deepseek.com",
        }
        if clean in WEB_APPS:
            import webbrowser
            try:
                os.startfile(WEB_APPS[clean])
            except Exception:
                webbrowser.open(WEB_APPS[clean])
            return True

        # 2. Smart Fuzzy Match in AppCatalog
        match = self._fuzzy_search(clean)
        if match:
            return self._launch_app_entry(match)

        # 3. Universal Fallback: Let Windows Shell find and run it
        try:
            logger.info(f"Fallback launch for '{clean}' via Windows cmd start...")
            subprocess.Popen(["cmd.exe", "/c", "start", "", clean],
                             creationflags=0x08000000,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True
        except Exception as fe:
            logger.error(f"Fallback launch failed: {fe}")
            return False

    def _fuzzy_search(self, query: str):
        if not self._loaded or not self._apps:
            self._load_installed_apps()
        q = query.lower().strip()
        q_words = [w for w in re.findall(r'\w+', q) if w not in ["tool", "app", "the", "program"]]
        if not q_words:
            q_words = re.findall(r'\w+', q)

        # Exact match
        for app in self._apps:
            if app["name"].lower() == q or any(a == q for a in app.get("aliases", [])):
                return app

        # Word tokens subset match (e.g. 'snip tool' -> matches 'Snipping Tool')
        best_token_matches = []
        for app in self._apps:
            n_lower = app["name"].lower()
            all_aliases = " ".join([n_lower] + app.get("aliases", []))
            if all(w in all_aliases for w in q_words):
                best_token_matches.append(app)

        if best_token_matches:
            best_token_matches.sort(key=lambda a: len(a["name"]))
            return best_token_matches[0]

        # Fuzzy Scoring via RapidFuzz / Difflib
        scored = []
        for app in self._apps:
            n_lower = app["name"].lower()
            if HAS_RAPIDFUZZ:
                s1 = fuzz.token_set_ratio(q, n_lower)
                s2 = fuzz.partial_ratio(q, n_lower)
                score = max(s1, s2)
            else:
                score = difflib.SequenceMatcher(None, q, n_lower).ratio() * 100
            scored.append((score, app))

        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] >= 55:
            logger.info(f"Fuzzy match resolved: '{query}' -> '{scored[0][1]['name']}' (score: {scored[0][0]:.1f})")
            return scored[0][1]

        return None

    def _launch_app_entry(self, entry: dict) -> bool:
        kind = entry.get("type")
        target = entry.get("target")
        name = entry.get("name")
        logger.info(f"Launching app '{name}' (type={kind}, target={target})")

        try:
            if kind == "lnk":
                os.startfile(target)
                return True
            elif kind == "appid":
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{target}"],
                                 creationflags=0x08000000,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            elif kind == "exe":
                if os.path.isabs(target) and os.path.exists(target):
                    try:
                        os.startfile(target)
                        return True
                    except Exception:
                        pass
                subprocess.Popen(["cmd.exe", "/c", "start", "", target],
                                 creationflags=0x08000000,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            elif kind == "protocol":
                try:
                    os.startfile(target)
                    return True
                except Exception:
                    subprocess.Popen(["explorer.exe", target],
                                     creationflags=0x08000000,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    return True
        except Exception as e:
            logger.error(f"Error launching {name}: {e}")
            try:
                subprocess.Popen(["cmd.exe", "/c", "start", "", target], creationflags=0x08000000)
                return True
            except Exception:
                return False

class SystemControl:
    def open_app(self, app_name: str) -> bool:
        app_clean = (app_name or "").lower().strip()
        logger.info(f"Opening app request: '{app_clean}'")

        if not app_clean:
            return False

        # 1. Antigravity IDE
        if "antigravity" in app_clean:
            ag = get_antigravity_path()
            if ag:
                try:
                    os.startfile(ag)
                    return True
                except Exception:
                    pass
            try:
                subprocess.Popen(["cmd.exe", "/c", "start", "", "antigravity"], creationflags=0x08000000)
                return True
            except Exception:
                pass

        # 2. Chrome & Browsers (Works on ANY machine)
        if app_clean in ["chrome", "google chrome", "browser"]:
            # If Chrome is already open, immediately restore and focus it
            if self.focus_window("Google Chrome") or self.focus_window("Chrome"):
                logger.info("Focused existing Google Chrome window.")
                return True
            chrome_candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ]
            for cp in chrome_candidates:
                if os.path.exists(cp):
                    try:
                        os.startfile(cp)
                        return True
                    except Exception:
                        pass
            try:
                subprocess.Popen(["cmd.exe", "/c", "start", "chrome", "https://www.google.com"],
                                 creationflags=0x08000000,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass
            import webbrowser
            webbrowser.open("https://www.google.com")
            return True

        # 3. Universal AppCatalog (100% of installed Windows apps, UWP, and shortcuts)
        if AppCatalog.get_instance().find_and_launch(app_clean):
            return True

        # 4. Check if target is a folder or directory
        try:
            from core.skills.file_manager import get_file_manager
            fm = get_file_manager()
            f_ok, _, _ = fm.open_folder(app_clean)
            if f_ok:
                return True
        except Exception as fe:
            logger.debug(f"Folder check skipped: {fe}")

        # 5. Fallback shell execute or URL
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

        # 3. Direct Injector in background thread
        def _dispatch_prompt():
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Switch thread to active interactive desktop WinSta0\Default
            try:
                h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
                if h_desk:
                    user32.SetThreadDesktop(h_desk)
            except Exception:
                pass

            logger.info(f"Waiting for target window matching '{window_keyword}' to open...")
            target_hwnd = None
            target_title = ""

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            # Poll for up to 14 seconds for the software window to finish spawning and rendering
            for attempt in range(28):
                time.sleep(0.5)
                found = []

                def cb(hwnd, _):
                    if user32.IsWindowVisible(hwnd):
                        l = user32.GetWindowTextLengthW(hwnd)
                        if l > 0:
                            buf = ctypes.create_unicode_buffer(l + 1)
                            user32.GetWindowTextW(hwnd, buf, l + 1)
                            title = buf.value
                            # Match target folder keyword in window title (ignoring File Explorer)
                            if window_keyword and window_keyword.lower() in title.lower():
                                if "explorer" not in title.lower():
                                    found.append((hwnd, title))
                    return True

                try:
                    user32.EnumWindows(WNDENUMPROC(cb), 0)
                except Exception:
                    pass

                if found:
                    target_hwnd, target_title = found[0]
                    logger.info(f"Found target window [{target_hwnd}]: '{target_title}' after {attempt * 0.5:.1f}s")
                    break

            # Bring target window to front and bypass Windows 11 foreground lock
            if target_hwnd:
                try:
                    fg_hwnd = user32.GetForegroundWindow()
                    fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
                    cur_tid = kernel32.GetCurrentThreadId()

                    if fg_tid != cur_tid:
                        user32.AttachThreadInput(cur_tid, fg_tid, True)

                    user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
                    user32.BringWindowToTop(target_hwnd)
                    user32.SetForegroundWindow(target_hwnd)

                    if fg_tid != cur_tid:
                        user32.AttachThreadInput(cur_tid, fg_tid, False)
                except Exception as e:
                    logger.warning(f"Foreground attach error: {e}")
            else:
                # Fallback: activate by title via WScript.Shell
                try:
                    import win32com.client
                    ws = win32com.client.Dispatch("WScript.Shell")
                    if window_keyword:
                        ws.AppActivate(window_keyword)
                    elif app_clean:
                        ws.AppActivate(app_clean)
                except Exception:
                    pass

            # Dismiss any active menu bar or overlay (e.g. if Alt or menu was pressed)
            try:
                user32.keybd_event(0x1B, 0, 0, 0)  # VK_ESCAPE down
                user32.keybd_event(0x1B, 0, 2, 0)  # VK_ESCAPE up
            except Exception:
                pass

            # Wait for the window to settle in the foreground
            time.sleep(0.8)

            # Focus the input area (prompt box)
            if target_hwnd:
                try:
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    is_antigravity = "antigravity" in (target_title or app_clean).lower()
                    if is_antigravity:
                        # In Antigravity IDE, click the prompt box in the right pane (center: 60% x, 46% y)
                        cx = rect.left + int(w * 0.60)
                        cy = rect.top + int(h * 0.46)
                    else:
                        cx = rect.left + int(w * 0.50)
                        cy = rect.top + int(h * 0.50)

                    user32.SetCursorPos(cx, cy)
                    time.sleep(0.05)
                    user32.mouse_event(2, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
                    time.sleep(0.05)
                    user32.mouse_event(4, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
                    time.sleep(0.05)
                    pyautogui.click(cx, cy)
                except Exception as ex:
                    logger.warning(f"Focus click error: {ex}")

            time.sleep(0.3)

            # Ensure clipboard holds the prompt
            try:
                pyperclip.copy(prompt)
            except Exception as e:
                logger.warning(f"Clipboard copy error: {e}")

            time.sleep(0.2)

            # Directly paste prompt (Ctrl + V) without any extra steps
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.4)

            # Submit prompt (Enter)
            pyautogui.press('enter')
            logger.info(f"Direct prompt pasted and submitted to '{target_title or app_clean}': '{prompt}'")

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

    def clean_temp(self) -> tuple[bool, str]:
        """Purges temporary files from %TEMP% and empties Windows Recycle Bin."""
        cleaned_files = 0
        freed_bytes = 0
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~/AppData/Local/Temp"))
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        cleaned_files += 1
                        freed_bytes += sz
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
        # Empty Recycle Bin without dialogs
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        except Exception:
            pass

        mb_freed = freed_bytes / (1024 * 1024)
        msg = f"System cache purged. Cleaned {cleaned_files} temporary files, freeing {mb_freed:.1f} MB disk space."
        logger.info(msg)
        return True, msg

    def get_system_diagnostics(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            cores = psutil.cpu_count(logical=True)
            avail_gb = mem.available / (1024 ** 3)
            free_disk_gb = disk.free / (1024 ** 3)
            return (
                f"System Diagnostics: CPU load is {cpu:.1f}% across {cores} logical processors. "
                f"RAM usage is {mem.percent}% with {avail_gb:.1f} GB memory available. "
                f"Primary drive C has {free_disk_gb:.1f} GB free. All core services nominal."
            )
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
    # VOLUME & AUDIO CONTROLS
    # ==========================================
    def _ensure_com(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            try:
                import comtypes
                comtypes.CoInitialize()
            except Exception:
                pass

    def get_volume(self) -> int:
        self._ensure_com()
        try:
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            return int(round(speakers.volume_percent))
        except Exception as e:
            logger.warning(f"Error getting volume: {e}")
            return 50

    def set_volume(self, level: int) -> int:
        self._ensure_com()
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
        self._ensure_com()
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
        self._ensure_com()
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
        """Minimizes all windows to show/toggle the desktop."""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            shell.ToggleDesktop()
            logger.info("Desktop toggled via Shell.Application COM.")
            return True
        except Exception as e:
            logger.warning(f"COM ToggleDesktop warning: {e}, falling back to keybd_event")
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
            except Exception as e2:
                logger.error(f"Minimize all error: {e2}")
                return False

    def execute_powershell(self, script: str) -> tuple:
        """Executes an arbitrary PowerShell script safely and returns (success, output)."""
        try:
            cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12.0)
            out = res.stdout.strip()
            err = res.stderr.strip()
            if res.returncode == 0:
                return True, out or "Command executed successfully."
            return False, err or out or f"Command failed with exit code {res.returncode}"
        except Exception as e:
            return False, str(e)

_sys_instance = None

def get_system_control() -> SystemControl:
    global _sys_instance
    if _sys_instance is None:
        _sys_instance = SystemControl()
    return _sys_instance
