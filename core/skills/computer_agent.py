"""
Autonomous Computer-Use Agent — controls mouse cursor, keyboard,
window management, and multi-step desktop workflows (Stonic AI style).
"""
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

import ctypes
import pyautogui
from core.utils.logger import get_logger
from core.skills.system_control import shell_execute, get_chrome_path

logger = get_logger("skills.computer_agent")

# Configure PyAutoGUI with minimal pause for fluid remote response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.001
_thread_local = threading.local()

class ComputerAgent:
    def __init__(self):
        self._action_logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.screen_width, self.screen_height = pyautogui.size()
        self._is_busy = False
        self._log_action("SYSTEM", f"Computer Agent initialized (Display: {self.screen_width}x{self.screen_height})")

    def _log_action(self, category: str, message: str):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "category": category,
            "message": message
        }
        with self._lock:
            self._action_logs.append(entry)
            if len(self._action_logs) > 60:
                self._action_logs.pop(0)
        logger.info(f"[{category}] {message}")

    def get_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._action_logs[-limit:])

    def is_busy(self) -> bool:
        return self._is_busy

    # ==========================================
    # MOUSE CONTROL (HIGH-PERFORMANCE WIN32 API)
    # ==========================================
    def _attach_desktop(self):
        """Attaches current thread to interactive desktop session WinSta0\\Default without handle leaks."""
        if getattr(_thread_local, "desktop_attached", False):
            return
        try:
            user32 = ctypes.windll.user32
            h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
            if h_desk:
                user32.SetThreadDesktop(h_desk)
                user32.CloseDesktop(h_desk)
            _thread_local.desktop_attached = True
        except Exception:
            pass

    def move_to(self, x: int, y: int, duration: float = 0.0) -> bool:
        try:
            self._attach_desktop()
            tx = max(0, min(self.screen_width - 1, int(x)))
            ty = max(0, min(self.screen_height - 1, int(y)))
            ctypes.windll.user32.SetCursorPos(tx, ty)
            return True
        except Exception as e:
            logger.error(f"move_to failed: {e}")
            return False

    def get_cursor_pos(self):
        """Returns (x, y, pct_x, pct_y) coordinates of current mouse cursor."""
        try:
            self._attach_desktop()
            user32 = ctypes.windll.user32
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            pct_x = round((pt.x / max(1, self.screen_width)) * 100.0, 2)
            pct_y = round((pt.y / max(1, self.screen_height)) * 100.0, 2)
            return pt.x, pt.y, pct_x, pct_y
        except Exception:
            return 0, 0, 50.0, 50.0

    def move_rel(self, dx: int, dy: int):
        """Zero-latency hardware cursor movement via Win32 SetCursorPos."""
        try:
            self._attach_desktop()
            user32 = ctypes.windll.user32

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            nx = max(0, min(self.screen_width - 1, pt.x + int(dx)))
            ny = max(0, min(self.screen_height - 1, pt.y + int(dy)))
            user32.SetCursorPos(nx, ny)
            pct_x = round((nx / max(1, self.screen_width)) * 100.0, 2)
            pct_y = round((ny / max(1, self.screen_height)) * 100.0, 2)
            return pct_x, pct_y
        except Exception as e:
            logger.error(f"move_rel failed: {e}")
            return None

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> bool:
        """High-speed native mouse clicks with desktop session attachment."""
        try:
            self._attach_desktop()
            user32 = ctypes.windll.user32

            if x is not None and y is not None:
                user32.SetCursorPos(int(x), int(y))

            btn = (button or "left").lower().strip()
            if btn in ("right", "secondary"):
                for i in range(clicks):
                    user32.mouse_event(0x0008, 0, 0, 0, 0)  # RIGHTDOWN
                    user32.mouse_event(0x0010, 0, 0, 0, 0)  # RIGHTUP
                    if clicks > 1 and i < clicks - 1:
                        time.sleep(0.04)
            elif btn == "middle":
                for i in range(clicks):
                    user32.mouse_event(0x0020, 0, 0, 0, 0)  # MIDDLEDOWN
                    user32.mouse_event(0x0040, 0, 0, 0, 0)  # MIDDLEUP
                    if clicks > 1 and i < clicks - 1:
                        time.sleep(0.04)
            else:  # left or double
                total = 2 if btn == "double" else clicks
                for i in range(total):
                    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
                    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
                    if total > 1 and i < total - 1:
                        time.sleep(0.04)
            return True
        except Exception as e:
            logger.error(f"click failed: {e}")
            return False

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x=x, y=y, button="right", clicks=1)

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x=x, y=y, button="left", clicks=2)

    def scroll(self, amount: int) -> bool:
        """Native Win32 mouse wheel scroll."""
        try:
            self._attach_desktop()
            # 0x0800 = MOUSEEVENTF_WHEEL
            ctypes.windll.user32.mouse_event(0x0800, 0, 0, int(amount), 0)
            return True
        except Exception as e:
            logger.error(f"scroll failed: {e}")
            return False

    # ==========================================
    # KEYBOARD CONTROL
    # ==========================================
    def type_text(self, text: str, interval: float = 0.025) -> bool:
        """Types text into active window."""
        try:
            self._attach_desktop()
            self._log_action("KEYBOARD", f"Typing text: '{text[:35]}...'")
            import pyperclip
            pyperclip.copy(text)
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)  # V down
            ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)  # V up
            ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            return True
        except Exception:
            try:
                pyautogui.write(text, interval=interval)
                return True
            except Exception as e:
                logger.error(f"type_text failed: {e}")
                return False
        except Exception as e:
            logger.error(f"type_text failed: {e}")
            return False

    def press_key(self, key_name: str) -> bool:
        try:
            k = key_name.lower().strip()
            pyautogui.press(k)
            self._log_action("KEYBOARD", f"Pressed key '{k}'")
            return True
        except Exception as e:
            logger.error(f"press_key failed: {e}")
            return False

    def hotkey(self, *keys: str) -> bool:
        try:
            cleaned = [k.lower().strip() for k in keys]
            pyautogui.hotkey(*cleaned)
            self._log_action("KEYBOARD", f"Executed hotkey: {' + '.join(cleaned)}")
            return True
        except Exception as e:
            logger.error(f"hotkey failed: {e}")
            return False

    # ==========================================
    # AUTONOMOUS AGENT WORKFLOWS (STONIC AI STYLE)
    # ==========================================
    def workflow_start_menu_launch(self, app_name: str) -> bool:
        """
        Launches an app by opening the Windows Start Menu, typing the app name,
        and pressing Enter — mimicking the Stonic AI autonomous demonstration.
        """
        self._is_busy = True
        try:
            self._log_action("AGENT", f"Initiating autonomous launch of '{app_name}' via Start Menu...")
            # 1. Smoothly move mouse toward bottom-left or center-bottom (Windows Start)
            start_x = int(self.screen_width * 0.5) if self.screen_width > 1200 else 30
            start_y = self.screen_height - 25
            self.move_to(start_x, start_y, duration=0.4)
            time.sleep(0.1)

            # 2. Trigger Windows Search
            self.hotkey("win")
            time.sleep(0.5)

            # 3. Type app name smoothly
            self.type_text(app_name, interval=0.04)
            time.sleep(0.6)

            # 4. Press Enter to launch
            self.press_key("enter")
            self._log_action("AGENT", f"App '{app_name}' launched successfully!")
            return True
        finally:
            self._is_busy = False

    def workflow_search_google(self, query: str) -> bool:
        """Opens Google Chrome, focuses address bar, types query, and hits Enter."""
        self._is_busy = True
        try:
            self._log_action("AGENT", f"Autonomous Google Search: '{query}'")
            chrome_path = get_chrome_path()
            if chrome_path:
                shell_execute(chrome_path, "about:blank")
            else:
                shell_execute("https://www.google.com")
            time.sleep(1.2)

            # Focus address bar (Ctrl + L)
            self.hotkey("ctrl", "l")
            time.sleep(0.2)

            # Type search query & submit
            self.type_text(f"https://www.google.com/search?q={query.replace(' ', '+')}", interval=0.01)
            time.sleep(0.2)
            self.press_key("enter")
            self._log_action("AGENT", f"Search results displayed for '{query}'")
            return True
        finally:
            self._is_busy = False

    def workflow_search_youtube(self, query: str) -> bool:
        """Opens YouTube, searches for the specified topic, and submits."""
        self._is_busy = True
        try:
            self._log_action("AGENT", f"Autonomous YouTube Search: '{query}'")
            yt_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            chrome_path = get_chrome_path()
            if chrome_path:
                shell_execute(chrome_path, yt_url)
            else:
                shell_execute(yt_url)
            time.sleep(1.5)

            # Move mouse into viewport smoothly
            self.move_to(int(self.screen_width * 0.5), int(self.screen_height * 0.4), duration=0.5)
            self._log_action("AGENT", f"YouTube loaded with query '{query}'")
            return True
        finally:
            self._is_busy = False

    def workflow_ask_ai(self, prompt: str) -> bool:
        """Opens ChatGPT or web AI, smooth-navigates and writes the prompt."""
        self._is_busy = True
        try:
            self._log_action("AGENT", f"Autonomous AI Assistant Prompt: '{prompt[:40]}...'")
            chatgpt_url = "https://chatgpt.com"
            chrome_path = get_chrome_path()
            if chrome_path:
                shell_execute(chrome_path, chatgpt_url)
            else:
                shell_execute(chatgpt_url)
            time.sleep(2.0)

            # Focus input area (center bottom of viewport)
            prompt_x = int(self.screen_width * 0.5)
            prompt_y = int(self.screen_height * 0.88)
            self.move_to(prompt_x, prompt_y, duration=0.4)
            self.click()
            time.sleep(0.3)

            # Instant, reliable clipboard paste for full prompt and multi-line content
            try:
                import pyperclip
                pyperclip.copy(prompt)
                time.sleep(0.1)
                self.hotkey("ctrl", "v")
            except Exception:
                self.type_text(prompt, interval=0.01)

            time.sleep(0.4)
            self.press_key("enter")
            self._log_action("AGENT", "AI Prompt submitted successfully!")
            return True
        finally:
            self._is_busy = False

    def workflow_send_document_to_chatgpt(self, folder_query: str, doc_query: str, user_prompt: str = "") -> tuple:
        """
        Locates a document in the given folder, extracts its content/summary,
        opens ChatGPT in Google Chrome, pastes the prompt and document content,
        and submits the query autonomously.
        """
        from core.skills.file_manager import get_file_manager
        fm = get_file_manager()
        doc_path, doc_name = fm.find_document_in_folder(folder_query, doc_query)
        if not doc_path:
            return False, f"Could not find document '{doc_query}' inside '{folder_query}' folder."

        content = fm.read_document_text(doc_path, max_chars=2800)
        instruction = user_prompt.strip() or "Please analyze this document and explain all details."

        full_prompt = (
            f"{instruction}\n\n"
            f"[Attached Document: {doc_name}]\n{content}"
        ) if content else f"{instruction}\n[Document: {doc_name} at {doc_path}]"

        success = self.workflow_ask_ai(full_prompt)
        if success:
            return True, f"Found '{doc_name}' in '{folder_query}', opened ChatGPT, and dispatched your request."
        return False, f"Located '{doc_name}', but encountered an issue submitting to ChatGPT."

    def workflow_quick_notepad(self, content: str, title: str = "JARVIS Autonomous Memo") -> bool:
        """Opens Notepad and autonomously writes a memo/note with typewriter animation."""
        self._is_busy = True
        try:
            self._log_action("AGENT", f"Autonomous Note generation: '{title}'")
            shell_execute("notepad.exe")
            time.sleep(0.8)

            header = f"=== {title} ===\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nAgent: JARVIS Autonomous Subsystem\n\n"
            self.type_text(header, interval=0.015)
            time.sleep(0.2)
            self.type_text(content, interval=0.02)
            self._log_action("AGENT", "Autonomous Notepad memo completed.")
            return True
        finally:
            self._is_busy = False

    def workflow_snap_window(self, direction: str = "max") -> bool:
        """Snaps or maximizes current foreground window (left, right, max, min)."""
        d = direction.lower().strip()
        self._log_action("WINDOW", f"Snapping active window ({d})...")
        if "max" in d:
            return self.hotkey("win", "up")
        elif "left" in d:
            return self.hotkey("win", "left")
        elif "right" in d:
            return self.hotkey("win", "right")
        elif "min" in d:
            return self.hotkey("win", "down")
        return False

    def workflow_switch_window(self) -> bool:
        """Alt+Tab to switch active window."""
        self._log_action("WINDOW", "Switching application window (Alt+Tab)...")
        return self.hotkey("alt", "tab")


_computer_agent_instance = None

def get_computer_agent() -> ComputerAgent:
    global _computer_agent_instance
    if _computer_agent_instance is None:
        _computer_agent_instance = ComputerAgent()
    return _computer_agent_instance
