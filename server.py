"""
JARVIS Mobile Remote Server — FastAPI backend for iPhone & Mobile Web HUD.
"""
import os
import sys
import time
import socket
import asyncio
import psutil
import json
import re
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

# Ensure project root in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Ensure safe stdio streams even when run silently with pythonw.exe or detached background
class _NullStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
    def isatty(self): return False
    def fileno(self): return -1
    def read(self, *args, **kwargs): return ""
    def readline(self, *args, **kwargs): return ""

_is_silent = (sys.stdout is None)
if sys.stdout is None:
    sys.stdout = _NullStream()
    sys.__stdout__ = sys.stdout
else:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = _NullStream()
    sys.__stderr__ = sys.stderr
if sys.stdin is None:
    sys.stdin = _NullStream()
    sys.__stdin__ = sys.stdin

from core.utils.logger import get_logger
from core.ai.nlp_engine import get_nlp
from core.ai.command_router import get_router
from core.skills.system_control import get_system_control
from core.skills.camera import get_camera
from core.skills.computer_agent import get_computer_agent

logger = get_logger("server")
app = FastAPI(title="GHOST Mobile Remote")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    text: str
    device_id: Optional[str] = None

class MouseMoveRequest(BaseModel):
    dx: int
    dy: int
    device_id: Optional[str] = None

class MouseClickRequest(BaseModel):
    button: str = "left"
    clicks: int = 1
    device_id: Optional[str] = None

class MouseScrollRequest(BaseModel):
    amount: int = -300
    device_id: Optional[str] = None

class KeyboardTypeRequest(BaseModel):
    text: str
    device_id: Optional[str] = None

class WorkflowRequest(BaseModel):
    action: str
    param: str = ""
    device_id: Optional[str] = None

class DevicePingRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = "Mobile Device"
    user_agent: Optional[str] = ""
    token: Optional[str] = None

class DeviceActionRequest(BaseModel):
    device_id: str

class VerifyTokenRequest(BaseModel):
    token: str
    device_id: str
    device_name: Optional[str] = "Mobile Device"
    user_agent: Optional[str] = ""

# ==========================================
# CONNECTED DEVICES & ACCESS CONTROL SYSTEM
# ==========================================
DEVICES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "devices.json")
AUTH_TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pairing_token.txt")

