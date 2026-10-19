"""
Live News Skill — Fetches real-time headlines using DuckDuckGo News (100% Free).
"""
from typing import List, Dict
from core.utils.logger import get_logger

logger = get_logger("skills.news")

class NewsSkill:
    def get_top_news(self, topic: str = "Pakistan", count: int = 5) -> str:
        """Fetches top news headlines for the specified country or topic."""
        logger.info(f"Fetching top {count} news for: '{topic}'")
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.news(topic, max_results=count))
                if not results:
                    return f"Ahmad, mujhe '{topic}' ke hawale se filhal koi taaza khabar nahi mili."

                headlines = []
                for idx, r in enumerate(results[:count], 1):
                    title = r.get("title", "").strip()
                    # Clean degree symbols or extra artifacts
                    title = title.replace("\u00b0", "").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
                    if title:
                        headlines.append(f"{idx}. {title}")

                joined = " ".join(headlines)
                resp = f"Ahmad, {topic} ki top {len(headlines)} taaza khabrein yeh hain: {joined}"
                return resp
        except Exception as e:
            logger.warning(f"Error fetching live news: {e}")
            return f"Ahmad, news fetch karte waqt connection issue aaya: {e}"

_news_instance = None

def get_news_skill() -> NewsSkill:
    global _news_instance
    if _news_instance is None:
        _news_instance = NewsSkill()
    return _news_instance
