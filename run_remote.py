"""
JARVIS Mobile Remote Launcher
Launches the local FastAPI server and an encrypted public HTTPS tunnel
accessible anywhere over 4G/5G mobile data or outside Wi-Fi networks.
"""
import os
import sys
import time
import subprocess
import re
import socket
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe")

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_tunnel_password():
    try:
        req = urllib.request.Request("https://loca.lt/mytunnelpassword", headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read().decode("utf-8").strip()
    except Exception:
        return None

def main():
    print("=" * 65)
    print("       [*] STARTING GHOST MOBILE REMOTE CONTROLLER")
    print("=" * 65)
    print("[1/3] Starting GHOST backend server on port 8000...")

    server_proc = subprocess.Popen(
        [PYTHON_EXE, os.path.join(ROOT_DIR, "server.py")],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)

    print("[2/3] Establishing encrypted public HTTPS tunnel...")
    tunnel_proc = subprocess.Popen(
        ["npx.cmd", "-y", "localtunnel", "--port", "8000"],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    tunnel_url = None
    print("[3/3] Generating your secure public link...")
    start_time = time.time()
    while time.time() - start_time < 30:
        line = tunnel_proc.stdout.readline()
        if not line and tunnel_proc.poll() is not None:
            break
        match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", line)
        if match:
            tunnel_url = match.group(0)
            break

    tunnel_pwd = get_tunnel_password()
    local_ip = get_local_ip()

    print("\n" + "=" * 65)
    print("       [+] GHOST MOBILE CONTROLLER IS READY & ONLINE!")
    print("=" * 65)

    if tunnel_url:
        print(f"\n>>> 🌍 4G/5G ANYWHERE ACCESS (Open on phone browser):")
        print(f"    URL:      {tunnel_url}")
        if tunnel_pwd:
            print(f"    PASSWORD: {tunnel_pwd}  (If prompted 'Click to Submit', enter this)")
    
    print(f"\n>>> 🏠 SAME WI-FI ACCESS:")
    print(f"    http://{local_ip}:8000")
    print("=" * 65)
    print("\nServer is active in the background. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            if server_proc.poll() is not None or tunnel_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping JARVIS Mobile Remote...")
    finally:
        server_proc.terminate()
        tunnel_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
