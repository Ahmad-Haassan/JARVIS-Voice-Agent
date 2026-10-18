"""
NLP Engine — intent recognition via Google Gemini API with comprehensive rule-based fallback.
"""
import json
import re
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("ai.nlp")

class NLPEngine:
    def __init__(self):
        self._model = None
        self._init_gemini()

    def _init_gemini(self):
        api_key = cfg.get("ai", "gemini_api_key", "").strip()
        if not api_key:
            logger.info("No Gemini API key configured. Rule engine active.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_name = cfg.get("ai", "model", "gemini-3.8-flash")
            self._model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini model '{model_name}' initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini model: {e}")
            self._model = None

    def clean_query(self, text: str) -> str:
        """Removes leading wake words and filler speech."""
        cleaned = (text or "").strip()
        wake_words = ["hey jarvis", "jarvis", "ok jarvis", "okay jarvis", "hello jarvis", "please"]
        lower = cleaned.lower()
        for w in wake_words:
            if lower.startswith(w):
                cleaned = cleaned[len(w):].strip(", !.?")
                lower = cleaned.lower()
        return cleaned

    def process(self, text: str) -> dict:
        query = self.clean_query(text)
        if not query:
            return {"intent": "chat", "entities": {}, "response": "Yes, I am listening."}

        logger.info(f"Processing command: '{query}'")

        # Fast-Path: Instantly resolve direct action commands (zero latency & no quota errors)
        fast_action = self._match_direct_command(query)
        if fast_action:
            logger.info(f"Fast-path matched intent: {fast_action.get('intent')}")
            return fast_action

        # Try Gemini AI for complex reasoning / conversational queries
        if self._model:
            try:
                prompt = (
                    "You are JARVIS, an advanced voice assistant running locally on Windows. "
                    "Analyze the user query and return ONLY valid JSON with keys 'intent', 'entities', and 'response'.\n"
                    "Possible intents:\n"
                    "- 'open_app' (entities: {'app': str})\n"
                    "- 'close_app' (entities: {'app': str})\n"
                    "- 'send_whatsapp' (entities: {'contact': str, 'message': str})\n"
                    "- 'youtube_play' (entities: {'query': str})\n"
                    "- 'work_mode' (entities: {})\n"
                    "- 'system_control' (entities: {'action': 'screenshot' | 'diagnostics' | 'lock' | 'sleep' | 'shutdown' | 'restart'})\n"
                    "- 'file_action' (entities: {'action': 'create_folder', 'name': str})\n"
                    "- 'weather' (entities: {'city': str})\n"
                    "- 'search_web' (entities: {'query': str})\n"
                    "- 'chat' (general conversation or question)\n\n"
                    f"User Query: \"{query}\"\n"
                    "Output JSON:"
                )
                res = self._model.generate_content(prompt)
                raw_text = res.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "intent" in parsed:
                    logger.info(f"Gemini parsed intent: {parsed.get('intent')}")
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini processing error: {e}")

        # Fallback to conversational small talk or web search
        return self._conversational_fallback(query)

    def _match_direct_command(self, query: str) -> dict:
        q = query.lower()

        # 1. Work Mode & Antigravity IDE
        if "antigravity" in q:
            return {"intent": "open_app", "entities": {"app": "antigravity"}, "response": "Opening Antigravity IDE."}

        if "work mode" in q or "workmode" in q:
            return {"intent": "work_mode", "entities": {}, "response": "Initiating development work mode. Opening Antigravity IDE, Google Chrome, and terminal."}

        # 2. System Diagnostics & Telemetry
        if any(w in q for w in ["system diagnostic", "diagnostics", "cpu load", "ram usage", "battery", "system specs"]):
            return {"intent": "system_control", "entities": {"action": "diagnostics"}, "response": "Checking system diagnostics."}

        # 3. Screenshot
        if "screenshot" in q or "screen shot" in q:
            return {"intent": "system_control", "entities": {"action": "screenshot"}, "response": "Capturing screen."}

        # 4. WhatsApp Automation
        if "whatsapp" in q or "message" in q:
            m = re.search(r"(?:send message to|message|tell|whatsapp)\s+([a-zA-Z0-9_\s]+?)\s+(?:saying|that|:)\s+(.+)", q)
            if m:
                contact = m.group(1).strip()
                msg = m.group(2).strip()
                return {"intent": "send_whatsapp", "entities": {"contact": contact, "message": msg}, "response": f"Sending WhatsApp message to {contact}."}
            elif "open whatsapp" in q or q.strip() == "whatsapp":
                return {"intent": "open_app", "entities": {"app": "whatsapp"}, "response": "Opening WhatsApp Desktop."}

        # 5. YouTube Media Playback
        if "youtube" in q or q.startswith("play "):
            play_query = q
            for prefix in ["play on youtube", "play in youtube", "play on you tube", "play", "youtube"]:
                if play_query.startswith(prefix):
                    play_query = play_query[len(prefix):].strip()
            play_query = play_query.replace("on youtube", "").strip()
            return {"intent": "youtube_play", "entities": {"query": play_query or "music"}, "response": f"Playing {play_query or 'music'} on YouTube."}

        # 6. Camera & Webcam
        if any(w in q for w in ["camera", "webcam", "take photo", "view camera", "access camera"]):
            return {"intent": "camera", "entities": {"action": "stream"}, "response": "Opening computer camera feed."}

        # 6.5 Autonomous Computer Control & Stonic AI Workflows
        if any(w in q for w in ["take over", "autonomous", "control mouse", "move mouse", "type note", "ask chatgpt", "snap window"]):
            if "snap" in q:
                dir_choice = "max"
                if "left" in q: dir_choice = "left"
                elif "right" in q: dir_choice = "right"
                elif "min" in q: dir_choice = "min"
                return {"intent": "computer_agent", "entities": {"action": "snap", "direction": dir_choice}, "response": f"Snapping active window {dir_choice}."}
            elif "ask chatgpt" in q or "ask ai" in q:
                m = re.search(r"(?:ask chatgpt|ask ai)\s+(?:about|to|that)?\s*(.+)", q)
                prompt = m.group(1).strip() if m else "Explain quantum computing in simple terms"
                return {"intent": "computer_agent", "entities": {"action": "ask_ai", "prompt": prompt}, "response": f"Autonomous agent opening ChatGPT and entering prompt."}
            elif "type note" in q or "write note" in q:
                m = re.search(r"(?:type note|write note)\s+(?:about|saying|that)?\s*(.+)", q)
                note_text = m.group(1).strip() if m else "Follow up on project tasks"
                return {"intent": "computer_agent", "entities": {"action": "notepad", "content": note_text}, "response": "Opening Notepad and typing memo."}

        if "alt tab" in q or "switch window" in q:
            return {"intent": "computer_agent", "entities": {"action": "switch_window"}, "response": "Switching active window."}
        if "scroll down" in q:
            return {"intent": "computer_agent", "entities": {"action": "scroll", "amount": -400}, "response": "Scrolling page down."}
        if "scroll up" in q:
            return {"intent": "computer_agent", "entities": {"action": "scroll", "amount": 400}, "response": "Scrolling page up."}
        if "maximize" in q and ("window" in q or "screen" in q):
            return {"intent": "computer_agent", "entities": {"action": "snap", "direction": "max"}, "response": "Maximizing window."}

        # 7. System Power & Unlock
        if "unlock" in q and ("pc" in q or "computer" in q or "screen" in q or q.strip() == "unlock"):
            m = re.search(r"pin\s*([0-9]{4,8})", q)
            pin = m.group(1) if m else ""
            return {"intent": "system_control", "entities": {"action": "unlock", "pin": pin}, "response": "Waking and unlocking workstation."}

        if "lock" in q and ("pc" in q or "computer" in q or "screen" in q or q.strip() == "lock"):
            return {"intent": "system_control", "entities": {"action": "lock"}, "response": "Locking workstation."}
        if "sleep" in q and ("pc" in q or "computer" in q or "go to sleep" in q or q.strip() == "sleep"):
            return {"intent": "system_control", "entities": {"action": "sleep"}, "response": "Entering sleep state."}

        # 7. File Actions
        if "desktop folder" in q or "create folder" in q or "new folder" in q:
            folder_name = "New Folder"
            m = re.search(r"folder\s+(?:named|called)?\s*([a-zA-Z0-9_\-]+)", q)
            if m:
                folder_name = m.group(1).strip()
            return {"intent": "file_action", "entities": {"action": "create_folder", "name": folder_name}, "response": f"Creating desktop folder '{folder_name}'."}

        # 8. Weather
        if "weather" in q or "temperature" in q:
            city = cfg.get("skills", "weather_city", "Karachi")
            m = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", q)
            if m:
                city = m.group(1).strip()
            return {"intent": "weather", "entities": {"city": city}, "response": f"Checking weather for {city}."}

        # 9. Close App
        if q.startswith("close ") or q.startswith("kill ") or q.startswith("exit "):
            app = q.split(" ", 1)[1].strip()
            return {"intent": "close_app", "entities": {"app": app}, "response": f"Closing {app}."}

        # 10. Open App
        if q.startswith("open ") or q.startswith("launch ") or q.startswith("start "):
            app = q.split(" ", 1)[1].strip()
            return {"intent": "open_app", "entities": {"app": app}, "response": f"Opening {app}."}

        if "chrome" in q or "google chrome" in q:
            return {"intent": "open_app", "entities": {"app": "chrome"}, "response": "Opening Google Chrome."}

        return None

    def _conversational_fallback(self, query: str) -> dict:
        q = query.lower()

        # 1. Work Mode & Antigravity IDE
        if "antigravity" in q:
            return {"intent": "open_app", "entities": {"app": "antigravity"}, "response": "Opening Antigravity IDE."}

        if "work mode" in q or "workmode" in q:
            return {"intent": "work_mode", "entities": {}, "response": "Initiating development work mode. Opening Antigravity IDE, Google Chrome, and terminal."}

        # 2. System Diagnostics & Telemetry
        if any(w in q for w in ["system diagnostic", "diagnostics", "cpu load", "ram usage", "battery", "system specs"]):
            return {"intent": "system_control", "entities": {"action": "diagnostics"}, "response": "Checking system diagnostics."}

        # 3. Screenshot
        if "screenshot" in q or "screen shot" in q:
            return {"intent": "system_control", "entities": {"action": "screenshot"}, "response": "Capturing screen."}

        # 4. WhatsApp Automation
        if "whatsapp" in q or "message" in q:
            # Check pattern: send message to X saying Y
            m = re.search(r"(?:send message to|message|tell|whatsapp)\s+([a-zA-Z0-9_\s]+?)\s+(?:saying|that|:)\s+(.+)", q)
            if m:
                contact = m.group(1).strip()
                msg = m.group(2).strip()
                return {"intent": "send_whatsapp", "entities": {"contact": contact, "message": msg}, "response": f"Sending WhatsApp message to {contact}."}
            elif "open whatsapp" in q:
                return {"intent": "open_app", "entities": {"app": "whatsapp"}, "response": "Opening WhatsApp Desktop."}

        # 5. YouTube Media Playback
        if "youtube" in q or q.startswith("play "):
            play_query = q
            for prefix in ["play on youtube", "play in youtube", "play on you tube", "play", "youtube"]:
                if play_query.startswith(prefix):
                    play_query = play_query[len(prefix):].strip()
            play_query = play_query.replace("on youtube", "").strip()
            return {"intent": "youtube_play", "entities": {"query": play_query or "music"}, "response": f"Playing {play_query or 'music'} on YouTube."}

        # 6. File Actions
        if "desktop folder" in q or "create folder" in q or "new folder" in q:
            folder_name = "New Folder"
            m = re.search(r"folder\s+(?:named|called)?\s*([a-zA-Z0-9_\-]+)", q)
            if m:
                folder_name = m.group(1).strip()
            return {"intent": "file_action", "entities": {"action": "create_folder", "name": folder_name}, "response": f"Creating desktop folder '{folder_name}'."}

        # 7. Weather
        if "weather" in q or "temperature" in q:
            city = cfg.get("skills", "weather_city", "Karachi")
            m = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", q)
            if m:
                city = m.group(1).strip()
            return {"intent": "weather", "entities": {"city": city}, "response": f"Checking weather for {city}."}

        # 8. Close App
        if q.startswith("close ") or q.startswith("kill ") or q.startswith("exit "):
            app = q.split(" ", 1)[1].strip()
            return {"intent": "close_app", "entities": {"app": app}, "response": f"Closing {app}."}

        # 9. Open App
        if q.startswith("open ") or q.startswith("launch ") or q.startswith("start "):
            app = q.split(" ", 1)[1].strip()
            return {"intent": "open_app", "entities": {"app": app}, "response": f"Opening {app}."}

        # 10. System Power
        if "lock" in q and ("pc" in q or "computer" in q or "screen" in q):
            return {"intent": "system_control", "entities": {"action": "lock"}, "response": "Locking workstation."}
        if "sleep" in q and ("pc" in q or "computer" in q or "go to sleep" in q):
            return {"intent": "system_control", "entities": {"action": "sleep"}, "response": "Entering sleep state."}

        # 11. Web Search
        if q.startswith("search ") or q.startswith("google ") or q.startswith("look up "):
            search_term = q.split(" ", 1)[1].strip()
            return {"intent": "search_web", "entities": {"query": search_term}, "response": f"Searching web for {search_term}."}

        # 12. General conversational small-talk
        greetings = {
            "hello": "Hello! How can I assist you today, sir?",
            "hi": "Hey there! Systems are fully operational.",
            "how are you": "I am operating at 100% capacity and ready to assist you.",
            "who are you": "I am JARVIS, your intelligent personal desktop assistant.",
        }
        for g, reply in greetings.items():
            if g in q:
                return {"intent": "chat", "entities": {}, "response": reply}

        # Default fallback: search query or general chat
        return {"intent": "search_web", "entities": {"query": query}, "response": f"Looking that up: '{query}'."}

_nlp_instance = None

def get_nlp() -> NLPEngine:
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPEngine()
    return _nlp_instance
