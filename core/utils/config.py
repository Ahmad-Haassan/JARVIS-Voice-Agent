import json
import os
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

_config = None

DEFAULT_CONFIG = {
    "app": {
        "name": "Jarvis",
        "version": "1.0.0",
        "wake_word": "jarvis",
        "language": "en",
        "theme": "dark"
    },
    "auth": {
        "password_hash": "",
        "voice_auth_enabled": False,
        "voice_print_path": "data/voice_prints"
    },
    "ai": {
        "provider": "gemini",
        "gemini_api_key": "",
        "openai_api_key": "",
        "model": "gemini-1.5-flash"
    },
    "voice": {
        "tts_engine": "pyttsx3",
        "tts_rate": 175,
        "stt_engine": "whisper",
        "whisper_model": "base"
    },
    "skills": {
        "weather_city": "Karachi",
        "default_browser": "chrome"
    },
    "system": {
        "minimize_to_tray": True,
        "startup_with_windows": False
    }
}

def load_config() -> dict:
    global _config
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _config = json.load(f)
                return _config
        except Exception:
            _config = DEFAULT_CONFIG.copy()
            return _config
    else:
        _config = DEFAULT_CONFIG.copy()
        save_config(_config)
        return _config

def save_config(cfg_dict: dict = None):
    global _config
    if cfg_dict is not None:
        _config = cfg_dict
    elif _config is None:
        _config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(_config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get(section: str, key: str, default: Any = None) -> Any:
    global _config
    if _config is None:
        load_config()
    sec_data = _config.get(section, {})
    if isinstance(sec_data, dict):
        return sec_data.get(key, default)
    return default

def set_value(section: str, key: str, value: Any):
    global _config
    if _config is None:
        load_config()
    if section not in _config or not isinstance(_config[section], dict):
        _config[section] = {}
    _config[section][key] = value
    save_config()
