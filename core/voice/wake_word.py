"""
Wake-word detection using Vosk (offline & open-source).
Listens continuously for the activation keyword ("jarvis").
"""
import os
import json
import queue
import threading
import time
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("voice.wake")

class WakeDetector:
    def __init__(self, on_detected=None):
        self.on_detected = on_detected
        self._running = False
        self._paused = False
        self._thread = None
        self._model = None
        self._audio_queue = queue.Queue()
        self.wake_word = cfg.get("app", "wake_word", "jarvis").lower()

    def _get_model_path(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        possible_paths = [
            os.path.join(root, "model"),
            os.path.join(root, "data", "vosk-model-small-en-us-0.15"),
            os.path.join(root, "vosk-model-small-en-us-0.15"),
        ]
        for p in possible_paths:
            if os.path.exists(p) and os.path.isdir(p):
                return p
        return None

    def start(self):
        if self._running:
            return
        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"Wake word detector started for keyword '{self.wake_word}'.")

    def pause(self):
        self._paused = True
        logger.info("Wake word detector paused.")

    def resume(self):
        self._paused = False
        logger.info("Wake word detector resumed.")

    def stop(self):
        self._running = False
        self._paused = False
        logger.info("Wake word detector stopped.")

    def _listen_loop(self):
        model_path = self._get_model_path()
        if not model_path:
            logger.info("No offline Vosk model found. Activating continuous background microphone listener...")
            self._speech_recognition_wake_loop()
            return

        try:
            from vosk import Model, KaldiRecognizer
            import sounddevice as sd

            logger.info(f"Loading Vosk model from: {model_path}")
            model = Model(model_path)
            recognizer = KaldiRecognizer(model, 16000)

            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"Audio status: {status}")
                if self._running and not self._paused:
                    self._audio_queue.put(bytes(indata))

            with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                                   channels=1, callback=audio_callback):
                logger.info("Microphone stream opened for wake word detection.")
                while self._running:
                    if self._paused:
                        time.sleep(0.3)
                        continue
                    try:
                        data = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    if recognizer.AcceptWaveform(data):
                        res = json.loads(recognizer.Result())
                        text = res.get("text", "").lower()
                        if self.wake_word in text or "jarvis" in text:
                            logger.info(f"Wake word detected in: '{text}'!")
                            self.pause()
                            if self.on_detected:
                                threading.Thread(target=self.on_detected, daemon=True).start()
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        part_text = partial.get("partial", "").lower()
                        if self.wake_word in part_text or "jarvis" in part_text:
                            logger.info(f"Wake word detected in partial: '{part_text}'!")
                            recognizer.Reset()
                            self.pause()
                            if self.on_detected:
                                threading.Thread(target=self.on_detected, daemon=True).start()
        except Exception as e:
            logger.warning(f"Vosk wake word loop error: {e}")
            while self._running:
                time.sleep(1.0)

    def _speech_recognition_wake_loop(self):
        WAKE_VARIANTS = [
            self.wake_word, "jarvis", "javis", "travis",
            "service", "darvis", "charvis", "harvest", "starvis"
        ]

        while self._running:
            if self._paused:
                time.sleep(0.3)
                continue

            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 280
                recognizer.dynamic_energy_threshold = False  # Fixed threshold to prevent deafening

                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    logger.info(f"Microphone active. Listening continuously for '{self.wake_word}'...")

                    while self._running and not self._paused:
                        try:
                            audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=4.0)
                            if self._paused or not self._running:
                                break

                            try:
                                text = recognizer.recognize_google(audio).lower()
                                logger.info(f"Microphone heard: '{text}'")
                                if any(v in text for v in WAKE_VARIANTS):
                                    logger.info(f"Wake word detected via speech recognition: '{text}'!")
                                    self.pause()
                                    if self.on_detected:
                                        threading.Thread(target=self.on_detected, daemon=True).start()
                                    break  # Exit with sr.Microphone() block so mic is free
                            except sr.UnknownValueError:
                                pass
                            except Exception as e:
                                logger.debug(f"Speech recognition parse error: {e}")
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as e:
                            logger.debug(f"Audio listen timeout/error: {e}")
                            time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Continuous wake loop error: {e}")
                time.sleep(1.0)

_wake_instance = None

def get_wake_detector(on_detected=None) -> WakeDetector:
    global _wake_instance
    if _wake_instance is None:
        _wake_instance = WakeDetector(on_detected=on_detected)
    elif on_detected is not None:
        _wake_instance.on_detected = on_detected
    return _wake_instance
