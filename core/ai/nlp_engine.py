"""
NLP Engine — Intelligent Intent Recognition, Semantic Tool Calling & Conversational Memory.
"""
import os
import json
import re
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("ai.nlp")

class NLPEngine:
    def __init__(self):
        self._model = None
        self._history = []  # Short-term conversational memory
        self._last_opened_app = None
        self._init_gemini()

    def _init_gemini(self):
        api_key = cfg.get("ai", "gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key or api_key.startswith("AQ."):
            logger.info("No valid Gemini API key configured. Smart Natural Language Engine active.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_name = cfg.get("ai", "model", "gemini-1.5-flash")
            self._model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini model '{model_name}' initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini model: {e}")
            self._model = None

    def clean_query(self, text: str) -> str:
        """Removes leading wake words and filler speech."""
        cleaned = (text or "").strip()
        wake_words = ["hey jarvis", "jarvis", "ok jarvis", "okay jarvis", "hello jarvis", "please", "can you please", "could you", "can you"]
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

        # Fast-Path: Instantly resolve direct action commands with sub-10ms latency
        action = self._match_direct_command(query)
        if action:
            self._record_turn(query, action.get("response", ""))
            if action.get("intent") in ["open_app", "open_folder"]:
                self._last_opened_app = action.get("entities", {}).get("app") or action.get("entities", {}).get("folder")
            logger.info(f"Resolved intent: {action.get('intent')} with entities: {action.get('entities')}")
            return action

        # Try Gemini AI for complex reasoning or creative conversation
        if self._model:
            try:
                prompt = (
                    "You are JARVIS, Tony Stark's sophisticated, polite, and witty AI running locally on Windows. "
                    "Analyze the user query and return ONLY valid JSON with keys 'intent', 'entities', and 'response'.\n"
                    "Possible intents:\n"
                    "- 'open_folder' (entities: {'folder': str})\n"
                    "- 'open_app' (entities: {'app': str})\n"
                    "- 'close_app' (entities: {'app': str})\n"
                    "- 'volume_control' (entities: {'action': 'up'|'down'|'mute'|'unmute'|'set', 'level': int})\n"
                    "- 'media_control' (entities: {'action': 'play_pause'|'next'|'prev'})\n"
                    "- 'window_control' (entities: {'action': 'list'|'focus'|'minimize_all', 'app': str})\n"
                    "- 'screen_info' (entities: {})\n"
                    "- 'send_whatsapp' (entities: {'contact': str, 'message': str})\n"
                    "- 'youtube_play' (entities: {'query': str})\n"
                    "- 'work_mode' (entities: {})\n"
                    "- 'file_action' (entities: {'action': 'create'|'open', 'name': str})\n"
                    "- 'system_control' (entities: {'action': 'screenshot' | 'diagnostics' | 'lock' | 'unlock' | 'sleep' | 'shutdown' | 'restart'})\n"
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
                    self._record_turn(query, parsed.get("response", ""))
                    logger.info(f"Gemini parsed intent: {parsed.get('intent')}")
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini processing error: {e}")

        # Intelligent Semantic Fallback (handles natural Q&A, Web Search, Conversational Chitchat)
        result = self._semantic_fallback(query)
        self._record_turn(query, result.get("response", ""))
        return result

    def _record_turn(self, query: str, response: str):
        self._history.append({"user": query, "jarvis": response})
        if len(self._history) > 6:
            self._history.pop(0)

    def _match_direct_command(self, query: str) -> dict:
        q = query.lower().strip()

        # 1. Work / Study / Coding Mode
        work_keywords = [
            "work mode", "workmode", "study mode", "coding mode", "workspace",
            "set up workspace", "set up work", "get to work", "let's code", "prepare workspace",
            "time to code", "start development", "dev mode"
        ]
        if any(w in q for w in work_keywords):
            return {
                "intent": "work_mode",
                "entities": {},
                "response": "Initiating developer workspace. Launching Antigravity IDE, Google Chrome, and terminal."
            }

        # 2. Volume & Audio Control
        if any(w in q for w in ["volume up", "turn up the sound", "turn up sound", "turn up", "louder", "make it louder", "raise volume", "increase volume"]):
            return {"intent": "volume_control", "entities": {"action": "up"}, "response": "Increasing volume."}
        if any(w in q for w in ["volume down", "turn down the sound", "turn down sound", "turn down", "quieter", "make it quieter", "lower volume", "decrease volume", "too loud"]):
            return {"intent": "volume_control", "entities": {"action": "down"}, "response": "Lowering volume."}
        
        vol_match = re.search(r"(?:set volume|volume to|volume)\s*(?:to|at)?\s*(\d{1,3})%?", q)
        if vol_match and ("volume" in q or "%" in q):
            lvl = int(vol_match.group(1))
            return {"intent": "volume_control", "entities": {"action": "set", "level": lvl}, "response": f"Volume set to {lvl}%."}

        if any(w in q for w in ["unmute", "restore audio", "sound back"]):
            return {"intent": "volume_control", "entities": {"action": "unmute"}, "response": "Audio unmuted."}
        if any(w in q for w in ["mute", "silence", "shut up", "be quiet"]):
            return {"intent": "volume_control", "entities": {"action": "mute"}, "response": "Audio muted."}

        # 3. Media Playback Controls
        media_pause_patterns = ["pause", "resume", "stop music", "pause music", "pause the music", "pause audio", "pause video", "play music", "resume music", "stop song"]
        if any(w in q for w in media_pause_patterns) or re.search(r"\b(?:pause|resume)\b.*?\b(?:music|song|video|audio|playback)\b", q):
            return {"intent": "media_control", "entities": {"action": "play_pause"}, "response": "Toggled media playback."}
        if any(w in q for w in ["next song", "next track", "skip song", "skip track", "skip"]):
            return {"intent": "media_control", "entities": {"action": "next"}, "response": "Skipping to next track."}
        if any(w in q for w in ["previous song", "previous track", "prev track", "last song"]):
            return {"intent": "media_control", "entities": {"action": "prev"}, "response": "Playing previous track."}

        # 4. Windows & Screen Awareness
        if any(w in q for w in ["what's on my screen", "what is on my screen", "explain screen", "describe screen", "check screen", "what am i looking at"]):
            return {"intent": "screen_info", "entities": {}, "response": "Inspecting your active workspace."}

        if any(w in q for w in ["what is open", "what's open", "what apps are running", "list open windows", "show running apps", "open windows"]):
            return {"intent": "window_control", "entities": {"action": "list"}, "response": "Scanning open windows."}

        if any(w in q for w in ["minimize all", "show desktop", "hide windows", "minimize windows", "clear desktop"]):
            return {"intent": "window_control", "entities": {"action": "minimize_all"}, "response": "Minimizing all windows to show desktop."}

        focus_match = re.search(r"(?:bring|switch to|focus|show)\s+(?:window\s+)?([a-zA-Z0-9_\s]+?)(?:\s+to front|\s+window)?$", q)
        if focus_match:
            target_app = focus_match.group(1).strip()
            if target_app and target_app not in ["desktop", "screen", "all"]:
                return {"intent": "window_control", "entities": {"action": "focus", "app": target_app}, "response": f"Bringing {target_app} to front."}

        # 5. Screenshot
        if any(w in q for w in ["screenshot", "screen shot", "capture screen", "snap screen"]):
            return {"intent": "system_control", "entities": {"action": "screenshot"}, "response": "Capturing screen."}

        # 6. Computer Camera & Webcam
        if any(w in q for w in ["camera", "webcam", "take photo", "view camera", "access camera", "pc camera"]):
            return {"intent": "camera", "entities": {"action": "stream"}, "response": "Opening computer camera feed."}

        # 7a. Open Target in App WITH Prompt (e.g. "open dsa folder in antigravity and solve assignment 3", "testing folder in antigravity and solve assignment")
        open_in_prompt_match = re.search(
            r"^(?:open\s+|launch\s+)?(?:the\s+|my\s+)?(.+?)\s+(?:in|with|using)\s+([a-zA-Z0-9_\-\s]+?)(?:[\,\;\:\-]\s*|\s+(?:and\s+give\s+(?:the\s+|a\s+)?(?:same\s+)?(?:prompt|promt)\s*(?:as\s+i\s+give\s+from\s+mobile\s*)?|and\s+(?:prompt|promt)\s+|with\s+(?:prompt|promt)\s+|and\s+ask\s+(?:it\s+|him\s+)?(?:to\s+)?|and\s+tell\s+(?:it\s+|him\s+)?(?:to\s+)?|then\s+(?:prompt|promt)\s+|dispatch\s+(?:prompt|promt)\s*|and\s+|then\s+)|\s*[\"\'\“\”])\s*(.+)$",
            q,
            re.IGNORECASE
        )
        if open_in_prompt_match:
            raw_target = open_in_prompt_match.group(1).strip()
            raw_app = open_in_prompt_match.group(2).strip()
            prompt_raw = open_in_prompt_match.group(3).strip(' "\'“”')
            prompt_text = re.sub(r'(?i)[\s"\']*(?:enter|press enter|hit enter|submit|send)[\s"\']*$', '', prompt_raw).strip(' "\'“”')
            clean_target = re.sub(r"\s+(?:folder|forlder|fldr|directory|dir|file)$", "", raw_target, flags=re.IGNORECASE).strip()
            return {
                "intent": "open_in",
                "entities": {"target": clean_target or raw_target, "app": raw_app, "prompt": prompt_text},
                "response": f"Opening {clean_target or raw_target} in {raw_app} and running your prompt."
            }

        # 7b. Give / Send / Dispatch Prompt to App (e.g. "give promt to antigravity make three files")
        give_prompt_to_app = re.search(
            r"^(?:give|send|dispatch|pass|run)\s+(?:the\s+|a\s+)?(?:prompt|promt)\s+(?:to|in)\s+([a-zA-Z0-9_\-\s]+?)\s*[:\"\'\“\”\s]\s*(.+)$",
            q,
            re.IGNORECASE
        )
        if give_prompt_to_app:
            raw_app = give_prompt_to_app.group(1).strip()
            prompt_raw = give_prompt_to_app.group(2).strip(' "\'“”')
            prompt_text = re.sub(r'(?i)[\s"\']*(?:enter|press enter|hit enter|submit|send)[\s"\']*$', '', prompt_raw).strip(' "\'“”')
            return {
                "intent": "open_in",
                "entities": {"target": "", "app": raw_app, "prompt": prompt_text},
                "response": f"Dispatching prompt to {raw_app}: '{prompt_text}'."
            }

        # 7c. Dispatch Prompt Directly (e.g. "dispatch prompt write intro of mine")
        dispatch_prompt_only = re.search(
            r"^(?:dispatch|send|run|give)\s+(?:the\s+|a\s+)?(?:prompt|promt)\s*[:\"\'\“\”\s]\s*(.+)$",
            q,
            re.IGNORECASE
        )
        if dispatch_prompt_only:
            prompt_raw = dispatch_prompt_only.group(1).strip(' "\'“”')
            prompt_text = re.sub(r'(?i)[\s"\']*(?:enter|press enter|hit enter|submit|send)[\s"\']*$', '', prompt_raw).strip(' "\'“”')
            return {
                "intent": "open_in",
                "entities": {"target": "", "app": "antigravity", "prompt": prompt_text},
                "response": f"Dispatching prompt to Antigravity: '{prompt_text}'."
            }

        # 7d. Open App Directly WITH Prompt (e.g. "open antigravity and solve assignment 3")
        app_prompt_match = re.search(
            r"^(?:open|launch)\s+(antigravity|vs\s*code|vscode|code|cursor|notepad|chrome)\s+(?:and\s+give\s+(?:the\s+|a\s+)?(?:same\s+)?(?:prompt|promt)\s*|and\s+(?:prompt|promt)\s+|with\s+(?:prompt|promt)\s+|and\s+ask\s+(?:it\s+|him\s+)?(?:to\s+)?|and\s+tell\s+(?:it\s+|him\s+)?(?:to\s+)?|then\s+(?:prompt|promt)\s+|and\s+|then\s+)(.+)$",
            q,
            re.IGNORECASE
        )
        if app_prompt_match:
            raw_app = app_prompt_match.group(1).strip()
            prompt_raw = app_prompt_match.group(2).strip(' "\'“”')
            prompt_text = re.sub(r'(?i)[\s"\']*(?:enter|press enter|hit enter|submit|send)[\s"\']*$', '', prompt_raw).strip(' "\'“”')
            return {
                "intent": "open_in",
                "entities": {"target": "", "app": raw_app, "prompt": prompt_text},
                "response": f"Opening {raw_app} and dispatching prompt: {prompt_text}."
            }

        # 7c. Open Target in Specific Application WITHOUT Prompt (e.g. "open dsa folder in antigravity")
        open_in_match = re.search(r"^(?:open|launch)\s+(?:the\s+|my\s+)?(.+?)\s+(?:in|with|using)\s+([a-zA-Z0-9_\-\s]+)$", q)
        if open_in_match:
            raw_target = open_in_match.group(1).strip()
            raw_app = open_in_match.group(2).strip()
            clean_target = re.sub(r"\s+(?:folder|directory|file)$", "", raw_target).strip()
            return {
                "intent": "open_in",
                "entities": {"target": clean_target or raw_target, "app": raw_app},
                "response": f"Opening {clean_target or raw_target} in {raw_app}."
            }

        # 8. Antigravity IDE (Explicit)
        if "antigravity" in q:
            if "close" in q or "kill" in q or "exit" in q:
                return {"intent": "close_app", "entities": {"app": "antigravity"}, "response": "Closing Antigravity IDE."}
            return {"intent": "open_app", "entities": {"app": "antigravity"}, "response": "Opening Antigravity IDE."}


        # 8. Chrome
        if "chrome" in q or "google chrome" in q:
            if "close" in q or "kill" in q or "exit" in q:
                return {"intent": "close_app", "entities": {"app": "chrome"}, "response": "Closing Google Chrome."}
            return {"intent": "open_app", "entities": {"app": "chrome"}, "response": "Opening Google Chrome."}

        # 9. Folder & Directory Opening Patterns
        # e.g., "open my downloads folder", "open the jarvis folder", "open uni assignments folder"
        folder_match1 = re.search(r"^(?:open|launch|show|explore)\s+(?:my\s+|the\s+)?([a-zA-Z0-9_\-\s]+?)\s+(?:folder|directory)$", q)
        # e.g., "open folder downloads", "open directory test"
        folder_match2 = re.search(r"^(?:open|launch|show|explore)\s+(?:folder|directory)\s+(?:called\s+|named\s+|for\s+)?([a-zA-Z0-9_\-\s]+)$", q)
        
        if folder_match1:
            target = folder_match1.group(1).strip()
            if target:
                return {
                    "intent": "open_folder",
                    "entities": {"folder": target},
                    "response": f"Opening {target} folder."
                }

        if folder_match2:
            target = folder_match2.group(1).strip()
            if target:
                return {
                    "intent": "open_folder",
                    "entities": {"folder": target},
                    "response": f"Opening {target} folder."
                }

        # Direct folder triggers (e.g. "open downloads", "open documents", "open my pc", "open this pc")
        direct_folder_triggers = {
            "downloads": ["open downloads", "open my downloads", "open download", "open my download", "show downloads"],
            "documents": ["open documents", "open my documents", "open document", "open docs", "open my docs"],
            "desktop": ["open desktop", "open my desktop", "open desktop folder"],
            "pictures": ["open pictures", "open my pictures", "open photos", "open my photos", "open images", "open my images"],
            "videos": ["open videos", "open my videos", "open movies", "open my movies"],
            "music": ["open music", "open my music", "open songs", "open my songs"],
            "this pc": ["open this pc", "open my pc", "open pc", "open computer", "open my computer", "open file explorer", "open explorer"],
            "c drive": ["open c drive", "open drive c", "open c:", "open local disk c"],
            "d drive": ["open d drive", "open drive d", "open d:", "open local disk d"],
            "jarvis": ["open jarvis", "open jarvis folder", "open my jarvis folder", "open project", "open project folder", "open my project folder", "open workspace"]
        }
        for f_name, triggers in direct_folder_triggers.items():
            if q in triggers:
                return {
                    "intent": "open_folder",
                    "entities": {"folder": f_name},
                    "response": f"Opening {f_name}."
                }

        # Continuous Hands-Free Conversation Mode Toggles
        if any(w in q for w in ["continuous mode on", "enable continuous", "continuous on", "hands free on", "hands-free on", "lagatar suno", "always listen", "conversational mode"]):
            return {
                "intent": "continuous_mode",
                "entities": {"action": "on"},
                "response": "Continuous hands-free conversation mode activated. Main all time sun raha hoon Ahmad."
            }
        if any(w in q for w in ["continuous mode off", "disable continuous", "continuous off", "stop continuous", "hands free off", "chup ho jao", "standby", "pause listening", "ruk jao"]):
            return {
                "intent": "continuous_mode",
                "entities": {"action": "off"},
                "response": "Continuous mode deactivated. Standing by boss."
            }

        # Document to ChatGPT Dispatch Workflow (Roman Urdu & English)
        # e.g., "ye mera dsa folder hai usme week 3 document hai wo chatgpt ko bhejo aur usay kaho detail bataye"
        doc_cg1 = re.search(
            r"(?:(?:ye|mera|the|my)\s+)*([a-zA-Z0-9_\-\s]+?)\s+(?:folder|directory).*?(?:usme|mein|me|in)\s+([a-zA-Z0-9_\-\.\s]+?)\s+(?:document|doc|file)?\s*(?:hai)?\s*(?:wo\s+|woh\s+)?(?:chatgpt|browser|ai)\s+(?:ko\s+bhejo|ko\s+send\s+karo|ko\s+do|pe\s+bhejo|ko\s+dikhao)(?:\s+(?:aur|and|or)\s+(?:usay\s+|use\s+)?(?:kaho|bolo|ask|tell)\s+(.+))?",
            q,
            re.IGNORECASE
        )
        doc_cg2 = re.search(
            r"^(?:send|pass|give)\s+(?:document\s+|file\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:from|in)\s+([a-zA-Z0-9_\-\s]+?)\s+(?:folder|directory)?\s+(?:to|into)\s+chatgpt(?:\s+(?:and|with|to)\s+(?:ask|tell|instruct)?\s*(.+))?$",
            q,
            re.IGNORECASE
        )
        if doc_cg1:
            raw_fld = doc_cg1.group(1).strip()
            fld = re.sub(r"^(?:ye|mera|the|my)\s+", "", raw_fld, flags=re.IGNORECASE).strip()
            raw_doc = doc_cg1.group(2).strip()
            doc = re.sub(r"\s+(?:document|doc|file|hai)$", "", raw_doc, flags=re.IGNORECASE).strip()
            pmt = doc_cg1.group(3).strip() if doc_cg1.group(3) else "Please analyze this document and explain all details."
            return {
                "intent": "doc_to_chatgpt",
                "entities": {"folder": fld or raw_fld, "document": doc or raw_doc, "prompt": pmt},
                "response": f"Finding '{doc or raw_doc}' in '{fld or raw_fld}' folder and dispatching to ChatGPT."
            }
        elif doc_cg2:
            doc = doc_cg2.group(1).strip()
            fld = doc_cg2.group(2).strip()
            pmt = doc_cg2.group(3).strip() if doc_cg2.group(3) else "Please analyze this document and explain all details."
            return {
                "intent": "doc_to_chatgpt",
                "entities": {"folder": fld, "document": doc, "prompt": pmt},
                "response": f"Finding '{doc}' in '{fld}' folder and dispatching to ChatGPT."
            }

        # Live Real-Time News (Pakistan / Tech / World)
        if any(w in q for w in ["top news", "top 5 news", "news btao", "aj ki news", "khabrein", "pakistan news", "headlines", "latest news"]):
            topic = "Pakistan"
            if "tech" in q: topic = "Technology"
            elif "world" in q or "dunya" in q: topic = "World"
            elif "cricket" in q: topic = "Pakistan Cricket"
            return {"intent": "live_news", "entities": {"topic": topic, "count": 5}, "response": f"Fetching live news for {topic}."}

        # Direct ChatGPT Prompts (e.g. "chatgpt pe search karo 5 lines on AI", "ask chatgpt write python script")
        cg_match = re.search(r"(?:chatgpt|chat\s*gpt)\s+(?:pe|par|me|mein)\s+(?:search\s+karo|poocho|likho|bhejo|prompt\s+do)\s+(.+)", q)
        cg_match2 = re.search(r"^(?:ask|tell)\s+chatgpt\s+(?:to\s+)?(.+)", q)
        if cg_match:
            user_p = cg_match.group(1).strip()
            return {"intent": "chatgpt_prompt", "entities": {"prompt": user_p}, "response": f"Asking ChatGPT: '{user_p}'."}
        if cg_match2:
            user_p = cg_match2.group(1).strip()
            return {"intent": "chatgpt_prompt", "entities": {"prompt": user_p}, "response": f"Asking ChatGPT: '{user_p}'."}

        # Desktop Folder Creation (Roman Urdu & English)
        ru_folder1 = re.search(r"desktop\s+(?:pe|par|me|mein)\s+(?:folder\s+bana\s+(?:do|de|o)|naya\s+folder\s+banao)\s+(?:called\s+|named\s+)?([a-zA-Z0-9_\-\s]+)$", q)
        ru_folder2 = re.search(r"desktop\s+(?:pe|par|me|mein)\s+([a-zA-Z0-9_\-\s]+?)\s+(?:ka\s+)?folder\s+bana\s*(?:do|de|o)?$", q)
        create_folder_match = re.search(r"^(?:create|make|new)\s+(?:a\s+)?folder\s+(?:named\s+|called\s+)?([a-zA-Z0-9_\-\s]+)$", q)
        if ru_folder1:
            name = ru_folder1.group(1).strip()
            return {"intent": "file_action", "entities": {"action": "create", "name": name}, "response": f"Creating desktop folder '{name}'."}
        if ru_folder2:
            name = ru_folder2.group(1).strip()
            return {"intent": "file_action", "entities": {"action": "create", "name": name}, "response": f"Creating desktop folder '{name}'."}
        if create_folder_match:
            f_name = create_folder_match.group(1).strip()
            return {
                "intent": "file_action",
                "entities": {"action": "create", "name": f_name},
                "response": f"Creating desktop folder '{f_name}'."
            }

        # Open File Pattern (e.g. "open file resume.pdf", "open document lab.docx")
        file_match = re.search(r"^(?:open|launch|view|show)\s+(?:file|document)\s+(.+)$", q)
        if file_match:
            f_target = file_match.group(1).strip()
            return {"intent": "open_file", "entities": {"file": f_target}, "response": f"Opening file {f_target}."}

        if re.search(r"\.[a-zA-Z0-9]{2,4}$", q) and (q.startswith("open ") or q.startswith("show ")):
            clean_f = re.sub(r"^(?:open|show)\s+", "", q).strip()
            return {"intent": "open_file", "entities": {"file": clean_f}, "response": f"Opening {clean_f}."}

        # Universal PowerShell Command Execution
        if q.startswith("powershell ") or q.startswith("run command ") or q.startswith("cmd "):
            cmd = re.sub(r"^(?:powershell|run command|cmd)\s+", "", q).strip()
            return {"intent": "powershell_exec", "entities": {"command": cmd}, "response": f"Executing command: {cmd}"}

        # 10. App Open / Close
        if q.startswith("close ") or q.startswith("kill ") or q.startswith("exit "):
            app_to_close = q.split(" ", 1)[1].strip()
            return {"intent": "close_app", "entities": {"app": app_to_close}, "response": f"Closing {app_to_close}."}

        if q.startswith("open ") or q.startswith("launch ") or q.startswith("start ") or q.startswith("bring up "):
            app_to_open = q.split(" ", 1)[1].strip()
            for prefix in ["app ", "program ", "the ", "my "]:
                if app_to_open.startswith(prefix):
                    app_to_open = app_to_open[len(prefix):].strip()
            if "folder" in app_to_open or "directory" in app_to_open:
                clean_target = re.sub(r"\b(?:folder|directory|my|the)\b", "", app_to_open).strip()
                return {"intent": "open_folder", "entities": {"folder": clean_target or app_to_open}, "response": f"Opening {clean_target or app_to_open} folder."}
            return {"intent": "open_app", "entities": {"app": app_to_open}, "response": f"Opening {app_to_open}."}

        # 10. YouTube Media Playback
        if "youtube" in q or q.startswith("play ") or q.startswith("listen to "):
            play_query = q
            for prefix in ["play on youtube", "play in youtube", "play on you tube", "play", "listen to", "put on some", "put on", "youtube"]:
                if play_query.startswith(prefix):
                    play_query = play_query[len(prefix):].strip()
            play_query = play_query.replace("on youtube", "").strip()
            return {"intent": "youtube_play", "entities": {"query": play_query or "lofi beats"}, "response": f"Playing {play_query or 'music'} on YouTube."}

        # 11. WhatsApp Automation
        if "whatsapp" in q or "message" in q:
            m = re.search(r"(?:send message to|message|tell|whatsapp)\s+([a-zA-Z0-9_\s]+?)\s+(?:saying|that|:)\s+(.+)", q)
            if m:
                contact = m.group(1).strip()
                msg = m.group(2).strip()
                return {"intent": "send_whatsapp", "entities": {"contact": contact, "message": msg}, "response": f"Sending WhatsApp message to {contact}."}
            elif "open whatsapp" in q or q.strip() == "whatsapp":
                return {"intent": "open_app", "entities": {"app": "whatsapp"}, "response": "Opening WhatsApp Desktop."}

        # 12. System Diagnostics & Telemetry
        if any(w in q for w in ["system diagnostic", "diagnostics", "cpu load", "ram usage", "battery", "system specs", "how is my pc", "status"]):
            return {"intent": "system_control", "entities": {"action": "diagnostics"}, "response": "Checking system diagnostics."}

        # 13. System Power & Unlock
        if "unlock" in q and ("pc" in q or "computer" in q or "screen" in q or q.strip() == "unlock"):
            m = re.search(r"pin\s*([0-9]{4,8})", q)
            pin = m.group(1) if m else ""
            return {"intent": "system_control", "entities": {"action": "unlock", "pin": pin}, "response": "Waking and unlocking workstation."}

        if "lock" in q and ("pc" in q or "computer" in q or "screen" in q or q.strip() == "lock"):
            return {"intent": "system_control", "entities": {"action": "lock"}, "response": "Locking workstation."}
        if "sleep" in q and ("pc" in q or "computer" in q or "go to sleep" in q or q.strip() == "sleep"):
            return {"intent": "system_control", "entities": {"action": "sleep"}, "response": "Entering sleep state."}

        # 14. Weather
        if "weather" in q or "temperature" in q:
            city = cfg.get("skills", "weather_city", "Karachi")
            m = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", q)
            if m:
                city = m.group(1).strip()
            return {"intent": "weather", "entities": {"city": city}, "response": f"Checking weather for {city}."}

        # 15. Contextual Pronouns (e.g. "close it")
        if q in ["close it", "close that", "kill it"] and self._last_opened_app:
            return {"intent": "close_app", "entities": {"app": self._last_opened_app}, "response": f"Closing {self._last_opened_app}."}

        return None

    def _semantic_fallback(self, query: str) -> dict:
        q = query.lower().strip()

        # Direct search query keywords
        if q.startswith("search ") or q.startswith("google ") or q.startswith("look up ") or q.startswith("find "):
            term = re.sub(r"^(?:search|google|look up|find)\s+(?:for\s+)?", "", q).strip()
            return {"intent": "search_web", "entities": {"query": term}, "response": f"Searching for {term}."}

        # Direct Q&A detection
        qa_starters = ["what is", "what are", "who is", "who was", "how to", "how does", "why is", "tell me about", "explain", "capital of"]
        if any(q.startswith(s) for s in qa_starters):
            return {"intent": "search_web", "entities": {"query": query}, "response": f"Looking into that for you, sir."}

        # Roman Urdu conversational chitchat personalized for Ahmad
        if any(w in q for w in ["awaz aa rahi hai", "awaz aa rhy hai", "meri awaz", "can you hear me", "sun rahe ho", "sun rhy ho"]):
            return {"intent": "chat", "entities": {}, "response": "Haan Ahmad, aapki awaz bilkul saaf aa rahi hai. Farmaiye main aapki kya madad kar sakta hoon?"}

        if any(w in q for w in ["kaise ho", "kya hal hai", "kese ho", "kaisay ho"]):
            return {"intent": "chat", "entities": {}, "response": "Main bilkul theek hoon Ahmad! Aapka loyal AI assistant all systems ready ke sath hazir hai."}

        if any(w in q for w in ["kya kar rahe ho", "kya kr rhy ho", "what are you doing"]):
            return {"intent": "chat", "entities": {}, "response": "Ahmad, main aapke commands ka intezar kar raha hoon. Bas aapka hukum chahiye."}

        if any(w in q for w in ["shukriya", "bohot shukriya", "dhanwad"]):
            return {"intent": "chat", "entities": {}, "response": "Hamesha aapke liye hazir hoon Ahmad!"}

        # Conversational greetings & personality
        greetings = {
            "hello": "Hello Ahmad. How may I assist you today?",
            "hi": "Greetings Ahmad. Systems are running smoothly.",
            "how are you": "I am fully operational and ready at your command, Ahmad.",
            "who are you": "I am JARVIS, your personal intelligent desktop assistant.",
            "thank you": "Always a pleasure to serve, Ahmad.",
            "thanks": "You're welcome, Ahmad.",
            "good morning": "Good morning Ahmad. All core diagnostics are green.",
            "good night": "Good night Ahmad. Powering down non-essential loops."
        }
        for key, reply in greetings.items():
            if key in q:
                return {"intent": "chat", "entities": {}, "response": reply}

        # Default fallback to quick search
        return {"intent": "search_web", "entities": {"query": query}, "response": f"Checking information for: '{query}'."}


_nlp_instance = None

def get_nlp() -> NLPEngine:
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPEngine()
    return _nlp_instance
