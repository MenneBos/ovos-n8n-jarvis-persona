import time
import threading
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ovos_utils.log import LOG

logger = LOG.create_logger(__name__)


class TimerController:
    def __init__(self, config: Dict[str, Any], audio_controller=None):
        self.config = config
        self.audio_controller = audio_controller
        self.timers = {}
        self.timer_threads = {}
        self.timer_counter = 0
        self.media_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "media"
        )
        self.timesup_sound = os.path.join(self.media_path, "timesup.mp3")
        logger.info(f"TimerController initialized with media path: {self.media_path}")
    
    def start_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        duration_ms = params.get("duration", None)
        timer_name = params.get("name", f"timer_{self.timer_counter}")
        self.timer_counter += 1
        
        if timer_name in self.timers and self.timers[timer_name].get("active"):
            return {
                "success": False,
                "error": f"Timer '{timer_name}' is already running"
            }
        
        timer_info = {
            "name": timer_name,
            "start_time": time.time(),
            "duration_ms": duration_ms,
            "active": True,
            "paused": False,
            "elapsed_when_paused": 0
        }
        
        self.timers[timer_name] = timer_info
        
        if duration_ms:
            duration_seconds = duration_ms / 1000.0
            timer_thread = threading.Thread(
                target=self._run_timer,
                args=(timer_name, duration_seconds)
            )
            timer_thread.daemon = True
            timer_thread.start()
            self.timer_threads[timer_name] = timer_thread
            
            return {
                "success": True,
                "message": f"Timer '{timer_name}' started for {duration_seconds} seconds",
                "timer_id": timer_name,
                "duration_ms": duration_ms
            }
        else:
            return {
                "success": True,
                "message": f"Open-ended timer '{timer_name}' started",
                "timer_id": timer_name,
                "open_ended": True
            }
    
    def _run_timer(self, timer_name: str, duration_seconds: float):
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            if timer_name not in self.timers or not self.timers[timer_name]["active"]:
                return
            
            if self.timers[timer_name]["paused"]:
                time.sleep(0.1)
                continue
                
            time.sleep(0.1)
        
        if timer_name in self.timers and self.timers[timer_name]["active"]:
            self.timers[timer_name]["active"] = False
            self._play_timer_sound()
            logger.info(f"Timer '{timer_name}' completed after {duration_seconds} seconds")
    
    def _play_timer_sound(self):
        if self.audio_controller and os.path.exists(self.timesup_sound):
            try:
                self.audio_controller.play_file({"file": self.timesup_sound})
                logger.info("Timer completion sound played")
            except Exception as e:
                logger.error(f"Failed to play timer sound: {e}")
        else:
            logger.warning("Audio controller not available or sound file not found")
    
    def stop_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timer_name = params.get("name", None)
        
        if not timer_name:
            active_timers = [name for name, info in self.timers.items() if info["active"]]
            if len(active_timers) == 1:
                timer_name = active_timers[0]
            elif len(active_timers) > 1:
                return {
                    "success": False,
                    "error": "Multiple timers active. Please specify which timer to stop.",
                    "active_timers": active_timers
                }
            else:
                return {
                    "success": False,
                    "error": "No active timers to stop"
                }
        
        if timer_name not in self.timers:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' not found"
            }
        
        timer_info = self.timers[timer_name]
        if not timer_info["active"]:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' is not active"
            }
        
        elapsed_ms = self._get_elapsed_time(timer_name)
        timer_info["active"] = False
        
        return {
            "success": True,
            "message": f"Timer '{timer_name}' stopped",
            "elapsed_ms": elapsed_ms,
            "elapsed_seconds": elapsed_ms / 1000.0
        }
    
    def cancel_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timer_name = params.get("name", None)
        
        if not timer_name:
            active_timers = [name for name, info in self.timers.items() if info["active"]]
            if len(active_timers) == 1:
                timer_name = active_timers[0]
            elif len(active_timers) > 1:
                return {
                    "success": False,
                    "error": "Multiple timers active. Please specify which timer to cancel.",
                    "active_timers": active_timers
                }
            else:
                return {
                    "success": False,
                    "error": "No active timers to cancel"
                }
        
        if timer_name not in self.timers:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' not found"
            }
        
        self.timers[timer_name]["active"] = False
        
        if timer_name in self.timer_threads:
            del self.timer_threads[timer_name]
        
        return {
            "success": True,
            "message": f"Timer '{timer_name}' cancelled"
        }
    
    def pause_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timer_name = params.get("name", None)
        
        if not timer_name:
            active_timers = [name for name, info in self.timers.items() 
                            if info["active"] and not info["paused"]]
            if len(active_timers) == 1:
                timer_name = active_timers[0]
            else:
                return {
                    "success": False,
                    "error": "Please specify which timer to pause"
                }
        
        if timer_name not in self.timers:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' not found"
            }
        
        timer_info = self.timers[timer_name]
        if timer_info["paused"]:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' is already paused"
            }
        
        timer_info["paused"] = True
        timer_info["elapsed_when_paused"] = self._get_elapsed_time(timer_name)
        
        return {
            "success": True,
            "message": f"Timer '{timer_name}' paused"
        }
    
    def resume_timer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timer_name = params.get("name", None)
        
        if not timer_name:
            paused_timers = [name for name, info in self.timers.items() 
                           if info["active"] and info["paused"]]
            if len(paused_timers) == 1:
                timer_name = paused_timers[0]
            else:
                return {
                    "success": False,
                    "error": "Please specify which timer to resume"
                }
        
        if timer_name not in self.timers:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' not found"
            }
        
        timer_info = self.timers[timer_name]
        if not timer_info["paused"]:
            return {
                "success": False,
                "error": f"Timer '{timer_name}' is not paused"
            }
        
        timer_info["paused"] = False
        timer_info["start_time"] = time.time() - (timer_info["elapsed_when_paused"] / 1000.0)
        
        return {
            "success": True,
            "message": f"Timer '{timer_name}' resumed"
        }
    
    def get_timer_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timer_name = params.get("name", None)
        
        if timer_name:
            if timer_name not in self.timers:
                return {
                    "success": False,
                    "error": f"Timer '{timer_name}' not found"
                }
            
            timer_info = self.timers[timer_name]
            elapsed_ms = self._get_elapsed_time(timer_name) if timer_info["active"] else 0
            
            status = {
                "name": timer_name,
                "active": timer_info["active"],
                "paused": timer_info["paused"],
                "elapsed_ms": elapsed_ms,
                "elapsed_seconds": elapsed_ms / 1000.0
            }
            
            if timer_info["duration_ms"]:
                remaining_ms = max(0, timer_info["duration_ms"] - elapsed_ms)
                status["duration_ms"] = timer_info["duration_ms"]
                status["remaining_ms"] = remaining_ms
                status["remaining_seconds"] = remaining_ms / 1000.0
            
            return {
                "success": True,
                "timer": status
            }
        else:
            all_timers = []
            for name, info in self.timers.items():
                elapsed_ms = self._get_elapsed_time(name) if info["active"] else 0
                timer_status = {
                    "name": name,
                    "active": info["active"],
                    "paused": info["paused"],
                    "elapsed_ms": elapsed_ms,
                    "elapsed_seconds": elapsed_ms / 1000.0
                }
                
                if info["duration_ms"]:
                    remaining_ms = max(0, info["duration_ms"] - elapsed_ms)
                    timer_status["duration_ms"] = info["duration_ms"]
                    timer_status["remaining_ms"] = remaining_ms
                    timer_status["remaining_seconds"] = remaining_ms / 1000.0
                
                all_timers.append(timer_status)
            
            return {
                "success": True,
                "timers": all_timers
            }
    
    def _get_elapsed_time(self, timer_name: str) -> float:
        if timer_name not in self.timers:
            return 0
        
        timer_info = self.timers[timer_name]
        
        if timer_info["paused"]:
            return timer_info["elapsed_when_paused"]
        
        elapsed_seconds = time.time() - timer_info["start_time"]
        return elapsed_seconds * 1000
    
    def clear_all_timers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        for timer_name in list(self.timers.keys()):
            self.timers[timer_name]["active"] = False
        
        self.timers.clear()
        self.timer_threads.clear()
        
        return {
            "success": True,
            "message": "All timers cleared"
        }