def get_or_create_pairing_token() -> str:
    if os.path.exists(AUTH_TOKEN_FILE):
        try:
            with open(AUTH_TOKEN_FILE, "r", encoding="utf-8") as f:
                t = f.read().strip()
                if t:
                    return t
        except Exception:
            pass
    import random
    new_t = f"{random.randint(100000, 999999)}"
    try:
        os.makedirs(os.path.dirname(AUTH_TOKEN_FILE), exist_ok=True)
        with open(AUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(new_t)
    except Exception:
        pass
    return new_t

PAIRING_TOKEN = get_or_create_pairing_token()

def load_devices() -> dict:
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_devices(data: dict):
    try:
        os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save devices: {e}")

def get_client_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "Unknown"

def is_device_authorized(device_id: Optional[str] = None, token: Optional[str] = None, client_ip: Optional[str] = None) -> bool:
    # 1. Local requests directly from the PC are always authorized
    if client_ip in ("127.0.0.1", "::1", "localhost", "Unknown"):
        return True
    
    # 2. Token match
    if token and token.strip() == PAIRING_TOKEN:
        return True
        
    # 3. Known and authenticated device in devices.json
    if device_id:
        devices = load_devices()
        dev = devices.get(device_id)
        if dev and not dev.get("is_blocked", False) and dev.get("is_authenticated", False):
            return True

    return False

def check_device_allowed(device_id: Optional[str] = None) -> bool:
    if not device_id:
        return True
    devices = load_devices()
    dev = devices.get(device_id)
    if dev and dev.get("is_blocked"):
        return False
    return True

@app.get("/api/auth/info")
async def get_auth_info(request: Request):
    """Returns pairing token for the host PC display."""
    return {
        "pairing_token": PAIRING_TOKEN,
        "gateway_url": "https://backpack-vanity-poser.ngrok-free.dev"
    }

@app.post("/api/auth/verify")
async def verify_pairing(req: VerifyTokenRequest, request: Request):
    """Verifies a pairing PIN/token entered by a new phone or client."""
    if req.token.strip() == PAIRING_TOKEN:
        devices = load_devices()
        dev_id = req.device_id.strip()
        client_ip = get_client_ip(request)
        ua = req.user_agent or request.headers.get("user-agent", "")
        now_ts = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        devices[dev_id] = {
            "device_id": dev_id,
            "device_name": req.device_name or "Paired Device",
            "ip": client_ip,
            "user_agent": ua,
            "first_seen": now_str,
            "last_seen": now_ts,
            "is_blocked": False,
            "is_authenticated": True
        }
        save_devices(devices)
        logger.info(f"New client authenticated successfully: {dev_id} ({req.device_name})")
        return {"success": True, "message": "Paired successfully."}
    return {"success": False, "message": "Invalid pairing PIN or token."}

@app.post("/api/devices/ping")
async def ping_device(req: DevicePingRequest, request: Request):
    dev_id = req.device_id.strip()
    client_ip = get_client_ip(request)

    if not is_device_authorized(dev_id, req.token, client_ip):
        return {
            "allowed": False,
            "status": "unauthorized",
            "message": "Device not paired. Pairing token required."
        }
    
    if not dev_id:
        return {"allowed": True, "status": "ok"}
    
    devices = load_devices()
    now_ts = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ua = req.user_agent or request.headers.get("user-agent", "")

    if dev_id in devices and devices[dev_id].get("is_blocked"):
        return {
            "allowed": False,
            "status": "blocked",
            "message": "Access revoked by PC administrator."
        }
    
    if dev_id not in devices:
        devices[dev_id] = {
            "device_id": dev_id,
            "device_name": req.device_name or "Mobile Device",
            "ip": client_ip,
            "user_agent": ua,
            "first_seen": now_str,
            "last_seen": now_ts,
            "is_blocked": False,
            "is_authenticated": True
        }
    else:
        devices[dev_id]["last_seen"] = now_ts
        devices[dev_id]["ip"] = client_ip
        devices[dev_id]["is_authenticated"] = True
        if req.device_name:
            devices[dev_id]["device_name"] = req.device_name
        if ua:
            devices[dev_id]["user_agent"] = ua

    save_devices(devices)
    return {"allowed": True, "status": "online", "device_id": dev_id}

@app.get("/api/devices")
async def get_devices(request: Request, device_id: Optional[str] = None, token: Optional[str] = None):
    client_ip = get_client_ip(request)
    req_token = token or request.headers.get("x-pairing-token")
    if not is_device_authorized(device_id, req_token, client_ip):
        raise HTTPException(status_code=401, detail="Unauthorized. Pairing token required.")

    devices = load_devices()
    now_ts = time.time()
    device_list = []
    online_count = 0
    blocked_count = 0

    for dev_id, info in devices.items():
        last_seen = info.get("last_seen", 0)
        is_blocked = info.get("is_blocked", False)
        is_online = (now_ts - last_seen < 35) and not is_blocked
        if is_online:
            online_count += 1
        if is_blocked:
            blocked_count += 1
            
        device_list.append({
            "device_id": dev_id,
            "device_name": info.get("device_name", "Remote Device"),
            "ip": info.get("ip", "Unknown"),
            "user_agent": info.get("user_agent", ""),
            "first_seen": info.get("first_seen", "Unknown"),
            "last_seen_seconds_ago": int(now_ts - last_seen),
            "is_online": is_online,
            "is_blocked": is_blocked
        })

    device_list.sort(key=lambda x: (x["is_blocked"], not x["is_online"], x["last_seen_seconds_ago"]))

    return {
        "success": True,
        "total_connected": online_count,
        "total_registered": len(device_list),
        "total_blocked": blocked_count,
        "devices": device_list
    }

@app.post("/api/devices/delete")
async def delete_device(req: DeviceActionRequest):
    dev_id = req.device_id.strip()
    devices = load_devices()
    if dev_id in devices:
        devices[dev_id]["is_blocked"] = True
        devices[dev_id]["blocked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_devices(devices)
        logger.warning(f"Device revoked & blocked: {dev_id} ({devices[dev_id].get('device_name')})")
        return {"success": True, "message": f"Device access revoked and disconnected."}
    return {"success": False, "message": "Device not found."}

@app.post("/api/devices/unblock")
async def unblock_device(req: DeviceActionRequest):
    dev_id = req.device_id.strip()
    devices = load_devices()
    if dev_id in devices:
        devices[dev_id]["is_blocked"] = False
        save_devices(devices)
        logger.info(f"Device unblocked: {dev_id}")
        return {"success": True, "message": f"Device unblocked successfully."}
    return {"success": False, "message": "Device not found."}

@app.get("/api/tunnel_info")
def get_tunnel_info():
    cf_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf.log")
    tunnel_url = None
    if os.path.exists(cf_log_path):
        try:
            with open(cf_log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
                if matches:
                    tunnel_url = matches[-1]
        except Exception:
            pass
    return {
        "tunnel_url": tunnel_url,
        "local_ip": get_local_ip()
    }

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

COMMAND_TIMEOUT_SECONDS = 30

@app.post("/api/command")
async def execute_command(req: CommandRequest, request: Request):
    """Runs the (blocking) command pipeline in a worker thread so a slow or hung
    PC action can never freeze the server's event loop."""
    client_ip = get_client_ip(request)
    req_token = request.headers.get("x-pairing-token")
    if not is_device_authorized(req.device_id, req_token, client_ip):
        raise HTTPException(status_code=401, detail="Unauthorized. Device pairing required.")
    if req.device_id and not check_device_allowed(req.device_id):
        raise HTTPException(status_code=403, detail="Device access has been revoked.")
    text = req.text.strip()
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_execute_command_sync, text),
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s: '{text}'")
        return {"success": False, "response": "That command is taking too long on the PC.", "intent": "timeout",
                "action": "", "screenshot_url": None, "camera_url": None}
    except Exception as e:
        logger.error(f"Command error: {e}")
        return {"success": False, "response": f"Command error: {e}", "intent": "error",
                "action": "", "screenshot_url": None, "camera_url": None}

def _execute_command_sync(text: str):
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
    
    # If screenshot, screen_info, or camera was requested
    screenshot_url = None
    camera_url = None
    action_type = entities.get("action", "")
    if (intent == "system_control" and action_type == "screenshot") or intent == "screen_info":
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

class SettingsRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    weather_city: Optional[str] = None

@app.get("/api/settings")
def get_settings():
    from core.utils import config as cfg
    key = cfg.get("ai", "gemini_api_key", "")
    return {
        "gemini_configured": bool(key and not key.startswith("AQ.")),
        "weather_city": cfg.get("skills", "weather_city", "Karachi"),
        "wake_word": cfg.get("app", "wake_word", "jarvis")
    }

@app.post("/api/settings")
def update_settings(req: SettingsRequest):
    from core.utils import config as cfg
    if req.gemini_api_key is not None:
        cfg.set("ai", "gemini_api_key", req.gemini_api_key.strip())
        from core.ai.nlp_engine import get_nlp
        get_nlp()._init_gemini()
    if req.weather_city is not None:
        cfg.set("skills", "weather_city", req.weather_city.strip())
    return {"success": True, "message": "Settings updated successfully."}

@app.get("/api/status")
async def get_status(request: Request, device_id: Optional[str] = None, token: Optional[str] = None):
    client_ip = get_client_ip(request)
    req_token = token or request.headers.get("x-pairing-token")
    if not is_device_authorized(device_id, req_token, client_ip):
        return {"status": "unpaired", "cpu": 0, "ram": 0, "battery": None}
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
    try:
        fresh_path = await asyncio.wait_for(asyncio.to_thread(sys_ctrl.take_screenshot), timeout=15)
    except Exception:
        fresh_path = None
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

def generate_screen_mjpeg_stream():
    """Streams real-time desktop screen with hardware-scaled StretchBlt and glowing mouse cursor.
    Uses 0% GDI leaks, reusable DCs, and minimal bandwidth (~3 KB/frame) to prevent mobile lag.
    """
    import ctypes
    import cv2
    import numpy as np

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32)
        ]

    try:
        h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
        if h_desk:
            user32.SetThreadDesktop(h_desk)
    except Exception:
        pass

    sw = user32.GetSystemMetrics(0) or 1920
    sh = user32.GetSystemMetrics(1) or 1080
    target_w = 960  # Ultra-fast 40+ FPS stream for mobile
    target_h = int(sh * target_w / sw)

    src_dc = None
    mem_dc = None
    bmp = None

    try:
        src_dc = user32.GetDC(0)
        mem_dc = gdi32.CreateCompatibleDC(src_dc)
        bmp = gdi32.CreateCompatibleBitmap(src_dc, target_w, target_h)
        gdi32.SelectObject(mem_dc, bmp)
        gdi32.SetStretchBltMode(mem_dc, 3)  # COLORONCOLOR

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = target_w
        bmi.biHeight = -target_h  # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 24
        bmi.biCompression = 0

        class CURSORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint32),
                ("flags", ctypes.c_uint32),
                ("hCursor", ctypes.c_void_p),
                ("ptScreenPos", POINT)
            ]

        ci = CURSORINFO()
        ci.cbSize = ctypes.sizeof(CURSORINFO)
        raw_buf = (ctypes.c_char * (target_w * target_h * 3))()
        pt = POINT()

        while True:
            # Hardware StretchBlt scale directly in GDI driver
            gdi32.StretchBlt(mem_dc, 0, 0, target_w, target_h, src_dc, 0, 0, sw, sh, 0x00CC0020)

            # Render real Windows hardware mouse cursor directly onto frame
            try:
                if user32.GetCursorInfo(ctypes.byref(ci)) and (ci.flags & 1) and ci.hCursor:
                    cur_x = int(ci.ptScreenPos.x * target_w / sw)
                    cur_y = int(ci.ptScreenPos.y * target_h / sh)
                    user32.DrawIconEx(mem_dc, cur_x, cur_y, ci.hCursor, 0, 0, 0, None, 3)
            except Exception:
                pass

            gdi32.GetDIBits(mem_dc, bmp, 0, target_h, ctypes.byref(raw_buf), ctypes.byref(bmi), 0)

            frame = np.frombuffer(raw_buf, dtype=np.uint8).reshape((target_h, target_w, 3)).copy()

            ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 62])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

            time.sleep(0.02)  # ~45 FPS ultra-fluid real-time capture
    except Exception as e:
        logger.debug(f"Screen stream client disconnected: {e}")
    finally:
        # Guarantee 100% GDI cleanup on generator exit
        if bmp and mem_dc:
            try: gdi32.DeleteObject(bmp)
            except Exception: pass
        if mem_dc:
            try: gdi32.DeleteDC(mem_dc)
            except Exception: pass
        if src_dc:
            try: user32.ReleaseDC(0, src_dc)
            except Exception: pass

