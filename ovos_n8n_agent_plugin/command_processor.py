import logging
from typing import Dict, Any, Optional
from ovos_utils.log import LOG
from .media_controllers import TimerController, AlarmController

logger = LOG.create_logger(__name__)


class CommandProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Note: Timer and Alarm controllers may need audio playback capability
        # Consider using Spotify MCP for alarm/timer sounds
        self.timer_controller = TimerController(config.get("timer", {}), None)
        self.alarm_controller = AlarmController(config.get("alarm", {}), None)
        
        self.tool_handlers = {
            "timer": self._handle_timer,
            "alarm": self._handle_alarm,
        }
        
        logger.info("CommandProcessor initialized with handlers for: " + ", ".join(self.tool_handlers.keys()))
    
    def process_command(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = tool_call.get("tool", "").lower()
        action = tool_call.get("action", "")
        params = tool_call.get("params", {})
        
        logger.debug(f"Processing tool call: {tool_name}.{action} with params: {params}")
        
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            logger.warning(f"No handler found for tool: {tool_name}")
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "tool": tool_name,
                "action": action
            }
        
        try:
            result = handler(action, params)
            result["tool"] = tool_name
            result["action"] = action
            return result
            
        except Exception as e:
            logger.error(f"Error handling {tool_name}.{action}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "action": action
            }
    
    
    
    
    def _handle_timer(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        action_map = {
            "start": self.timer_controller.start_timer,
            "stop": self.timer_controller.stop_timer,
            "cancel": self.timer_controller.cancel_timer,
            "pause": self.timer_controller.pause_timer,
            "resume": self.timer_controller.resume_timer,
            "status": self.timer_controller.get_timer_status,
            "clear": self.timer_controller.clear_all_timers,
        }
        
        handler = action_map.get(action)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown timer action: {action}"
            }
        
        return handler(params)
    
    def _handle_alarm(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        action_map = {
            "set": self.alarm_controller.set_alarm,
            "cancel": self.alarm_controller.cancel_alarm,
            "delete": self.alarm_controller.delete_alarm,
            "snooze": self.alarm_controller.snooze_alarm,
            "list": self.alarm_controller.list_alarms,
            "enable": self.alarm_controller.enable_alarm,
            "disable": self.alarm_controller.disable_alarm,
            "stop": self.alarm_controller.stop_alarm_sound,
            "clear": self.alarm_controller.clear_all_alarms,
        }
        
        handler = action_map.get(action)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown alarm action: {action}"
            }
        
        return handler(params)