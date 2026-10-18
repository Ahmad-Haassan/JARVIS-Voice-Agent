"""
JARVIS Mobile Remote Server — FastAPI backend for iPhone & Mobile Web HUD.
"""
import os
import sys
import time
import socket
import psutil
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from core.utils.logger import get_logger
from core.ai.nlp_engine import get_nlp
from core.ai.command_router import get_router
from core.skills.system_control import get_system_control
from core.skills.camera import get_camera

logger = get_logger("server")
app = FastAPI(title="JARVIS Mobile Remote")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    text: str

def get_local_ip():
    """Detects the PC's Wi-Fi / Local Network IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.post("/api/command")
async def execute_command(req: CommandRequest):
    text = req.text.strip()
    logger.info(f"Mobile Remote Command received: '{text}'")

    nlp = get_nlp()
    router = get_router()

    nlp_result = nlp.process(text)
    intent = nlp_result.get("intent", "chat")
    entities = nlp_result.get("entities") or {}
    spoken_resp = nlp_result.get("response", "")

    exec_result = router.route({
        "intent": intent,
        "entities": entities,
        "response": spoken_resp
    })

    final_resp = exec_result.response or spoken_resp or "Command executed."
    
    # If screenshot or camera was requested
    screenshot_url = None
    camera_url = None
    action_type = entities.get("action", "")
    if intent == "system_control" and action_type == "screenshot":
        screenshot_url = "/api/screenshot"
    elif intent == "camera":
        camera_url = "/api/camera/stream"

    return {
        "success": exec_result.success,
        "response": final_resp,
        "intent": intent,
        "action": action_type,
        "screenshot_url": screenshot_url,
        "camera_url": camera_url
    }

@app.get("/api/status")
async def get_status():
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        battery_info = psutil.sensors_battery()
        battery = int(battery_info.percent) if battery_info else None
        return {
            "status": "online",
            "cpu": cpu,
            "ram": ram,
            "battery": battery
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/screenshot")
async def get_screenshot():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    path = os.path.join(data_dir, "screenshot.png")
    
    # If fresh screenshot exists (taken within last 5 seconds), serve it immediately
    if os.path.exists(path) and (time.time() - os.path.getmtime(path) < 5.0):
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    sys_ctrl = get_system_control()
    fresh_path = sys_ctrl.take_screenshot()
    if fresh_path and os.path.exists(fresh_path):
        return FileResponse(fresh_path, media_type="image/png", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    elif os.path.exists(path):
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"error": "Failed to capture screenshot"}

@app.get("/api/camera/stream")
def camera_stream():
    """Live MJPEG video stream from the computer's webcam."""
    cam = get_camera()
    return StreamingResponse(
        cam.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/snapshot")
def camera_snapshot():
    """Captures and returns a single photo from the PC camera."""
    cam = get_camera()
    path = cam.capture_snapshot()
    if path and os.path.exists(path):
        return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"error": "Failed to capture camera snapshot"}

@app.post("/api/voice")
async def process_voice_audio(audio: UploadFile = File(...)):
    """Receives voice audio from mobile, transcribes via Google STT, and executes command."""
    try:
        import speech_recognition as sr
        import tempfile
        
        contents = await audio.read()
        suffix = os.path.splitext(audio.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(contents)
            tmp_audio_path = tf.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_audio_path) as source:
            recorded = recognizer.record(source)
            text = recognizer.recognize_google(recorded)

        try:
            os.remove(tmp_audio_path)
        except Exception:
            pass

        logger.info(f"Mobile voice transcribed: '{text}'")
        return await execute_command(CommandRequest(text=text))
    except Exception as e:
        logger.warning(f"Voice upload processing error: {e}")
        return {"success": False, "response": f"Voice transcription error: {e}"}

def print_banner(host_ip, port):
    url = f"http://{host_ip}:{port}"
    print("\n" + "=" * 60)
    print("   [+] JARVIS MOBILE REMOTE SERVER IS ACTIVE!")
    print("=" * 60)
    print(f"\n>>> OPEN THIS URL ON YOUR IPHONE (Safari/Chrome):")
    print(f"    {url}\n")
    print("    Make sure your iPhone is connected to the same Wi-Fi!\n")

    # Generate QR Code in terminal
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        print("[*] SCAN THIS QR CODE WITH YOUR IPHONE CAMERA:")
        qr.print_ascii(invert=True)
    except Exception:
        pass
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import uvicorn
    local_ip = get_local_ip()
    port = 8000
    print_banner(local_ip, port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