@app.get("/api/screen/stream")
def screen_stream():
    """Live MJPEG video stream of the computer screen for the mobile touchpad HUD."""
    return StreamingResponse(
        generate_screen_mjpeg_stream(),
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
    """Receives voice audio from mobile (webm/mp4/wav), converts via ffmpeg if needed, transcribes, and executes command."""
    import tempfile
    import subprocess
    import speech_recognition as sr

    in_path = None
    wav_path = None
    try:
        contents = await audio.read()
        suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(contents)
            in_path = tf.name

        wav_path = in_path + "_converted.wav"
        
        # Convert any incoming mobile audio container (webm, mp4, aac, ogg) to 16kHz mono WAV using ffmpeg
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["ffmpeg", "-y", "-i", in_path, "-vn", "-ar", "16000", "-ac", "1", "-f", "wav", wav_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=6
            )
            target_audio = wav_path
        except Exception as fe:
            logger.warning(f"ffmpeg conversion note: {fe}, attempting direct read...")
            target_audio = in_path

        def _transcribe():
            recognizer = sr.Recognizer()
            with sr.AudioFile(target_audio) as source:
                recorded = recognizer.record(source)
                return recognizer.recognize_google(recorded)

        text = await asyncio.wait_for(asyncio.to_thread(_transcribe), timeout=20)

        logger.info(f"Mobile voice transcribed: '{text}'")
        res = await execute_command(CommandRequest(text=text))
        if isinstance(res, dict):
            res["transcription"] = text
        return res
    except Exception as e:
        logger.warning(f"Voice upload processing error: {e}")
        return {"success": False, "response": f"Voice transcription error: {e}", "transcription": ""}
    finally:
        for p in [in_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

@app.post("/api/voice/pc_listen")
async def trigger_pc_listen():
    """Triggers the computer's physical microphone to listen for a spoken command (desktop app mode)."""
    try:
        from core.voice.stt import get_stt
        stt = get_stt()
        logger.info("PC physical microphone listening triggered from mobile...")
        text = await asyncio.wait_for(asyncio.to_thread(stt.listen, timeout=6.0), timeout=20)
        if text:
            logger.info(f"PC microphone captured: '{text}'")
            res = await execute_command(CommandRequest(text=text))
            if isinstance(res, dict):
                res["transcription"] = text
            return res
        else:
            return {"success": False, "response": "No speech detected on PC microphone.", "transcription": ""}
    except Exception as e:
        logger.error(f"PC mic listen error: {e}")
        return {"success": False, "response": f"PC microphone error: {e}", "transcription": ""}

# ==========================================
# AUTONOMOUS COMPUTER CONTROL & TOUCHPAD
# ==========================================
@app.websocket("/ws/mouse")
async def websocket_mouse_endpoint(websocket: WebSocket):
    """Ultra-low-latency bidirectional WebSocket for mobile touchpad.
    Zero HTTP overhead, sub-millisecond execution for fluid cursor movement and real-time cursor alignment.
    """
    dev_id = websocket.query_params.get("device_id")
    if dev_id and not check_device_allowed(dev_id):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    agent = get_computer_agent()

    # Instantly align pulse cursor upon connection & send exact screen resolution
    try:
        _, _, init_x, init_y = agent.get_cursor_pos()
        await websocket.send_text(f"res:{agent.screen_width},{agent.screen_height}")
        await websocket.send_text(f"p:{init_x},{init_y}")
    except Exception:
        pass

    try:
        while True:
            msg = await websocket.receive_text()
            if not msg:
                continue
            if dev_id and not check_device_allowed(dev_id):
                await websocket.send_text("error:access_revoked")
                await websocket.close(code=1008)
                break
            if msg.startswith("m:"):
                # "m:dx,dy" format for relative movement
                parts = msg[2:].split(",")
                if len(parts) == 2:
                    try:
                        coords = agent.move_rel(int(parts[0]), int(parts[1]))
                        if coords:
                            await websocket.send_text(f"p:{coords[0]},{coords[1]}")
                    except ValueError:
                        pass
            elif msg.startswith("a:"):
                # "a:pctX,pctY" format for direct screen touch / absolute position
                parts = msg[2:].split(",")
                if len(parts) == 2:
                    try:
                        px = float(parts[0])
                        py = float(parts[1])
                        abs_x = int((px / 100.0) * agent.screen_width)
                        abs_y = int((py / 100.0) * agent.screen_height)
                        agent.move_to(abs_x, abs_y)
                        await websocket.send_text(f"p:{px:.2f},{py:.2f}")
                    except ValueError:
                        pass
            elif msg.startswith("c:"):
                # "c:btn" format for clicks (left, right, double)
                btn = msg[2:].strip()
                agent.click(button=btn)
                try:
                    _, _, cx, cy = agent.get_cursor_pos()
                    await websocket.send_text(f"p:{cx},{cy}")
                except Exception:
                    pass
            elif msg.startswith("s:"):
                # "s:amount" format for wheel scroll
                try:
                    agent.scroll(int(msg[2:].strip()))
                except ValueError:
                    pass
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception as e:
        logger.debug(f"Mouse WS closed: {e}")

@app.post("/api/computer/mouse/move")
@app.post("/api/mouse/move")
async def mouse_move(req: MouseMoveRequest):
    if req.device_id and not check_device_allowed(req.device_id):
        raise HTTPException(status_code=403, detail="Device access revoked.")
    agent = get_computer_agent()
    success = agent.move_rel(req.dx, req.dy)
    return {"success": success}

@app.post("/api/computer/mouse/click")
@app.post("/api/mouse/click")
async def mouse_click(req: MouseClickRequest):
    if req.device_id and not check_device_allowed(req.device_id):
        raise HTTPException(status_code=403, detail="Device access revoked.")
    agent = get_computer_agent()
    success = agent.click(button=req.button, clicks=req.clicks)
    return {"success": success}

@app.post("/api/computer/mouse/scroll")
@app.post("/api/mouse/scroll")
async def mouse_scroll(req: MouseScrollRequest):
    if req.device_id and not check_device_allowed(req.device_id):
        raise HTTPException(status_code=403, detail="Device access revoked.")
    agent = get_computer_agent()
    success = agent.scroll(req.amount)
    return {"success": success}

@app.post("/api/computer/keyboard/type")
@app.post("/api/keyboard/type")
def keyboard_type(req: KeyboardTypeRequest):
    if req.device_id and not check_device_allowed(req.device_id):
        raise HTTPException(status_code=403, detail="Device access revoked.")
    agent = get_computer_agent()
    success = agent.type_text(req.text)
    return {"success": success}

@app.post("/api/computer/workflow")
def run_workflow(req: WorkflowRequest):
    agent = get_computer_agent()
    act = req.action.lower().strip()
    param = req.param.strip()
    logger.info(f"Triggering autonomous workflow: {act} ('{param}')")

    if act == "search_google":
        success = agent.workflow_search_google(param or "latest AI breakthroughs")
    elif act == "search_youtube":
        success = agent.workflow_search_youtube(param or "lofi beats")
    elif act == "ask_ai":
        success = agent.workflow_ask_ai(param or "Generate a python automation script")
    elif act == "notepad":
        success = agent.workflow_quick_notepad(param or "Meeting notes: sync on AI architecture at 4 PM.")
    elif act == "start_menu":
        success = agent.workflow_start_menu_launch(param or "calculator")
    elif act == "snap_left":
        success = agent.workflow_snap_window("left")
    elif act == "snap_right":
        success = agent.workflow_snap_window("right")
    elif act == "maximize":
        success = agent.workflow_snap_window("max")
    elif act == "alt_tab":
        success = agent.workflow_switch_window()
    else:
        return {"success": False, "error": f"Unknown workflow '{act}'"}

    return {"success": success, "action": act, "logs": agent.get_logs(limit=5)}

@app.get("/api/computer/logs")
def get_computer_logs():
    agent = get_computer_agent()
    return {"logs": agent.get_logs(limit=25)}

@app.get("/api/ssl_info")
def get_ssl_info():
    ip = get_local_ip()
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.pem")
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert.pem")
    https_ready = os.path.exists(key_path) and os.path.exists(cert_path)
    return {
        "https_enabled": https_ready,
        "https_port": 8443,
        "http_port": 8000,
        "local_ip": ip,
        "https_url": f"https://{ip}:8443",
        "http_url": f"http://{ip}:8000"
    }

def ensure_ssl_certificates(host_ip: str):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(root_dir, "key.pem")
    cert_path = os.path.join(root_dir, "cert.pem")
    if os.path.exists(key_path) and os.path.exists(cert_path):
        return key_path, cert_path

    try:
        import datetime
        import ipaddress
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"GHOST Mobile Server"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"GHOST OS"),
        ])

        alt_names = [
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        try:
            alt_names.append(x509.IPAddress(ipaddress.IPv4Address(host_ip)))
        except Exception:
            pass

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        return key_path, cert_path
    except Exception as e:
        logger.warning(f"Could not generate SSL certificates: {e}")
        return None, None

def print_banner(host_ip, http_port, https_port=None):
    try:
        http_url = f"http://{host_ip}:{http_port}"
        https_url = f"https://{host_ip}:{https_port}" if https_port else None

        print("\n" + "=" * 65)
        print("       [+] GHOST MOBILE REMOTE SERVER IS ACTIVE!")
        print("=" * 65)
        
        if https_url:
            print(f"\n>>> 🔒 SECURE HTTPS (Unlocks iPhone Mic & 'Ghost' Wake Word):")
            print(f"    {https_url}")
            print(f"    (Tap 'Show Details' -> 'Visit this website' once on iPhone)\n")

        print(f">>> 🌐 STANDARD HTTP:")
        print(f"    {http_url}\n")
        print("    Make sure your iPhone is connected to the same Wi-Fi!\n")

        # Generate QR Code for HTTPS if available, otherwise HTTP
        target_qr = https_url or http_url
        try:
            import qrcode
            qr = qrcode.QRCode(border=1)
            qr.add_data(target_qr)
            qr.make(fit=True)
            print(f"[*] SCAN THIS QR CODE WITH YOUR IPHONE CAMERA ({'HTTPS' if https_url else 'HTTP'}):")
            qr.print_ascii(invert=True)
        except Exception:
            pass
        print("=" * 65 + "\n")
    except Exception:
        pass

def free_ports(*ports):
    """Automatically free ports if occupied by another instance or stale process."""
    import subprocess
    my_pid = str(os.getpid())
    for port in ports:
        try:
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in line.upper():
                    pid = parts[-1]
                    if pid != my_pid and pid != "0":
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        time.sleep(0.2)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        import uvicorn
        import threading
        local_ip = get_local_ip()
        http_port = 8000
        https_port = 8443

        # Prevent [Errno 10048] by releasing any stale listeners
        free_ports(http_port, https_port)

        key_path, cert_path = ensure_ssl_certificates(local_ip)

        if not _is_silent:
            print_banner(local_ip, http_port, https_port if key_path else None)

        # Run HTTPS on 8443 in a background thread if certificates exist
        if key_path and cert_path:
            def run_https():
                try:
                    uvicorn.run(
                        app,
                        host="0.0.0.0",
                        port=https_port,
                        ssl_keyfile=key_path,
                        ssl_certfile=cert_path,
                        log_level="warning" if not _is_silent else "critical"
                    )
                except Exception as ex:
                    logger.warning(f"HTTPS server error: {ex}")

            t_https = threading.Thread(target=run_https, daemon=True)
            t_https.start()

        # Run HTTP on 8000 in main thread
        if not _is_silent:
            uvicorn.run(app, host="0.0.0.0", port=http_port, log_level="warning")
        else:
            uvicorn.run(app, host="0.0.0.0", port=http_port, log_config=None)
    except BaseException as e:
        import traceback
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs", "server_crash.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{time.ctime()}] CRASH: {type(e)} {e}\n{traceback.format_exc()}\n")
        except Exception:
            pass
