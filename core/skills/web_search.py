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
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    snippets = [r.get("body", "") for r in results if r.get("body")]
                    summary = " ".join(snippets[:2])
                    summary = summary.encode("ascii", "ignore").decode("ascii")
                    return summary[:400]
        except Exception as e:
            logger.warning(f"Web search error: {e}")

        # Fallback to browser search
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"I opened search results for '{query}' in your browser."

    def play_youtube(self, query: str) -> bool:
        logger.info(f"Playing YouTube query: '{query}'")
        try:
            import urllib.request
            import re
            from core.skills.system_control import shell_execute, get_chrome_path

            encoded = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded}"
            play_url = search_url

            # Scrape first video ID for instant direct playback
            try:
                req = urllib.request.Request(
                    search_url, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
                    if ids:
                        first_id = ids[0]
                        play_url = f"https://www.youtube.com/watch?v={first_id}"
                        logger.info(f"Found first YouTube video: {play_url}")
            except Exception as fe:
                logger.warning(f"Direct video extraction fallback: {fe}")

            cp = get_chrome_path()
            if cp:
                return shell_execute(cp, play_url)
            return shell_execute(play_url)
        except Exception as e:
            logger.error(f"YouTube play error: {e}")
            return False

_web_instance = None

def get_web_search() -> WebSearch:
    global _web_instance
    if _web_instance is None:
        _web_instance = WebSearch()
    return _web_instance
