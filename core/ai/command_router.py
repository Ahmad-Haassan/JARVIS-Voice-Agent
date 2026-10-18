"""
Command Router — maps parsed intents to corresponding skill executors.
"""
from dataclasses import dataclass
from typing import Any, Optional
from core.utils.logger import get_logger
from core.skills.system_control import get_system_control
from core.skills.whatsapp import get_whatsapp
from core.skills.file_manager import get_file_manager
from core.skills.web_search import get_web_search
from core.skills.weather import get_weather
from core.skills.timer_alarm import get_timer

logger = get_logger("ai.router")

@dataclass
class CommandResult:
    success: bool
    response: str
    data: Optional[Any] = None

class CommandRouter:
    def route(self, action: dict) -> CommandResult:
        intent = action.get("intent", "chat")
        entities = action.get("entities") or {}
        spoken_resp = action.get("response", "")

        logger.info(f"Routing intent: '{intent}' with entities: {entities}")

        try:
            # 1. Open App
            if intent == "open_app":
                app_name = entities.get("app", "")
                success = get_system_control().open_app(app_name)
                resp = f"Opened {app_name}." if success else f"Could not open {app_name}."
                return CommandResult(success=success, response=resp)

            # 2. Close App
            elif intent == "close_app":
                app_name = entities.get("app", "")
                success = get_system_control().close_app(app_name)
                resp = f"Closed {app_name}." if success else f"Could not find or close {app_name}."
                return CommandResult(success=success, response=resp)

            # 3. Work Mode
            elif intent == "work_mode":
                success = get_system_control().work_mode()
                resp = "Work mode initialized. Antigravity IDE, Google Chrome, and terminal opened." if success else "Failed to launch work mode."
                return CommandResult(success=success, response=resp)

            # 4. System Control (Diagnostics, Screenshot, Power)
            elif intent == "system_control":
                sub_action = entities.get("action", "")
                sys_ctrl = get_system_control()

                if sub_action == "diagnostics":
                    diag = sys_ctrl.get_system_diagnostics()
                    return CommandResult(success=True, response=f"System Diagnostics: {diag}", data=diag)
                elif sub_action == "screenshot":
                    path = sys_ctrl.take_screenshot()
                    resp = "Screenshot captured successfully." if path else "Could not capture screenshot. If Windows is locked, please unlock your PC first."
                    return CommandResult(success=bool(path), response=resp, data=path)
                elif sub_action in ["lock", "unlock", "sleep", "restart", "shutdown"]:
                    pin = entities.get("pin", "")
                    success = sys_ctrl.system_power(sub_action, pin=pin)
                    resp = "Workstation screen awakened and unlocked." if sub_action == "unlock" else f"Executed system {sub_action}."
                    return CommandResult(success=success, response=resp)
                else:
                    return CommandResult(success=True, response=spoken_resp or "System action completed.")

            # 5. Computer Camera Feed
            elif intent == "camera":
                from core.skills.camera import get_camera
                cam = get_camera()
                path = cam.capture_snapshot()
                resp = "Computer camera feed online." if path else "Could not access computer camera."
                return CommandResult(success=bool(path), response=resp, data=path)

            # 5.5 Autonomous Computer Control (Stonic AI Workflows)
            elif intent == "computer_agent":
                from core.skills.computer_agent import get_computer_agent
                agent = get_computer_agent()
                action_type = entities.get("action", "")

                if action_type == "snap":
                    direction = entities.get("direction", "max")
                    success = agent.workflow_snap_window(direction)
                    return CommandResult(success=success, response=f"Window snapped {direction}.")
                elif action_type == "ask_ai":
                    prompt_text = entities.get("prompt", "")
                    success = agent.workflow_ask_ai(prompt_text)
                    return CommandResult(success=success, response=f"AI Prompt '{prompt_text[:30]}...' dispatched.")
                elif action_type == "notepad":
                    content = entities.get("content", "")
                    success = agent.workflow_quick_notepad(content)
                    return CommandResult(success=success, response="Autonomous memo typed into Notepad.")
                elif action_type == "switch_window":
                    success = agent.workflow_switch_window()
                    return CommandResult(success=success, response="Switched active window.")
                elif action_type == "scroll":
                    amount = entities.get("amount", -400)
                    success = agent.scroll(amount)
                    return CommandResult(success=success, response="Scrolled page.")
                else:
                    return CommandResult(success=True, response="Computer agent action executed.")

            # 6. WhatsApp
            elif intent == "send_whatsapp":
                contact = entities.get("contact", "")
                message = entities.get("message", "")
                success = get_whatsapp().send_message(contact, message)
                resp = f"Message dispatched to {contact} on WhatsApp." if success else "Failed to send WhatsApp message."
                return CommandResult(success=success, response=resp)

            # 6. YouTube Playback
            elif intent == "youtube_play":
                query = entities.get("query", "music")
                success = get_web_search().play_youtube(query)
                resp = f"Playing {query} on YouTube." if success else "Could not open YouTube."
                return CommandResult(success=success, response=resp)

            # 7. File Actions
            elif intent == "file_action":
                name = entities.get("name", "New Folder")
                path = get_file_manager().create_desktop_folder(name)
                resp = f"Created desktop folder '{name}'." if path else "Failed to create folder."
                return CommandResult(success=bool(path), response=resp, data=path)

            # 8. Weather
            elif intent == "weather":
                city = entities.get("city")
                weather_info = get_weather().get_weather(city)
                return CommandResult(success=True, response=weather_info, data=weather_info)

            # 9. Web Search
            elif intent == "search_web":
                query = entities.get("query", "")
                summary = get_web_search().search(query)
                return CommandResult(success=True, response=summary, data=summary)

            # 10. General Chat
            else:
                return CommandResult(success=True, response=spoken_resp or "Command received.")

        except Exception as e:
            logger.error(f"Router execution error for intent '{intent}': {e}")
            return CommandResult(success=False, response=f"An error occurred executing command: {e}")

_router_instance = None

def get_router() -> CommandRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = CommandRouter()
    return _router_instance
