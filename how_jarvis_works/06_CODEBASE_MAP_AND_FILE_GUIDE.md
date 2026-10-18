# Chapter 6: Codebase Map & File Guide

This chapter provides a complete file-by-file inventory of the entire JARVIS repository. If someone points to any file or asks where a specific feature is implemented, use this guide.

---

## 1. Directory Tree Overview

```
jarvis/
├── core/
│   ├── ai/
│   │   ├── nlp_engine.py           # Dual-Brain NLP: Gemini API + Local Semantic Parser
│   │   └── command_router.py       # Central Intent Router & Skill Dispatcher
│   ├── skills/
│   │   ├── system_control.py       # Win32 OS API, App Launch (-n), Volume, Work Mode
│   │   ├── file_manager.py         # Natural Language Folder/File Resolver (depth 3)
│   │   ├── computer_agent.py       # PyAutoGUI mouse/keyboard takeover & Stonic AI
│   │   ├── camera.py               # OpenCV webcam MJPEG stream & snapshot capture
│   │   ├── whatsapp.py             # WhatsApp Web automated messaging
│   │   ├── web_search.py           # DuckDuckGo/Google search & YouTube playback
│   │   ├── weather.py              # Live weather retrieval via wttr.in / OpenWeather
│   │   └── timer_alarm.py          # Asynchronous countdown timers & alarms
│   ├── voice/
│   │   ├── stt.py                  # Speech-to-Text (Google Speech API & Faster-Whisper)
│   │   ├── tts.py                  # Text-to-Speech (pyttsx3 SAPI5 offline engine)
│   │   └── wake_word.py            # Offline wake-word detection ("jarvis") via Vosk
│   └── utils/
│       ├── config.py               # Configuration loader & persistent JSON manager
│       ├── logger.py               # Central colored logging system with rotation
│       └── inject_prompt.ps1       # COM WScript.Shell prompt injection fallback script
├── gui/
│   └── main_window.py              # PyQt6 Desktop HUD (Arc Reactor, chat, quick actions)
├── web/
│   └── index.html                  # Mobile Web HUD (Speak Mode, Text Mode, Touchpad)
├── config.json                     # System configuration (wake word, models, paths)
├── main.py                         # Desktop App Entrypoint (launches PyQt6 GUI)
├── server.py                       # Mobile Remote Server (FastAPI on 0.0.0.0:8000)
├── setup_autostart_mobile.bat      # Registers silent mobile server into Windows Startup
├── remove_autostart_mobile.bat     # Removes mobile server from Windows Startup
├── start_mobile_silent.vbs         # WScript.Shell launcher (Window Style 0 - Hidden)
├── start_mobile_silent.bat         # Silent execution script (pythonw.exe server.py)
├── stop_mobile.bat                 # Process killer for background server
├── requirements.txt                # Python package dependencies
└── README.md                       # Project documentation
```

---

## 2. File-by-File Technical Deep Dive

### 🧠 Cognitive & Routing Layer
- **[`core/ai/nlp_engine.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/ai/nlp_engine.py)**:
  - Class: `NLPEngine`
  - Key Methods:
    - `process(query: str) -> dict`: Main cognitive entry point. Normalizes text, matches regex rules, or calls Gemini.
    - `_semantic_fallback(query: str) -> dict`: Fallback rule-based matching when offline or unconfigured.
    - `_init_gemini()`: Initializes Google Generative AI client.
- **[`core/ai/command_router.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/ai/command_router.py)**:
  - Class: `CommandRouter`
  - Key Method:
    - `route(command: dict) -> CommandResult`: Maps `intent` (`open_in`, `volume_control`, `camera`, `work_mode`) to execution skills.

---

