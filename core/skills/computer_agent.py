"""
Autonomous Computer-Use Agent — controls mouse cursor, keyboard,
window management, and multi-step desktop workflows (Stonic AI style).
"""
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

import pyautogui
from core.utils.logger import get_logger
from core.skills.system_control import shell_execute, get_chrome_path

logger = get_logger("skills.computer_agent")

# Configure PyAutoGUI safely
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

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
    # MOUSE CONTROL
    # ==========================================
    def move_to(self, x: int, y: int, duration: float = 0.35) -> bool:
        try:
            # Bound coordinates within screen
            tx = max(0, min(self.screen_width - 1, int(x)))
            ty = max(0, min(self.screen_height - 1, int(y)))
            pyautogui.moveTo(tx, ty, duration=duration, tween=pyautogui.easeInOutQuad)
            self._log_action("MOUSE", f"Moved cursor to ({tx}, {ty})")
            return True
        except Exception as e:
            logger.error(f"move_to failed: {e}")
            return False

    def move_rel(self, dx: int, dy: int) -> bool:
        try:
            cur_x, cur_y = pyautogui.position()
            return self.move_to(cur_x + dx, cur_y + dy, duration=0.05)
        except Exception as e:
            logger.error(f"move_rel failed: {e}")
            return False

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> bool:
        try:
            btn = "left"
            if button in ("right", "middle", "left", "primary", "secondary"):
                btn = button
            elif button == "double":
                btn = "left"
                clicks = 2
            if x is not None and y is not None:
                self.move_to(x, y, duration=0.2)
            pyautogui.click(button=btn, clicks=clicks)
            self._log_action("MOUSE", f"Clicked {btn} button ({clicks}x) at {pyautogui.position()}")
            return True
        except Exception as e:
            logger.error(f"click failed: {e}")
            return False

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x=x, y=y, button="right", clicks=1)

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x=x, y=y, button="left", clicks=2)

    def scroll(self, amount: int) -> bool:
        try:
            pyautogui.scroll(amount)
            self._log_action("MOUSE", f"Scrolled mouse wheel ({amount})")
            return True
        except Exception as e:
            logger.error(f"scroll failed: {e}")
            return False

    # ==========================================
    # KEYBOARD CONTROL
    # ==========================================
    def type_text(self, text: str, interval: float = 0.025) -> bool:
        """Types text with natural human-like keystroke intervals."""
        try:
            self._log_action("KEYBOARD", f"Typing text: '{text[:35]}...'")
            pyautogui.write(text, interval=interval)
            return True
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

            # Move cursor to center-bottom of screen (typical chat prompt input area)
            prompt_x = int(self.screen_width * 0.5)
            prompt_y = int(self.screen_height * 0.88)
            self.move_to(prompt_x, prompt_y, duration=0.6)
            self.click()
            time.sleep(0.3)

            # Type prompt smoothly
            self.type_text(prompt, interval=0.03)
            time.sleep(0.4)
            self.press_key("enter")
            self._log_action("AGENT", "AI Prompt submitted successfully!")
            return True
        finally:
            self._is_busy = False

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
