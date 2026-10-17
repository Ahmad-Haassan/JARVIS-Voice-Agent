import queue
import threading
import time
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("voice.tts")

class TTSEngine:
    def __init__(self):
        self._queue = queue.Queue()
        self._running = True
        self._engine = None
        self._speaking = False
        self._stop_current = False
        self._init_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._init_thread.start()

    def _worker_loop(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            rate = cfg.get("voice", "tts_rate", 175)
            self._engine.setProperty("rate", rate)
            logger.info("TTS Engine initialized with pyttsx3.")
        except Exception as e:
            logger.warning(f"Could not initialize pyttsx3 engine: {e}")
            self._engine = None

        while self._running:
            try:
                task = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            text, block, done_event = task
            if not text:
                if done_event:
                    done_event.set()
                continue

            self._speaking = True
            self._stop_current = False
            try:
                if self._engine:
                    self._engine.say(text)
                    self._engine.runAndWait()
                else:
                    logger.info(f"[TTS Audio Simulation]: {text}")
                    # Simulate speech duration based on word count
                    time.sleep(max(0.5, len(text.split()) * 0.25))
            except Exception as e:
                logger.error(f"TTS Speech error: {e}")
                # Try re-initializing engine if it encountered a driver error
                try:
                    import pyttsx3
                    self._engine = pyttsx3.init()
                except Exception:
                    pass
            finally:
                self._speaking = False
                if done_event:
                    done_event.set()

    def speak(self, text: str, block: bool = False):
        if not text or not text.strip():
            return
        logger.info(f"Jarvis Speaking: {text}")
        done_event = threading.Event() if block else None
        self._queue.put((text, block, done_event))
        if block and done_event:
            done_event.wait(timeout=15.0)

    def stop(self):
        self._stop_current = True
        # Clear any queued pending speech
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        try:
            if self._engine:
                self._engine.stop()
        except Exception:
            pass

_tts_instance = None

def get_tts() -> TTSEngine:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSEngine()
    return _tts_instance
