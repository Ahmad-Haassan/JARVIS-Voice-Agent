"""
GHOST Firebase Cloud Bridge
Enables worldwide 4G/5G zero-config remote control via Firebase Realtime Database.
No port forwarding, no tunnels, survives laptop reboots and network switches.
"""
import os
import sys
import time
import json
import socket
import psutil
import threading
import urllib.request
import urllib.error
import base64
from datetime import datetime
from typing import Optional, Dict, Any

from core.utils.logger import get_logger

logger = get_logger("bridge.firebase")

DATABASE_URL = "https://jarvis-remote-8bf6a-default-rtdb.firebaseio.com"
FIREBASE_ROOT = "ghost_bridge"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEVICES_FILE = os.path.join(ROOT_DIR, "data", "devices.json")
AUTH_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "pairing_token.txt")

def get_pairing_pin() -> str:
    if os.path.exists(AUTH_TOKEN_FILE):
        try:
            with open(AUTH_TOKEN_FILE, "r", encoding="utf-8") as f:
                t = f.read().strip()
                if t:
                    return t
        except Exception:
            pass
    import random
    pin = f"{random.randint(100000, 999999)}"
    try:
        os.makedirs(os.path.dirname(AUTH_TOKEN_FILE), exist_ok=True)
        with open(AUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(pin)
    except Exception:
        pass
    return pin

def load_local_devices() -> dict:
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_local_devices(data: dict):
    try:
        os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save devices locally: {e}")

def fb_request(path: str, data: Optional[dict] = None, method: str = "GET", timeout: int = 6) -> Optional[Any]:
    url = f"{DATABASE_URL}/{FIREBASE_ROOT}/{path.lstrip('/')}.json"
    headers = {"Content-Type": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_data = response.read().decode("utf-8")
            if res_data and res_data != "null":
                return json.loads(res_data)
            return None
    except Exception as e:
        logger.debug(f"Firebase {method} {path} error: {e}")
        return None

def get_active_window_title() -> str:
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
    except Exception:
        pass
    return "Desktop"

class FirebaseCloudBridge:
    def __init__(self):
        self.pairing_pin = get_pairing_pin()
        self.pc_name = socket.gethostname()
        self.running = False
        self._threads = []
        self._processed_cmd_ids = set()
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        logger.info(f"Starting Firebase Cloud Bridge (PC: {self.pc_name}, PIN: {self.pairing_pin})...")
        
        # 1. Telemetry heartbeat thread
        t1 = threading.Thread(target=self._telemetry_loop, daemon=True)
        t1.name = "FB-Telemetry"
        t1.start()
        self._threads.append(t1)

        # 2. Devices sync loop
        t2 = threading.Thread(target=self._device_sync_loop, daemon=True)
        t2.name = "FB-DeviceSync"
        t2.start()
        self._threads.append(t2)

        # 3. Realtime command dispatcher loop
        t3 = threading.Thread(target=self._command_dispatcher_loop, daemon=True)
        t3.name = "FB-CommandDispatcher"
        t3.start()
        self._threads.append(t3)

        logger.info("[+] Firebase Cloud Bridge is fully online and ready worldwide!")

    def stop(self):
        self.running = False
        try:
            fb_request("status", {"online": False, "last_seen": time.time()}, method="PATCH")
        except Exception:
            pass

    def _telemetry_loop(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                bat = None
                plugged = True
                try:
                    s_bat = psutil.sensors_battery()
                    if s_bat:
                        bat = s_bat.percent
                        plugged = s_bat.power_plugged
                except Exception:
                    pass

                window_title = get_active_window_title()

                status_payload = {
                    "online": True,
                    "pc_name": self.pc_name,
                    "cpu": round(cpu, 1),
                    "ram": round(ram, 1),
                    "battery": bat,
                    "battery_plugged": plugged,
                    "active_window": window_title,
                    "pairing_pin": self.pairing_pin,
                    "last_seen": time.time(),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                fb_request("status", status_payload, method="PUT")
            except Exception as e:
                logger.debug(f"Telemetry loop error: {e}")
            
            time.sleep(3.5)

    def _device_sync_loop(self):
        while self.running:
            try:
                # A. Sync local devices to Firebase
                local_devs = load_local_devices()
                fb_request("devices", local_devs, method="PUT")

                # B. Check for device action requests from Web UI (delete)
                actions = fb_request("device_actions", method="GET")
                if actions and isinstance(actions, dict):
                    for act_id, act in list(actions.items()):
                        dev_id = act.get("device_id")
                        act_type = act.get("action")
                        if dev_id:
                            if dev_id in local_devs:
                                del local_devs[dev_id]
                                save_local_devices(local_devs)
                                logger.info(f"[CloudBridge] Device completely deleted: {dev_id}")
                            fb_request(f"devices/{dev_id}", method="DELETE")
                        
                        # Delete action once handled
                        fb_request(f"device_actions/{act_id}", method="DELETE")

                # C. Check pending registrations from mobile QR/PIN scans
                pending = fb_request("pending_registrations", method="GET")
                if pending and isinstance(pending, dict):
                    for reg_id, reg_data in list(pending.items()):
                        token = str(reg_data.get("token", "")).strip()
                        dev_id = str(reg_data.get("device_id", "")).strip()
                        if token == self.pairing_pin and dev_id:
                            local_devs[dev_id] = {
                                "device_id": dev_id,
                                "device_name": reg_data.get("device_name", "Remote Device"),
                                "ip": reg_data.get("ip", "4G/Cloud"),
                                "user_agent": reg_data.get("user_agent", ""),
                                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "last_seen": time.time(),
                                "is_blocked": False,
                                "is_authenticated": True
                            }
                            save_local_devices(local_devs)
                            fb_request(f"devices/{dev_id}", local_devs[dev_id], method="PUT")
                            fb_request(f"pending_registrations/{reg_id}", {"success": True, "paired": True}, method="PATCH")
                            logger.info(f"[CloudBridge] Device paired successfully via Cloud: {dev_id} ({local_devs[dev_id]['device_name']})")
                        else:
                            fb_request(f"pending_registrations/{reg_id}", {"success": False, "error": "Invalid PIN"}, method="PATCH")
            except Exception as e:
                logger.debug(f"Device sync loop error: {e}")
            
            time.sleep(5)

    def _command_dispatcher_loop(self):
        """Streams commands in real-time using Firebase Server-Sent Events (SSE).
        Falls back to fast polling if stream disconnects.
        """
        while self.running:
            url = f"{DATABASE_URL}/{FIREBASE_ROOT}/commands.json"
            req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
            try:
                with urllib.request.urlopen(req, timeout=45) as stream:
                    logger.info("[CloudBridge] Real-time SSE stream connected.")
                    cur_event = None
                    for raw_line in stream:
                        if not self.running:
                            break
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        if line.startswith("event:"):
                            cur_event = line[6:].strip()
                        elif line.startswith("data:"):
                            raw_data = line[5:].strip()
                            if raw_data == "null":
                                continue
                            try:
                                payload = json.loads(raw_data)
                                if isinstance(payload, dict):
                                    # SSE can deliver root dict of commands {"cmd1": {...}, "cmd2": {...}}
                                    # or path patch: {"path": "/cmd1", "data": {...}}
                                    if "path" in payload and "data" in payload:
                                        p = payload["path"].lstrip("/")
                                        d = payload["data"]
                                        if p and isinstance(d, dict):
                                            self._execute_single_command(p, d)
                                        elif not p and isinstance(d, dict):
                                            for cid, cdata in d.items():
                                                if isinstance(cdata, dict):
                                                    self._execute_single_command(cid, cdata)
                                    else:
                                        for cid, cdata in payload.items():
                                            if isinstance(cdata, dict):
                                                self._execute_single_command(cid, cdata)
                            except Exception as pe:
                                logger.debug(f"SSE parse error: {pe}")
            except Exception as se:
                logger.debug(f"SSE stream reconnecting: {se}")
                # Fallback poll to drain any pending commands before reconnecting SSE
                try:
                    cmds = fb_request("commands", method="GET", timeout=4)
                    if cmds and isinstance(cmds, dict):
                        for cid, cdata in cmds.items():
                            if isinstance(cdata, dict):
                                self._execute_single_command(cid, cdata)
                except Exception:
                    pass
                time.sleep(1.5)

    def _execute_single_command(self, cmd_id: str, cmd_data: dict):
        with self._lock:
            if cmd_id in self._processed_cmd_ids:
                return
            self._processed_cmd_ids.add(cmd_id)
            if len(self._processed_cmd_ids) > 500:
                self._processed_cmd_ids.pop()

        # Delete command node immediately so it won't be reprocessed
        fb_request(f"commands/{cmd_id}", method="DELETE")

        # Security check: only reject if device was explicitly deleted/blocked
        local_devs = load_local_devices()
        if dev_id and dev_id in local_devs:
            if local_devs[dev_id].get("is_blocked"):
                logger.warning(f"[CloudBridge] Blocked device attempt: {dev_id}")
                fb_request(f"responses/{cmd_id}", {
                    "success": False,
                    "response": "Access Revoked by PC Owner",
                    "error": "Access Revoked",
                    "blocked": True,
                    "timestamp": time.time()
                }, method="PUT")
                return

        # Auto-register device if not already present
        if dev_id and dev_id not in local_devs:
            local_devs[dev_id] = {
                "device_id": dev_id,
                "device_name": cmd_data.get("device_name", "Remote Device"),
                "ip": "Cloud/4G",
                "user_agent": "",
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_seen": time.time(),
                "is_blocked": False,
                "is_authenticated": True
            }
            save_local_devices(local_devs)
            fb_request(f"devices/{dev_id}", local_devs[dev_id], method="PUT")

        # Execute action in a dedicated worker thread
        threading.Thread(target=self._run_action_worker, args=(cmd_id, cmd_data), daemon=True).start()

    def _run_action_worker(self, cmd_id: str, cmd_data: dict):
        action = cmd_data.get("action", "command")
        logger.info(f"[CloudBridge] Executing action '{action}' for cmd {cmd_id}")
        
        from core.skills.computer_agent import get_computer_agent
        from core.skills.system_control import get_system_control

        agent = get_computer_agent()
        sys_ctrl = get_system_control()

        resp_payload = {"success": True, "action": action, "timestamp": time.time()}

        try:
            if action in ("command", "ai", "nlp"):
                text = cmd_data.get("text", "")
                from server import _execute_command_sync
                res = _execute_command_sync(text)
                resp_payload.update(res)

            elif action == "mouse_move":
                dx = int(cmd_data.get("dx", 0))
                dy = int(cmd_data.get("dy", 0))
                coords = agent.move_rel(dx, dy)
                resp_payload["coords"] = coords

            elif action == "mouse_touch":
                pct_x = float(cmd_data.get("pct_x", 50))
                pct_y = float(cmd_data.get("pct_y", 50))
                abs_x = int((pct_x / 100.0) * agent.screen_width)
                abs_y = int((pct_y / 100.0) * agent.screen_height)
                agent.move_to(abs_x, abs_y)
                resp_payload["x"] = abs_x
                resp_payload["y"] = abs_y

            elif action == "mouse_click":
                btn = cmd_data.get("button", "left")
                clicks = int(cmd_data.get("clicks", 1))
                agent.click(button=btn, clicks=clicks)

            elif action == "mouse_scroll":
                amount = int(cmd_data.get("amount", -300))
                agent.scroll(amount)

            elif action == "keyboard_type":
                text = cmd_data.get("text", "")
                agent.type_text(text)

            elif action == "keyboard_key":
                key = cmd_data.get("key", "")
                if "+" in key:
                    keys = [k.strip() for k in key.split("+")]
                    agent.hotkey(*keys)
                else:
                    agent.press_key(key)

            elif action == "workflow":
                wf = cmd_data.get("workflow", "")
                if wf == "snap_left":
                    agent.workflow_snap_window("left")
                elif wf == "snap_right":
                    agent.workflow_snap_window("right")
                elif wf == "maximize":
                    agent.workflow_snap_window("max")
                elif wf == "alt_tab":
                    agent.workflow_switch_window()
                elif wf == "lock":
                    sys_ctrl.lock_screen()
                elif wf == "sleep":
                    sys_ctrl.sleep_pc()
                elif wf == "shutdown":
                    sys_ctrl.shutdown_pc(timer=10)
                elif wf == "restart":
                    sys_ctrl.restart_pc(timer=10)

            elif action == "volume":
                level = cmd_data.get("level")
                if level is not None:
                    sys_ctrl.set_volume(int(level))
                elif cmd_data.get("mute"):
                    sys_ctrl.mute_volume()

            elif action == "screenshot_req":
                p = sys_ctrl.take_screenshot()
                if p and os.path.exists(p):
                    try:
                        import cv2
                        frame = cv2.imread(p)
                        if frame is not None:
                            h, w = frame.shape[:2]
                            target_w = 960
                            target_h = int(h * target_w / w)
                            resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                            ret, buf = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                            if ret:
                                b64 = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")
                                fb_request("screen", {"image": b64, "timestamp": time.time()}, method="PUT")
                                resp_payload["screenshot_ready"] = True
                    except Exception as ie:
                        logger.error(f"Screenshot compression error: {ie}")

            elif action == "ping":
                resp_payload["ping"] = "pong"

        except Exception as e:
            logger.error(f"Error handling action '{action}': {e}")
            resp_payload["success"] = False
            resp_payload["error"] = str(e)

        # Write response to Firebase for mobile HUD
        fb_request(f"responses/{cmd_id}", resp_payload, method="PUT")

_bridge_instance: Optional[FirebaseCloudBridge] = None

def get_firebase_bridge() -> FirebaseCloudBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = FirebaseCloudBridge()
    return _bridge_instance

if __name__ == "__main__":
    b = get_firebase_bridge()
    b.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        b.stop()
