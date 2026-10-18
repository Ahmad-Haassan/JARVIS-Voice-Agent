# Chapter 7: Interview & Presentation Q&A Cheat Sheet

If someone asks you anything about JARVIS—in a job interview, university project defense, technical review, or casual demonstration—use the exact answers in this cheat sheet.

---

### Q1: What is JARVIS in simple terms?
**Answer:**
> *"JARVIS is a hybrid desktop and mobile personal AI operating system built for Windows 11. Unlike cloud-only assistants like Siri or Alexa that are restricted to mobile sandboxes, JARVIS has direct operating system privileges. It can manage real Windows applications, autonomously launch coding projects in isolated windows, inject prompts into AI IDEs, stream webcam video, control hardware volume, and allow complete wireless control from any smartphone over Wi-Fi without needing an App Store app."*

---

### Q2: What tech stack did you use to build it?
**Answer:**
> *"The backend is built in **Python 3.11+** utilizing **FastAPI** for asynchronous REST and streaming endpoints. The desktop GUI is built with **PyQt6**. Voice recognition uses **Google Speech Recognition** and offline **Vosk** neural networks for wake-word detection, while speech synthesis uses **pyttsx3** (SAPI5). Low-level Windows OS automation uses **Win32 APIs via ctypes** (`user32.dll`, `kernel32.dll`) and **pycaw** for audio endpoint control. Mobile remote control is built in responsive **HTML5/Vanilla CSS/JavaScript** using Web Speech API, MediaRecorder, and an **FFmpeg** audio transcoding pipeline."*

---

### Q3: How does JARVIS process natural language? Does it rely on a cloud LLM?
**Answer:**
> *"JARVIS uses a **Dual-Brain Hybrid Architecture**. For open-ended creative, analytical, or research questions, it leverages **Google Gemini 2.0 / 3.8 Flash**. However, for operating system controls, application launches, and system tasks, it uses a **Deterministic Semantic Regex Engine**. This ensures that system commands execute in under **5 milliseconds** with 100% deterministic reliability, zero cloud cost, and no risk of LLM hallucination."*

---

### Q4: Does JARVIS work completely offline?
**Answer:**
> *"Yes. The wake-word detector uses a local, offline **Vosk** acoustic neural network model. The offline semantic NLP engine handles all system tasks (window management, volume, launching apps, Antigravity IDE automation, locking/unlocking PC) without needing an internet connection. The cloud Gemini LLM is only invoked when internet is available and the user asks general-knowledge questions."*

---

### Q5: How does JARVIS autonomously open folders in Antigravity IDE and submit prompts?
**Answer:**
> *"It executes a 4-step automation pipeline:
> 1. It resolves the natural language folder name (e.g. `dsa` or `testing`) to an absolute path.
> 2. It launches `antigravity-ide.cmd` with the `-n` (`--new-window`) flag so the user's existing workspaces and open files remain completely untouched.
> 3. It polls Windows for the specific window title matching the folder name, and bypasses Windows 11 foreground lock using `AttachThreadInput` and `SetForegroundWindow`.
> 4. It clicks inside the editor canvas, sends `Ctrl + L` to focus the Agent chat panel, copies the prompt to the clipboard, pastes it with `Ctrl + V`, and presses `Enter`."*

---

### Q6: Why were existing windows closing before, and how did you solve it?
**Answer:**
> *"Electron-based editors (like VS Code and Antigravity IDE) default to replacing the workspace in the currently active frontmost window. Previously, Antigravity was invoked without the `-n` flag, which caused Electron to reuse and swap the frontmost window. Furthermore, the prompt injector had an early fallback matching `'Antigravity'`, which grabbed the user's active window before the new folder finished rendering. We solved this by strictly enforcing the `-n` (`--new-window`) flag and making the injector poll specifically for the exact target folder title."*

---

### Q7: How do you bypass the Windows 11 Foreground Lock?
**Answer:**
> *"Starting in Windows 10/11, Microsoft enforces `LockSetForegroundWindow`, preventing background processes from stealing focus. When a command arrives from a smartphone, JARVIS is a background process. To bypass this restriction:
> 1. We obtain the foreground window's thread ID and attach our current thread input to it using `user32.AttachThreadInput(cur_tid, fg_tid, True)`.
> 2. We simulate an `ALT` key tap using `user32.keybd_event` to trick Windows into allowing a foreground switch.
> 3. We call `ShowWindow(hwnd, 9)` and `SetForegroundWindow(hwnd)`.
> 4. We detach the thread input."*

---

### Q8: How does the mobile remote work without installing an iOS or Android app?
**Answer:**
> *"JARVIS hosts its own FastAPI web server on port `8000`. By querying a UDP socket connection to `8.8.8.8:80`, it detects the PC's local network IPv4 address (e.g., `192.168.0.115`). When you connect your phone to the same Wi-Fi network and open Safari or Chrome, it serves a responsive, hardware-accelerated web app with modern Web APIs (Web Speech, MediaRecorder, TouchEvents, SpeechSynthesis) that behaves just like a native mobile app."*

---

### Q9: How did you get the server to start silently with Windows without a black terminal popping up?
**Answer:**
> *"We implemented a silent execution chain:
> 1. A setup batch script installs a Windows shortcut (`JARVIS Mobile Server.lnk`) into the Windows Startup folder (`shell:startup`).
> 2. The shortcut targets a VBScript file (`start_mobile_silent.vbs`) that calls `WScript.Shell.Run "start_mobile_silent.bat", 0, False`. The `0` parameter instructs Windows to execute completely hidden with no console window.
> 3. The batch file runs `pythonw.exe server.py` (the windowless Python binary)."*

