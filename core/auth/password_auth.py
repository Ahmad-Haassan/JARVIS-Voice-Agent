import hashlib
import os
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("auth.password")

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt or SHA-256 fallback."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")
    else:
        salt = os.urandom(16).hex()
        digest = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
        return f"sha256${salt}${digest}"

def check_password(plain: str, hashed: str) -> bool:
    """Verify plaintext against stored hash."""
    if not hashed or not plain:
        return False
    try:
        if hashed.startswith("sha256$"):
            parts = hashed.split("$")
            salt, digest = parts[1], parts[2]
            return hashlib.sha256((salt + plain).encode("utf-8")).hexdigest() == digest
        elif HAS_BCRYPT:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        else:
            return False
    except Exception as e:
        logger.error(f"Password check failed: {e}")
        return False

def is_password_set() -> bool:
    pwd_hash = cfg.get("auth", "password_hash", "")
    return bool(pwd_hash and pwd_hash.strip())

def set_password(plain: str) -> bool:
    hashed = hash_password(plain)
    cfg.set_value("auth", "password_hash", hashed)
    logger.info("New access password configured successfully.")
    return True
