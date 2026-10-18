# Chapter 3: Natural Language Processing & Decision Engine

## 1. The Dual-Brain Cognitive Architecture

Many AI assistants make the fatal mistake of relying 100% on cloud Large Language Models (LLMs) for every trivial interaction. This introduces high latency (1–3 seconds), high API costs, dependency on an active internet connection, and the dangerous risk of **LLM hallucination** when executing system commands.

JARVIS solves this problem using a **Dual-Brain Hybrid Cognitive Architecture**:

```
[ Incoming User Command ]
           │
           ▼
┌───────────────────────────────────────┐
│       Pre-Processing & Cleaning       │
│  - Lowercase & whitespace trimming    │
│  - Typo correction (forlder -> folder)│
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│  Tier 1: Deterministic Semantic NLP   │
│  - Intent matching via optimized regex│
│  - Exact entity extraction            │
│  - Execution latency: < 5ms           │
└───────┬───────────────────────┬───────┘
        │ Match Found           │ No Match (General Q&A)
        ▼                       ▼
┌───────────────┐       ┌────────────────────────┐
│ Command Router│       │ Tier 2: Cloud LLM      │
│ (System Skill)│       │ (Google Gemini 2.0/3.8)│
└───────────────┘       └────────────────────────┘
```

1. **Tier 1: Deterministic Semantic NLP (Offline & Zero-Latency)**:
   - Covers all operating system controls, application launches, volume changes, media playback, folder resolution, and window commands.
   - Guaranteed deterministic execution in **under 5 milliseconds** with zero cloud calls.
2. **Tier 2: Google Gemini Generative Intelligence (Cloud Reasoning)**:
   - Activated when the user asks open-ended, creative, or analytical questions (e.g., *"What is the difference between TCP and UDP?"*, *"Write a poem about space exploration"*).
   - Uses structured system prompts instructing Gemini to output either conversational text or a strict JSON schema.

---

## 2. Complete Intent Catalog

The table below lists all intents recognized by `core/ai/nlp_engine.py` and dispatched by `core/ai/command_router.py`:

| Intent | Sample User Utterances | Entities Extracted | Handled By |
|---|---|---|---|
| **`open_in`** | *"Open dsa folder in antigravity and solve task"*, *"Open testing in vscode, write 5 lines"* | `target`, `app`, `prompt` | `system_control.open_with_app_and_prompt` |
| **`open_app`** | *"Open Google Chrome"*, *"Launch paint"*, *"Open calculator"* | `app` | `system_control.open_app` |
| **`open_folder`** | *"Open my downloads"*, *"Open dsa folder"*, *"Show documents"* | `folder` | `file_manager.open_folder` |
| **`open_file`** | *"Open resume.pdf"*, *"Open notes.txt"* | `file` | `file_manager.open_file` |
| **`volume_control`** | *"Volume up"*, *"Lower volume"*, *"Mute"*, *"Set volume to 75%"* | `action` (`up`/`down`/`mute`/`set`), `level` | `system_control.change_volume` / `set_volume` |
| **`media_control`** | *"Pause music"*, *"Play"*, *"Next track"*, *"Skip song"* | `action` (`play_pause`/`next`/`prev`) | `system_control.media_play_pause` |
| **`window_control`**| *"Minimize all"*, *"Show desktop"*, *"What windows are open"* | `action` (`minimize_all`/`list`/`focus`) | `system_control.minimize_all` / `focus_window` |
| **`system_control`**| *"Take screenshot"*, *"Lock PC"*, *"Unlock PC"*, *"Go to sleep"* | `action` (`screenshot`/`lock`/`unlock`/`sleep`) | `system_control.system_power` / `take_screenshot` |
| **`camera`** | *"Open camera"*, *"Take photo"*, *"Webcam stream"* | `action` (`stream`/`snapshot`) | `camera.capture_snapshot` |
| **`work_mode`** | *"Start work mode"*, *"Focus mode"* | None | `system_control.work_mode` (Launches IDE, Chrome, Terminal) |
| **`computer_agent`**| *"Ask AI to explain quantum physics"*, *"Snap left"* | `action`, `direction`, `prompt`, `content` | `computer_agent.py` (Stonic AI Workflows) |
| **`youtube_play`** | *"Play lo-fi hip hop on YouTube"* | `query` | `web_search.play_youtube` |
| **`send_whatsapp`** | *"Send WhatsApp message to John hello"* | `contact`, `message` | `whatsapp.send_message` |
| **`weather`** | *"Weather in London"*, *"What's the temperature"* | `city` | `weather.get_weather` |
| **`close_app`** | *"Close it"*, *"Kill Chrome"* | `app` (or contextual pronoun memory) | `system_control.close_app` |

---

## 3. Typo Tolerance & Natural Language Flexibility

Real human voice and mobile typing is messy. People make typos, use punctuation irregularly, or insert conversational filler words. The NLP engine incorporates several layers of heuristic tolerance:

### A. Typo Normalization
- Target keywords automatically strip spelling anomalies:
  ```python
  clean_target = re.sub(r"\s+(?:folder|forlder|fldr|directory|dir|file)$", "", raw_target, flags=re.IGNORECASE).strip()
  ```
  If a user speaks or types *"Open testing forlder in antigravity"*, the engine normalizes `testing forlder` directly to `testing`.

### B. Flexible Separator Matching
Human speech and mobile typing often separate the app from the prompt with a comma, colon, quote, or phrase:
- *"Open testing in antigravity, write a poem"* (comma separated)
- *"Open testing in antigravity and give prompt write a poem"* (phrase separated)
- *"Open testing in antigravity \"write a poem\""* (quote separated)

The NLP regex dynamically matches across all these separator patterns:
```python
r"^(?:open|launch)\s+(?:the\s+|my\s+)?(.+?)\s+(?:in|with|using)\s+([a-zA-Z0-9_\-\s]+?)(?:[\,\;\:\-]\s*|\s+(?:and\s+give\s+prompt|and\s+|then\s+)|\s*[\"\'\“\”])\s*(.+)$"
```

### C. Contextual Pronoun Memory
If you tell JARVIS *"Open Chrome"*, JARVIS records `_last_opened_app = "chrome"`.
If you subsequently say *"Close it"* or *"Kill that"*, the engine detects the pronoun, retrieves the stored context, and terminates Google Chrome without requiring you to repeat the app name.
