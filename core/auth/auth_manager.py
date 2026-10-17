from core.auth.password_auth import is_password_set, check_password, set_password
from core.auth.voice_auth import is_voice_enrolled, verify_voice
from core.utils import config as cfg
from core.utils.logger import get_logger

logger = get_logger("auth.manager")

class AuthManager:
    def __init__(self):
        self._authenticated = False

    def is_first_run(self) -> bool:
        """Returns True if no password has been setup yet."""
        return not is_password_set()

    def setup_password(self, password: str) -> bool:
        """Configures initial password for JARVIS."""
        success = set_password(password)
        if success:
            self._authenticated = True
        return success

    def login_password(self, password: str) -> bool:
        """Verifies password and sets authenticated state."""
        stored_hash = cfg.get("auth", "password_hash", "")
        if check_password(password, stored_hash):
            self._authenticated = True
            logger.info("User logged in via password successfully.")
            return True
        logger.warning("Failed login attempt.")
        return False

    def is_authenticated(self) -> bool:
        return self._authenticated

    def logout(self):
        self._authenticated = False
        logger.info("User logged out.")

_auth_manager_instance = None

def get_auth_manager() -> AuthManager:
    global _auth_manager_instance
    if _auth_manager_instance is None:
        _auth_manager_instance = AuthManager()
    return _auth_manager_instance