### ⚡ Execution & System Skills
- **[`core/skills/system_control.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/skills/system_control.py)**:
  - Class: `SystemControl`
  - Key Methods:
    - `open_with_app_and_prompt(app_name, target_path, prompt)`: Launches separate new window (`-n`), polls specifically for the folder title, attaches thread input via Win32, sends `Ctrl+L`, pastes prompt, and hits `Enter`.
    - `open_with_app(app_name, target_path)`: Opens file/folder in specified app with `-n` isolation.
    - `change_volume(delta)` / `set_volume(level)`: Direct hardware audio control via `pycaw`.
    - `take_screenshot() -> str`: Captures desktop via Win32 GDI or PowerShell Drawing API.
    - `system_power(action, pin)`: Handles `lock`, `unlock`, `sleep`, `restart`, `shutdown`.
    - `work_mode()`: Single-command developer workflow (launches IDE, Chrome, Terminal).
- **[`core/skills/file_manager.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/skills/file_manager.py)**:
  - Class: `FileManager`
  - Key Methods:
    - `resolve_folder(target: str) -> (path, name)`: Translates natural language names (`dsa`, `downloads`, `testing`) to absolute system paths by searching Desktop, Documents, Downloads, and User Home up to depth 3.
- **[`core/skills/computer_agent.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/skills/computer_agent.py)**:
  - Class: `ComputerAgent`
  - Key Methods:
    - `move_rel(dx, dy)` / `click(button)` / `scroll(amount)`: Virtual touchpad driver.
    - `workflow_ask_ai(prompt)`: Autonomous ChatGPT / web AI memo creation.
    - `workflow_snap_window(direction)`: Snaps active window left, right, or maximized.
- **[`core/skills/camera.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/skills/camera.py)**:
  - Class: `CameraSkill`
  - Key Methods:
    - `generate_mjpeg_stream()`: Yields multipart/x-mixed-replace JPEG frames from PC webcam for real-time video streaming.
    - `capture_snapshot() -> str`: Saves high-resolution snapshot to PC Desktop.

---

### 🎙️ Voice & Audio Subsystem
- **[`core/voice/stt.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/voice/stt.py)**:
  - Class: `STTEngine`
  - Method: `listen(timeout=7.0) -> str`: Records PC microphone audio and transcribes via Google Speech Recognition or Faster-Whisper.
- **[`core/voice/tts.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/voice/tts.py)**:
  - Class: `TTSEngine`
  - Method: `speak(text: str, block=False)`: Thread-safe offline speech synthesizer powered by `pyttsx3` (Windows SAPI5).
- **[`core/voice/wake_word.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/voice/wake_word.py)**:
  - Class: `WakeDetector`
  - Method: `_listen_loop()`: Continuous offline audio listener using the **Vosk** acoustic neural network for instant keyword wake (*"jarvis"*).

---

### 📱 Mobile Remote & Server
- **[`server.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/server.py)**:
  - High-performance FastAPI server running on `0.0.0.0:8000`.
  - Features `_NullStream` safe virtual stdio streams for silent background execution.
  - Endpoints:
    - `GET /`: Serves `web/index.html`.
    - `POST /api/command`: Executes incoming text or transcribed voice commands.
    - `POST /api/voice`: Accepts mobile audio blobs (`webm`/`mp4`/`wav`), converts via `ffmpeg`, and transcribes with Google STT.
    - `POST /api/voice/pc_listen`: Triggers the PC's physical microphone.
    - `GET /api/status`: Returns live CPU, RAM, and Battery percentages.
    - `GET /api/screenshot`: Serves high-res desktop screenshot image.
    - `GET /api/camera/stream`: Streams live webcam MJPEG video.
    - `POST /api/computer/mouse/move`: Virtual mouse touchpad tracking.
- **[`web/index.html`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/web/index.html)**:
  - Hardware-accelerated mobile web HUD.
  - Contains **Speak Mode**, **Text Mode**, and **Controls Mode**, plus the permanent sticky dual input bar.

---

### ⚙️ Startup Scripts
- **[`setup_autostart_mobile.bat`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/setup_autostart_mobile.bat)**: One-click registration of `JARVIS Mobile Server.lnk` into Windows Startup (`shell:startup`).
- **[`start_mobile_silent.vbs`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/start_mobile_silent.vbs)**: Invokes `start_mobile_silent.bat` with window style `0` (completely invisible/headless).
- **[`stop_mobile.bat`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/stop_mobile.bat)**: Kills background server instances using Windows `taskkill`.
