import os
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("auth.voice")

def is_voice_enrolled() -> bool:
    print_path = cfg.get("auth", "voice_print_path", "data/voice_prints")
    if os.path.exists(print_path):
        files = [f for f in os.listdir(print_path) if f.endswith(".npy") or f.endswith(".wav")]
        return len(files) > 0
    return False

def enroll_voice() -> bool:
    logger.info("Voice enrollment requested.")
    return True

def verify_voice() -> bool:
    logger.info("Voice verification requested.")
    return True
