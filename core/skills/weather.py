"""
Weather Skill — fetches live meteorological telemetry using wttr.in.
"""
import requests
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("skills.weather")

class WeatherSkill:
    def get_weather(self, city: str = None) -> str:
        target_city = city or cfg.get("skills", "weather_city", "Karachi")
        logger.info(f"Querying weather for: '{target_city}'")
        try:
            url = f"https://wttr.in/{target_city}?format=%C,+%t+(feels+like+%f)+with+humidity+%h"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                raw = res.text.strip()
                cleaned = raw.replace("°C", " degrees Celsius").replace("°F", " degrees Fahrenheit").replace("+", "")
                cleaned = " ".join(cleaned.split())
                report = f"The weather in {target_city} is {cleaned}."
                return report
        except Exception as e:
            logger.warning(f"Weather lookup error: {e}")

        return f"Could not retrieve current weather telemetry for {target_city}."

_weather_instance = None

def get_weather() -> WeatherSkill:
    global _weather_instance
    if _weather_instance is None:
        _weather_instance = WeatherSkill()
    return _weather_instance
