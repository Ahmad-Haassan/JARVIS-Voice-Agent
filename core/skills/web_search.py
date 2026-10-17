"""
Web Search & Media Skill — DuckDuckGo search + YouTube media queries.
"""
import urllib.parse
import webbrowser
import subprocess
from core.utils.logger import get_logger

logger = get_logger("skills.web")

class WebSearch:
    def search(self, query: str) -> str:
        logger.info(f"Performing search query: '{query}'")
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    snippets = [r.get("body", "") for r in results if r.get("body")]
                    summary = " ".join(snippets[:2])
                    return summary[:350]
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")

        # Fallback to browser search
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"I opened search results for '{query}' in your browser."

    def play_youtube(self, query: str) -> bool:
        logger.info(f"Playing YouTube query: '{query}'")
        try:
            from core.skills.system_control import get_chrome_path
            encoded = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            cp = get_chrome_path()
            if cp:
                subprocess.Popen([cp, url])
                return True
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.error(f"YouTube play error: {e}")
            return False

_web_instance = None

def get_web_search() -> WebSearch:
    global _web_instance
    if _web_instance is None:
        _web_instance = WebSearch()
    return _web_instance