---

### Q10: Why was Python crashing when launched silently in the background?
**Answer:**
> *"When Python runs via `pythonw.exe` or headless VBScript, Windows sets standard I/O streams (`sys.stdout`, `sys.stderr`, `sys.stdin`) to `None`. ASGI servers like Uvicorn check `sys.stdout.isatty()`. In a headless environment, accessing `isatty()` on `None` throws an immediate `AttributeError` crash. We fixed this by implementing a custom `_NullStream` virtual class that safely stubs `write()`, `flush()`, and `isatty()` before any libraries are loaded."*

---

### Q11: How does voice and wake-word input work on iPhone Safari?
**Answer:**
> *"Apple's WebKit engine strictly blocks `window.webkitSpeechRecognition` on insecure (`http://`) IP origins to protect user privacy. JARVIS solves this elegantly with an automated dual-server pipeline:
> 1. On startup, `server.py` uses the `cryptography` library to automatically generate a self-signed SSL certificate with Subject Alternative Names (SAN) for localhost and the PC's Wi-Fi IP address.
> 2. It spins up a secure **HTTPS server on port 8443** alongside the standard HTTP server on port 8000.
> 3. When opened via `https://<ip>:8443`, iOS Safari marks the page as a Secure Context (`window.isSecureContext = true`), unlocking the microphone hardware, `webkitSpeechRecognition`, and continuous 'Jarvis' wake-word detection.
> 4. If the user accesses the plain HTTP port 8000, the HUD displays a 1-tap modal to switch to HTTPS or fall back to the PC room microphone."*

---

### Q12: How does JARVIS talk back through your phone?
**Answer:**
> *"When a command finishes executing on the PC, the server sends a JSON response back to the phone. The mobile web HUD passes the response text to the browser's built-in `window.speechSynthesis` engine using `SpeechSynthesisUtterance`. The phone speaks the confirmation aloud through its internal speakers."*

---

### Q13: How does the file manager resolve folders like 'dsa' or 'downloads'?
**Answer:**
> *"In `core/skills/file_manager.py`, the `resolve_folder` method uses a multi-tier search algorithm:
> 1. It checks common aliases (`downloads`, `documents`, `desktop`).
> 2. It checks direct path matches in Desktop, Documents, Downloads, and User Home.
> 3. If not found at root, it performs a recursive search up to 3 directory depths, skipping heavy folders like `node_modules` and `.git`.
> 4. It applies fuzzy matching via Python's `difflib.SequenceMatcher` with an 84% confidence threshold to match approximate names."*

---

### Q14: How does the virtual touchpad work from a phone?
**Answer:**
> *"The mobile webpage has a touch container that captures `touchmove` events. It calculates movement offsets `(dx, dy)` and throttles network transmissions to **40 Hz** to avoid network congestion. The coordinates are posted to `/api/computer/mouse/move`, where `pyautogui.moveRel(dx, dy)` translates them to real mouse cursor movements on Windows with zero perceived latency."*

---

### Q15: Is JARVIS private and secure?
**Answer:**
> *"Yes, significantly more private than commercial cloud assistants. All desktop commands, volume controls, camera streams, and touchpad coordinates remain strictly within your local home Wi-Fi network. No telemetry or ambient room audio is ever sent to any remote server."*

---

### Q16: How does hands-free 'Jarvis' wake-word activation work on mobile?
**Answer:**
> *"When enabled via the HUD toggle switch, the phone initializes a continuous SpeechRecognition instance with interim phrase matching. It listens continuously for 'Jarvis' (using phonetic regex to account for common speech engine interpretations like 'service' or 'travis').
> When detected:
> 1. An on-device Web Audio API synthesizer generates an authentic 2-tone Iron Man confirmation chime instantly with zero network latency.
> 2. The Holographic Arc Reactor Orb enters the glowing pulsating red 'listening' state.
> 3. It captures the subsequent spoken command (either in the same breath, e.g. 'Jarvis, open DSA folder in Antigravity', or two-step where JARVIS responds 'Yes, sir?' first).
> 4. To avoid audio feedback loops, acoustic echo cancellation temporarily suppresses speech recognition while the phone's speaker reads JARVIS's answer aloud."*

---

### Q17: What is 'Work Mode'?
**Answer:**
> *"Work Mode is a single-voice-command productivity routine. When you say 'Start work mode', JARVIS simultaneously launches your primary development IDE (Antigravity IDE), Google Chrome, and your Terminal, positioning you to begin coding immediately."*

---

### Q18: What was the most challenging technical hurdle in this project?
**Answer:**
> *"The hardest challenge was achieving reliable, non-destructive prompt injection into Antigravity IDE from a headless mobile server. We had to solve three interlocking low-level Windows issues simultaneously:
> 1. Forcing Electron to open an isolated workspace (`-n`) so active code was not replaced.
> 2. Bypassing Windows 11 foreground lock using Win32 thread input attachment (`AttachThreadInput`).
> 3. Preventing headless python crashes with `_NullStream` stdio virtualization.
> Once those were resolved, the system achieved 100% reliable autonomous code execution from a phone."*

---

### Q19: What is on the future roadmap for JARVIS?
**Answer:**
> *"The future roadmap includes:
> 1. Self-signed SSL certificate generation for out-of-the-box native HTTPS on local networks.
> 2. Local vision models (e.g. YOLO / LLaVA) for autonomous visual screen understanding.
> 3. Multi-agent subtask decomposition for multi-file software engineering tasks."*
