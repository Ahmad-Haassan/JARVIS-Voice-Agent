"""
JARVIS Mobile Remote Server — FastAPI backend for iPhone & Mobile Web HUD.
"""
import os
import sys
import socket
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
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
        return f.read()

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
    
    # If screenshot was requested
    screenshot_url = None
    action_type = entities.get("action", "")
    if intent == "system_control" and action_type == "screenshot":
        screenshot_url = "/api/screenshot"

    return {
        "success": exec_result.success,
        "response": final_resp,
        "intent": intent,
        "action": action_type,
        "screenshot_url": screenshot_url
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
    sys_ctrl = get_system_control()
    path = sys_ctrl.take_screenshot()
    if path and os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return {"error": "Failed to capture screenshot"}

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
