import os
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("voice.stt")

class STTEngine:
    def __init__(self):
        self._recognizer = None
        self._whisper_model = None
        self._init_engine()

    def _init_engine(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 280
            self._recognizer.dynamic_energy_threshold = False
            logger.info("SpeechRecognition engine initialized.")
        except ImportError:
            logger.warning("speech_recognition library not available.")

    def transcribe(self, audio_data=None) -> str:
        """Transcribe an audio buffer or return string if already transcribed."""
        if isinstance(audio_data, str):
            return audio_data
        if not audio_data or not self._recognizer:
            return ""
        try:
            return self._recognizer.recognize_google(audio_data).strip()
        except Exception:
            return ""

    def listen(self, timeout: float = 7.0, phrase_time_limit: float = 10.0) -> str:
        """Listens from the microphone and returns the transcribed text."""
        if not self._recognizer:
            self._init_engine()
        if not self._recognizer:
            logger.warning("STT Engine not available.")
            return ""

        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                logger.info(f"Listening for command (timeout={timeout}s, phrase_limit={phrase_time_limit}s)...")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                logger.info("Audio captured, transcribing...")

                # First try faster-whisper if configured
                stt_engine = cfg.get("voice", "stt_engine", "google").lower()
                if stt_engine == "whisper":
                    try:
                        from faster_whisper import WhisperModel
                        if self._whisper_model is None:
                            model_size = cfg.get("voice", "whisper_model", "base")
                            self._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
                        
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                            tf.write(audio.get_wav_data())
                            wav_path = tf.name
                        
                        segments, _ = self._whisper_model.transcribe(wav_path, beam_size=2)
                        text = " ".join([seg.text for seg in segments]).strip()
                        try:
                            os.remove(wav_path)
                        except Exception:
                            pass
                        logger.info(f"Whisper Transcribed: '{text}'")
                        return text
                    except Exception as we:
                        logger.warning(f"Whisper transcription failed, falling back to Google: {we}")

                # Google Speech Recognition fallback
                text = self._recognizer.recognize_google(audio)
                logger.info(f"Google STT Transcribed: '{text}'")
                return text.strip()

        except sr.WaitTimeoutError:
            logger.info("Listening timed out, no speech detected.")
            return ""
        except sr.UnknownValueError:
            logger.info("Could not understand audio.")
            return ""
        except Exception as e:
            logger.warning(f"Error during audio recording/transcription: {e}")
            return ""

_stt_instance = None

def get_stt() -> STTEngine:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = STTEngine()
    return _stt_instance
