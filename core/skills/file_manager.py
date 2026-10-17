"""
File Manager Skill — creates and manages desktop folders and files.
"""
import os
import subprocess
from core.utils.logger import get_logger

logger = get_logger("skills.files")

class FileManager:
    def __init__(self):
        self.desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(self.desktop):
            self.desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")

    def create_desktop_folder(self, folder_name: str = "New Folder") -> str:
        folder_path = os.path.join(self.desktop, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Desktop folder created at: {folder_path}")
            return folder_path
        except Exception as e:
            logger.error(f"Failed to create desktop folder: {e}")
            return ""

    def open_folder(self, path: str = None) -> bool:
        target = path or self.desktop
        try:
            os.startfile(target)
            return True
        except Exception as e:
            logger.error(f"Failed to open folder {target}: {e}")
            return False

_file_instance = None

def get_file_manager() -> FileManager:
    global _file_instance
    if _file_instance is None:
        _file_instance = FileManager()
    return _file_instance
