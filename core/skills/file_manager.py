"""
File Manager Skill — creates, resolves, and manages desktop and system folders.
"""
import os
import re
import subprocess
from typing import Optional, Tuple
from core.utils.logger import get_logger

logger = get_logger("skills.files")

class FileManager:
    def __init__(self):
        self.home = os.path.expanduser("~")
        onedrive = os.path.join(self.home, "OneDrive")
        self.onedrive = onedrive if os.path.exists(onedrive) else None

        # Standard Windows & OneDrive directories
        self.desktop = (
            os.path.join(self.onedrive, "Desktop")
            if self.onedrive and os.path.exists(os.path.join(self.onedrive, "Desktop"))
            else os.path.join(self.home, "Desktop")
        )
        self.documents = (
            os.path.join(self.onedrive, "Documents")
            if self.onedrive and os.path.exists(os.path.join(self.onedrive, "Documents"))
            else os.path.join(self.home, "Documents")
        )
        self.downloads = os.path.join(self.home, "Downloads")
        self.pictures = (
            os.path.join(self.onedrive, "Pictures")
            if self.onedrive and os.path.exists(os.path.join(self.onedrive, "Pictures"))
            else os.path.join(self.home, "Pictures")
        )
        self.videos = os.path.join(self.home, "Videos")
        self.music = os.path.join(self.home, "Music")
        
        # Project workspace root
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def resolve_folder(self, target: Optional[str]) -> Tuple[Optional[str], str]:
        """Resolves natural language folder requests (e.g. 'my downloads folder') into absolute paths."""
        if not target:
            return self.desktop, "Desktop"

        raw = target.strip().strip("\"'")
        norm = raw.lower().strip()
        norm = re.sub(r"^(?:my|the)\s+", "", norm)
        norm = re.sub(r"^(?:folder|directory)\s+(?:of|called|named)?\s*", "", norm)
        norm = re.sub(r"\s+(?:folder|directory)$", "", norm)
        norm = norm.strip()

        # Known common aliases
        if norm in ["downloads", "download", "my downloads"]:
            return self.downloads, "Downloads"
        if norm in ["documents", "document", "docs", "doc", "my documents"]:
            return self.documents, "Documents"
        if norm in ["desktop", "my desktop"]:
            return self.desktop, "Desktop"
        if norm in ["pictures", "picture", "photos", "photo", "images", "image", "pics"]:
            return self.pictures, "Pictures"
        if norm in ["videos", "video", "movies", "movie"]:
            return self.videos, "Videos"
        if norm in ["music", "songs", "song", "audio"]:
            return self.music, "Music"
        if norm in ["this pc", "my pc", "pc", "computer", "my computer", "explorer", "file explorer"]:
            return "explorer.exe", "This PC"
        if norm in ["recycle bin", "trash", "bin"]:
            return "shell:RecycleBinFolder", "Recycle Bin"
        if norm in ["c drive", "drive c", "local disk c", "c:", "c"]:
            return "C:\\", "Local Disk (C:)"
        if norm in ["d drive", "drive d", "local disk d", "d:", "d"]:
            return ("D:\\", "Local Disk (D:)") if os.path.exists("D:\\") else (None, "D Drive")
        if norm in ["e drive", "drive e", "local disk e", "e:", "e"]:
            return ("E:\\", "Local Disk (E:)") if os.path.exists("E:\\") else (None, "E Drive")
        if norm in ["jarvis", "project", "workspace", "code", "repo", "repository"]:
            return self.project_root, "Jarvis Project"
        if norm in ["home", "user", "profile", "user profile"]:
            return self.home, "User Profile"

        # Direct existing paths
        if os.path.exists(target) and os.path.isdir(target):
            return os.path.abspath(target), os.path.basename(target) or target
        if os.path.exists(raw) and os.path.isdir(raw):
            return os.path.abspath(raw), os.path.basename(raw) or raw

        # Base user directories to search (never search internal program files or repo code)
        bases = [self.desktop, self.documents, self.downloads, self.home]
        for base in bases:
            if not base or not os.path.exists(base):
                continue
            cand_raw = os.path.join(base, raw)
            if os.path.exists(cand_raw) and os.path.isdir(cand_raw):
                return cand_raw, os.path.basename(cand_raw)
            cand_norm = os.path.join(base, norm)
            if os.path.exists(cand_norm) and os.path.isdir(cand_norm):
                return cand_norm, os.path.basename(cand_norm)

        # Deep recursive folder search (up to depth 3)
        SKIP_DIRS = {
            "node_modules", ".git", "__pycache__", "venv", ".venv", ".next", 
            "appdata", "dist", "build", "core", "gui", "data", ".vscode", "bin", "obj"
        }
        
        # Pass 1: Exact directory name match
        for base in bases:
            if not base or not os.path.exists(base):
                continue
            base_depth = base.rstrip(os.sep).count(os.sep)
            for root, dirs, _ in os.walk(base):
                dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
                cur_depth = root.rstrip(os.sep).count(os.sep) - base_depth
                if cur_depth >= 3:
                    dirs[:] = []
                    continue
                for d in dirs:
                    if d.lower() == norm or d.lower() == raw.lower():
                        return os.path.join(root, d), d

        # Pass 2: Exact word token match or high-confidence fuzzy match
        import difflib
        best_candidate = None
        best_ratio = 0.0
        norm_words = norm.split()
        
        for base in bases:
            if not base or not os.path.exists(base):
                continue
            base_depth = base.rstrip(os.sep).count(os.sep)
            for root, dirs, _ in os.walk(base):
                dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
                cur_depth = root.rstrip(os.sep).count(os.sep) - base_depth
                if cur_depth >= 3:
                    dirs[:] = []
                    continue
                for d in dirs:
                    d_low = d.lower()
                    d_words = d_low.split()
                    
                    # Exact whole words match (e.g. 'uni assignments')
                    if len(norm_words) > 1 and all(w in d_words for w in norm_words):
                        return os.path.join(root, d), d
                    
                    # Prefix match if query has 4+ characters
                    if len(norm) >= 4 and d_low.startswith(norm + " "):
                        return os.path.join(root, d), d
                    
                    # High confidence fuzzy match (requires >= 84% similarity and similar length)
                    if abs(len(norm) - len(d_low)) <= 3:
                        ratio = difflib.SequenceMatcher(None, norm, d_low).ratio()
                        if ratio > best_ratio and ratio >= 0.84:
                            best_ratio = ratio
                            best_candidate = (os.path.join(root, d), d)

        if best_candidate:
            return best_candidate

        return None, raw

    def open_file(self, file_name_or_path: str) -> Tuple[bool, str, Optional[str]]:
        """Finds and opens a specific file on the computer with its default application."""
        if not file_name_or_path:
            return False, "No file specified.", None
        raw = file_name_or_path.strip().strip("\"'")
        if os.path.exists(raw) and os.path.isfile(raw):
            try:
                os.startfile(raw)
                return True, f"Opened file {os.path.basename(raw)}.", raw
            except Exception as e:
                return False, f"Could not open file: {e}", None

        bases = [self.desktop, self.documents, self.downloads, self.project_root]
        SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", ".next", "appdata"}
        target_low = raw.lower()
        for base in bases:
            if not base or not os.path.exists(base):
                continue
            base_depth = base.rstrip(os.sep).count(os.sep)
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
                if root.rstrip(os.sep).count(os.sep) - base_depth >= 3:
                    dirs[:] = []
                    continue
                for f in files:
                    if f.lower() == target_low or target_low in f.lower():
                        full = os.path.join(root, f)
                        try:
                            os.startfile(full)
                            return True, f"Opened {f}.", full
                        except Exception as e:
                            return False, f"Error opening {f}: {e}", None
        return False, f"Could not find file '{raw}'.", None


    def is_folder_request(self, text: str) -> bool:
        """Determines if a command text is requesting to open or manipulate a folder."""
        if not text:
            return False
        t_low = text.lower().strip()
        if any(w in t_low for w in ["folder", "directory", "downloads", "documents", "desktop", "c drive", "d drive", "file explorer", "this pc"]):
            return True
        path, _ = self.resolve_folder(text)
        return path is not None

    def create_desktop_folder(self, folder_name: str = "New Folder") -> str:
        folder_path = os.path.join(self.desktop, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Desktop folder created at: {folder_path}")
            return folder_path
        except Exception as e:
            logger.error(f"Failed to create desktop folder: {e}")
            return ""

    def open_folder(self, path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Opens the specified or resolved folder in Windows File Explorer."""
        resolved, name = self.resolve_folder(path)
        if not resolved:
            logger.warning(f"Could not resolve folder target: '{path}'")
            return False, f"Could not find folder '{path}' on your system.", None

        try:
            if resolved == "explorer.exe":
                subprocess.Popen(["explorer.exe"])
                logger.info("Launched File Explorer.")
                return True, "Opened File Explorer.", "explorer.exe"
            elif resolved.startswith("shell:"):
                subprocess.Popen(["explorer.exe", resolved])
                logger.info(f"Opened shell location: {resolved}")
                return True, f"Opened {name}.", resolved
            else:
                os.startfile(resolved)
                logger.info(f"Successfully opened folder: {resolved}")
                return True, f"Opened {name} folder.", resolved
        except Exception as e:
            logger.warning(f"os.startfile failed for '{resolved}': {e}, attempting explorer.exe fallback...")
            try:
                subprocess.Popen(["explorer.exe", resolved])
                logger.info(f"Explorer fallback opened folder: {resolved}")
                return True, f"Opened {name} folder.", resolved
            except Exception as fe:
                logger.error(f"Failed to open folder {resolved}: {fe}")
                return False, f"Failed to open folder '{name}': {fe}", None

    def read_document_text(self, file_path: str, max_chars: int = 4000) -> str:
        """Reads text from Word documents (.docx), text files, code, etc."""
        if not file_path or not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".docx":
            try:
                import zipfile, xml.etree.ElementTree as ET
                with zipfile.ZipFile(file_path) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    paragraphs = []
                    for p in tree.iterfind(".//w:p", ns):
                        text = "".join(node.text for node in p.iterfind(".//w:t", ns) if node.text)
                        if text:
                            paragraphs.append(text)
                    return "\n".join(paragraphs)[:max_chars]
            except Exception as e:
                logger.warning(f"Failed to parse docx '{file_path}': {e}")
                return ""

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars)
        except Exception:
            try:
                with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                    return f.read(max_chars)
            except Exception as e:
                logger.warning(f"Failed to read file '{file_path}': {e}")
                return ""

    def find_document_in_folder(self, folder_query: str, doc_query: str) -> Tuple[Optional[str], str]:
        """Locates a document inside a specified folder."""
        folder_path, folder_name = self.resolve_folder(folder_query)
        if not folder_path or not os.path.exists(folder_path):
            return None, f"Could not find folder '{folder_query}'"

        q_clean = doc_query.lower().strip()
        q_tokens = [tok for tok in q_clean.replace("_", " ").replace("-", " ").split() if len(tok) > 1]

        # Scan folder up to depth 3
        for root, dirs, files in os.walk(folder_path):
            rel_depth = root[len(folder_path):].count(os.sep)
            if rel_depth > 3:
                continue
            for f in files:
                f_lower = f.lower()
                if q_clean in f_lower or (q_tokens and all(tok in f_lower for tok in q_tokens)):
                    return os.path.join(root, f), f
        
        # Broader search: any token
        for root, dirs, files in os.walk(folder_path):
            rel_depth = root[len(folder_path):].count(os.sep)
            if rel_depth > 3:
                continue
            for f in files:
                f_lower = f.lower()
                if q_tokens and any(tok in f_lower for tok in q_tokens):
                    return os.path.join(root, f), f

        return None, f"Could not find document '{doc_query}' in '{folder_name}'"

_file_instance = None

def get_file_manager() -> FileManager:
    global _file_instance
    if _file_instance is None:
        _file_instance = FileManager()
    return _file_instance

