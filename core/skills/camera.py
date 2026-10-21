"""
Camera Skill — captures computer webcam snapshots and streams live video to mobile HUD.
"""
import os
import time
import threading
from core.utils.logger import get_logger

logger = get_logger("skills.camera")

class CameraSkill:
    def __init__(self):
        self._lock = threading.Lock()

    def capture_snapshot(self) -> str:
        """Captures a single high-quality snapshot from the PC webcam and saves to data/camera_snapshot.jpg."""
        with self._lock:
            try:
                import cv2
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    logger.warning("Could not open webcam.")
                    return ""

                # Let camera adjust auto-exposure
                for _ in range(5):
                    cap.read()
                ret, frame = cap.read()
                cap.release()

                if not ret or frame is None:
                    logger.warning("Failed to grab camera frame.")
                    return ""

                data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
                os.makedirs(data_dir, exist_ok=True)
                path = os.path.join(data_dir, "camera_snapshot.jpg")
                cv2.imwrite(path, frame)

                # Also save copy to Desktop
                try:
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Ghost_camera.jpg")
                    cv2.imwrite(desktop_path, frame)
                except Exception:
                    pass

                logger.info(f"Webcam snapshot saved successfully: {path}")
                return path
            except Exception as e:
                logger.error(f"Error capturing camera snapshot: {e}")
                return ""

    def generate_mjpeg_stream(self):
        """Yields MJPEG frames for real-time live webcam video streaming to mobile."""
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.warning("Live camera stream: webcam not accessible.")
                return

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.05)
                        continue

                    # Resize slightly for smooth mobile streaming
                    h, w = frame.shape[:2]
                    if w > 640:
                        frame = cv2.resize(frame, (640, int(h * 640 / w)))

                    # Encode to JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                    if not ret:
                        continue

                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(0.04)  # ~25 FPS
            finally:
                cap.release()
                logger.info("Camera stream closed.")
        except Exception as e:
            logger.error(f"Camera stream error: {e}")

_camera_instance = None

def get_camera() -> CameraSkill:
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = CameraSkill()
    return _camera_instance
