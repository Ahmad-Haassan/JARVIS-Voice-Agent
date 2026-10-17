<div align="center">

# 🎙️ JARVIS AI — Supercharged Desktop Voice Assistant
### *Offline Wake-Word Detection, Local Whisper Transcription & Deep Windows OS Automation*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Vosk](https://img.shields.io/badge/Vosk-Offline_Wake_Word-FF6F00?style=for-the-badge)](https://alphacephei.com/vosk/)
[![Faster-Whisper](https://img.shields.io/badge/Faster_Whisper-Local_STT-blue?style=for-the-badge)](https://github.com/SYSTRAN/faster-whisper)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6_Cyber_HUD-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](./LICENSE)

<br />

<p align="center">
  JARVIS is an always-listening, privacy-first personal desktop AI assistant built in Python. Designed with a dual-stage speech pipeline (lightweight offline wake-word + local quantized Whisper STT), JARVIS provides hands-free OS control, instant app launching, YouTube media automation, and system diagnostics through a glowing cyberpunk PyQt6 interface.
</p>

[**Explore Capabilities**](#-core-capabilities) • [**Architecture**](#-speech--automation-pipeline) • [**Command Glossary**](#-supported-voice-commands) • [**Setup Guide**](#-setup--installation)

<br />

![JARVIS Voice Assistant Cyber HUD](./docs/jarvis_hud_showcase.jpg)

</div>

---

## 🌟 Core Capabilities

### 1. 🛡️ Dual-Stage Speech Engine (100% Private & Offline)
* **Stage 1 (Vosk Wake-Word)**: Continuously listens for the `"Jarvis"` activation key using an ultra-low CPU offline acoustic model. Zero cloud streaming while idling.
* **Stage 2 (Faster-Whisper STT)**: Once triggered, speech is transcribed locally via quantized Whisper (`large-v3` or `base.en`), providing high-accuracy transcription even in noisy environments without cloud subscription costs.

### 2. ⚡ Deep Windows OS Automation
* **Smart App Indexer**: Scans and indexes all installed Windows applications (VS Code, Chrome, Spotify, Figma) for instant zero-latency voice launching.
* **"Work Mode" Routine**: A single phrase (*"Start work mode"*) simultaneously opens your development environment: VS Code, terminal windows, Chrome documentation tabs, and background audio.
* **Native WhatsApp Desktop Routing**: Prepares and sends messages through native Windows messaging apps.

### 3. 🌐 Media & Web Execution
* **Instant YouTube Automation**: Commands like *"Play lo-fi music on YouTube"* automatically query the YouTube search engine and launch playback instantly.
* **System Telemetry & Diagnostics**: Query CPU load, memory utilization, network latency, and weather reports through voice.

### 4. 🌌 Cyber-Ring Glassmorphic HUD
* **Dynamic Waveform Visualization**: Visual ring pulses in sync with real-time mic amplitude, giving clear visual cues for *Listening*, *Thinking*, *Speaking*, and *Standby*.
* **Minimal Resource Footprint**: Built with hardware-accelerated PyQt6 shaders that consume less than 3% background CPU.

---

## 🏗️ Speech & Automation Pipeline

```text
[ Microphone Stream ]
         │
         ▼
[ Vosk Lightweight Offline Engine ] ──► (Waiting for "Jarvis"...)
         │ (Wake Word Detected!)
         ▼
[ Cyber-Ring HUD Activates ("Listening...") ]
         │
         ▼
[ Faster-Whisper Local Transcription ]
         │
         ▼
[ NLP Intent Matcher & Rule Engine ]
         │
    ┌────┴───────────────────────────┐
    ▼                                ▼
[ OS & Desktop Automation ]   [ Web & Media Automation ]
(Launch VS Code, System Info) (YouTube Streams, Searches)
         │                                │
         └──────────────┬─────────────────┘
                        ▼
            [ Natural Voice Response & UI Log ]
```

---

## 🗣️ Supported Voice Commands

| Category | Example Voice Command | Action Executed |
| :--- | :--- | :--- |
| **Workspace** | *"Start work mode"* | Opens VS Code, Terminal, Spotify, and Chrome |
| **Media** | *"Play synthwave on YouTube"* | Finds & plays top-ranked track directly |
| **System** | *"System diagnostics"* | Reads current CPU %, RAM usage, and battery |
| **Communication** | *"Open WhatsApp and message Alex"* | Dispatches chat window with pre-filled prompt |
| **Standby** | *"Go to sleep"* | Silences listening and minimizes to system tray |

---

## 🛠️ Tech Stack & Dependencies

* **Language**: Python 3.10+
* **Speech-to-Text**: Faster-Whisper, Vosk Speech Recognition
* **Text-to-Speech**: pyttsx3 / Edge-TTS
* **Desktop GUI**: PyQt6 (QML & Shader support)
* **OS Interactivity**: `pyautogui`, `psutil`, `subprocess`

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ahmad-Haassan/JARVIS-Voice-Agent.git
cd JARVIS-Voice-Agent
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Download Offline Acoustic Model
Download the small English model from [Vosk Models](https://alphacephei.com/vosk/models) (e.g., `vosk-model-small-en-us-0.15`) and place it inside `./model/`.

### 4. Run JARVIS
```bash
python main.py
```
Say **"Jarvis"** to wake the assistant, then give any command!

---

## 📬 Connect & Author

- **Developer**: Ahmad Hassan
- **GitHub**: [@Ahmad-Haassan](https://github.com/Ahmad-Haassan)
- **Email**: [ahmad.hassan.dev@gmail.com](mailto:ahmad.hassan.dev@gmail.com)

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).
