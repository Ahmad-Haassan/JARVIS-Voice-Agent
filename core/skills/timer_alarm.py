"""
Timer & Alarm Skill — background timers and notification alerts.
"""
import threading
import time
from core.utils.logger import get_logger

logger = get_logger("skills.timer")

class TimerSkill:
    def set_timer(self, seconds: int, label: str = "Timer") -> str:
        logger.info(f"Setting timer for {seconds} seconds ('{label}')")
        def _countdown():
            time.sleep(seconds)
            try:
                from core.voice.tts import get_tts
                get_tts().speak(f"Alert: Your {label} for {seconds} seconds has finished!")
            except Exception as e:
                logger.error(f"Timer alarm failed: {e}")

        threading.Thread(target=_countdown, daemon=True).start()
        return f"Timer set for {seconds} seconds."

_timer_instance = None

def get_timer() -> TimerSkill:
    global _timer_instance
    if _timer_instance is None:
        _timer_instance = TimerSkill()
    return _timer_instance
