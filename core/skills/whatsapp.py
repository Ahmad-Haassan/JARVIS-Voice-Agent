"""
WhatsApp Desktop Automation Skill — send messages via Windows WhatsApp app.
"""
import os
import time
import pyperclip
from core.utils.logger import get_logger

logger = get_logger("skills.whatsapp")

class WhatsAppAutomation:
    def send_message(self, contact: str, message: str) -> bool:
        logger.info(f"Dispatching WhatsApp message to '{contact}': '{message}'")
        try:
            import pyautogui

            # Launch/focus WhatsApp desktop app
            os.system("start whatsapp:")
            time.sleep(2.0)

            # Start new chat or search contact (Ctrl+N in Windows WhatsApp)
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(0.8)

            # Copy contact name to clipboard and paste to avoid typing issues with non-ASCII
            pyperclip.copy(contact)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.2)

            # Select the contact
            pyautogui.press('enter')
            time.sleep(0.8)

            # Paste and send message
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.4)
            pyautogui.press('enter')

            logger.info("WhatsApp message successfully dispatched.")
            return True
        except Exception as e:
            logger.error(f"WhatsApp automation error: {e}")
            return False

_wa_instance = None

def get_whatsapp() -> WhatsAppAutomation:
    global _wa_instance
    if _wa_instance is None:
        _wa_instance = WhatsAppAutomation()
    return _wa_instance
