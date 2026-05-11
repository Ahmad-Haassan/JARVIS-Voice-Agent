# JARVIS — Supercharged PC Assistant

Jarvis is a premium, always-listening AI desktop assistant designed to provide deep OS integration, automated workflows, and high-accuracy voice control.

## 🌟 Key Features

- **🎤 Persistent Listening**: Say "Jarvis" once to activate. He stays active for multiple commands until you say "Go to sleep."
- **📁 Deep OS Integration**: Automatically scans and indexes all your installed apps (Chrome, VS Code, Figma, etc.) for instant voice launching.
- **📺 YouTube Automation**: Play any video directly. Say "Play lo-fi music on YouTube" and Jarvis searches and starts the video instantly.
- **💬 WhatsApp Desktop Automation**: Send messages to your contacts using the native WhatsApp Desktop app.
- **🧩 Smart Memory**: Jarvis learns your habits and stores preferences in a local memory system.
- **🌈 Cyber-Ring UI**: A dynamic, glassmorphic interface with pulsing animations that reflect Jarvis's state (Listening, Thinking, Idle).

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Windows 10/11**
- **Microphone**

### 2. Installation
1. Clone this repository.
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Add your **Gemini API Key** in `config.json`.

### 3. Usage
Run the main script:
```powershell
python main.py
```
1. **Login**: Use your password to access the assistant.
2. **Wake Up**: Say **"Jarvis"** to start the conversation.
3. **Commands**:
   - "Open WhatsApp"
   - "Play latest tech news on YouTube"
   - "Start work mode" (Opens Chrome, VS Code, Spotify, and WhatsApp)
   - "What's the weather in London?"
4. **Sleep**: Say **"Go to sleep"** to return to standby.

---

## 🛠️ Project Structure
- `core/`: Core engine (AI, Voice, Skills, Auth)
- `gui/`: Premium PyQt6 interface components
- `data/`: Local storage for logs, memory, and voice models
- `main.py`: Application entry point

---

## 🛡️ Security & Privacy
- **Offline Wake Word**: Uses Vosk for local, private wake-word detection.
- **Offline STT**: Uses Whisper (Faster-Whisper) for local speech-to-text.
- **Encrypted Auth**: Passwords are hashed using bcrypt.

---

## 📜 License
This project is for educational and personal use.
