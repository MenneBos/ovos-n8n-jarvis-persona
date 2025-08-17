import time
import threading
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ovos_utils.log import LOG

logger = LOG.create_logger(__name__)


class AlarmController:
    def __init__(self, config: Dict[str, Any], audio_controller=None):
        self.config = config
        self.audio_controller = audio_controller
        self.alarms = {}
        self.alarm_threads = {}
        self.alarm_counter = 0
        self.running = True
        self.snooze_duration = config.get("snooze_duration_minutes", 5)
        
        self.media_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "media"
        )
        self.alarm_sound = os.path.join(self.media_path, "alarm.mp3")
        
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info(f"AlarmController initialized with media path: {self.media_path}")
    
    def set_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        time_str = params.get("time")
        name = params.get("name", f"alarm_{self.alarm_counter}")
        repeat_daily = params.get("repeat_daily", False)
        label = params.get("label", "")
        
        if not time_str:
            return {
                "success": False,
                "error": "No time specified for alarm"
            }
        
        try:
            alarm_time = self._parse_time(time_str)
            
            if name in self.alarms and self.alarms[name]["active"]:
                return {
                    "success": False,
                    "error": f"Alarm '{name}' already exists and is active"
                }
            
            self.alarm_counter += 1
            
            alarm_info = {
                "name": name,
                "time": alarm_time,
                "repeat_daily": repeat_daily,
                "label": label,
                "active": True,
                "snoozed": False,
                "snooze_until": None,
                "created_at": datetime.now(),
                "last_triggered": None
            }
            
            self.alarms[name] = alarm_info
            
            time_str_formatted = alarm_time.strftime("%H:%M")
            repeat_str = " (daily)" if repeat_daily else ""
            
            return {
                "success": True,
                "message": f"Alarm '{name}' set for {time_str_formatted}{repeat_str}",
                "alarm_id": name,
                "time": time_str_formatted,
                "repeat_daily": repeat_daily,
                "label": label
            }
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid time format: {str(e)}"
            }
    
    def _parse_time(self, time_str: str) -> datetime:
        now = datetime.now()
        
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                
                alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if alarm_time <= now:
                    alarm_time += timedelta(days=1)
                
                return alarm_time
            elif len(parts) == 3:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2])
                
                alarm_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
                
                if alarm_time <= now:
                    alarm_time += timedelta(days=1)
                
                return alarm_time
        
        if time_str.lower().endswith(("am", "pm")):
            time_str = time_str.replace(" ", "")
            
            if "am" in time_str.lower():
                time_part = time_str.lower().replace("am", "")
                is_pm = False
            else:
                time_part = time_str.lower().replace("pm", "")
                is_pm = True
            
            if ":" in time_part:
                parts = time_part.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            else:
                hour = int(time_part)
                minute = 0
            
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if alarm_time <= now:
                alarm_time += timedelta(days=1)
            
            return alarm_time
        
        raise ValueError(f"Unable to parse time: {time_str}")
    
    def cancel_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        
        if not name:
            active_alarms = [n for n, info in self.alarms.items() if info["active"]]
            if len(active_alarms) == 1:
                name = active_alarms[0]
            elif len(active_alarms) > 1:
                return {
                    "success": False,
                    "error": "Multiple alarms active. Please specify which alarm to cancel.",
                    "active_alarms": active_alarms
                }
            else:
                return {
                    "success": False,
                    "error": "No active alarms to cancel"
                }
        
        if name not in self.alarms:
            return {
                "success": False,
                "error": f"Alarm '{name}' not found"
            }
        
        self.alarms[name]["active"] = False
        
        return {
            "success": True,
            "message": f"Alarm '{name}' cancelled"
        }
    
    def delete_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        
        if not name:
            return {
                "success": False,
                "error": "Please specify alarm name to delete"
            }
        
        if name not in self.alarms:
            return {
                "success": False,
                "error": f"Alarm '{name}' not found"
            }
        
        del self.alarms[name]
        
        return {
            "success": True,
            "message": f"Alarm '{name}' deleted"
        }
    
    def snooze_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        duration_minutes = params.get("duration", self.snooze_duration)
        
        if not name:
            recently_triggered = []
            now = datetime.now()
            for n, info in self.alarms.items():
                if info["last_triggered"] and (now - info["last_triggered"]).seconds < 60:
                    recently_triggered.append(n)
            
            if len(recently_triggered) == 1:
                name = recently_triggered[0]
            else:
                return {
                    "success": False,
                    "error": "Please specify which alarm to snooze"
                }
        
        if name not in self.alarms:
            return {
                "success": False,
                "error": f"Alarm '{name}' not found"
            }
        
        alarm = self.alarms[name]
        alarm["snoozed"] = True
        alarm["snooze_until"] = datetime.now() + timedelta(minutes=duration_minutes)
        
        return {
            "success": True,
            "message": f"Alarm '{name}' snoozed for {duration_minutes} minutes",
            "snooze_until": alarm["snooze_until"].strftime("%H:%M:%S")
        }
    
    def list_alarms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        alarm_list = []
        
        for name, info in self.alarms.items():
            alarm_data = {
                "name": name,
                "time": info["time"].strftime("%H:%M"),
                "active": info["active"],
                "repeat_daily": info["repeat_daily"],
                "label": info["label"],
                "snoozed": info["snoozed"]
            }
            
            if info["snoozed"] and info["snooze_until"]:
                alarm_data["snooze_until"] = info["snooze_until"].strftime("%H:%M:%S")
            
            if info["last_triggered"]:
                alarm_data["last_triggered"] = info["last_triggered"].strftime("%Y-%m-%d %H:%M:%S")
            
            alarm_list.append(alarm_data)
        
        return {
            "success": True,
            "alarms": alarm_list,
            "count": len(alarm_list)
        }
    
    def enable_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        
        if not name:
            return {
                "success": False,
                "error": "Please specify alarm name to enable"
            }
        
        if name not in self.alarms:
            return {
                "success": False,
                "error": f"Alarm '{name}' not found"
            }
        
        self.alarms[name]["active"] = True
        self.alarms[name]["snoozed"] = False
        self.alarms[name]["snooze_until"] = None
        
        return {
            "success": True,
            "message": f"Alarm '{name}' enabled"
        }
    
    def disable_alarm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        
        if not name:
            return {
                "success": False,
                "error": "Please specify alarm name to disable"
            }
        
        if name not in self.alarms:
            return {
                "success": False,
                "error": f"Alarm '{name}' not found"
            }
        
        self.alarms[name]["active"] = False
        
        return {
            "success": True,
            "message": f"Alarm '{name}' disabled"
        }
    
    def _scheduler_loop(self):
        logger.info("Alarm scheduler started")
        
        while self.running:
            try:
                now = datetime.now()
                
                for name, alarm in list(self.alarms.items()):
                    if not alarm["active"]:
                        continue
                    
                    # Check if alarm is snoozed
                    if alarm["snoozed"] and alarm["snooze_until"]:
                        if now >= alarm["snooze_until"]:
                            alarm["snoozed"] = False
                            alarm["snooze_until"] = None
                            self._trigger_alarm(name)
                        continue
                    
                    # Check regular alarm time
                    alarm_time = alarm["time"]
                    
                    # Check if it's time to trigger the alarm
                    if (now.hour == alarm_time.hour and 
                        now.minute == alarm_time.minute and
                        now.second < 2):  # Within first 2 seconds of the minute
                        
                        # Check if already triggered recently
                        if alarm["last_triggered"]:
                            time_since_last = (now - alarm["last_triggered"]).seconds
                            if time_since_last < 60:  # Don't trigger again within a minute
                                continue
                        
                        self._trigger_alarm(name)
                        
                        # Update alarm time for next day if daily repeat
                        if alarm["repeat_daily"]:
                            alarm["time"] = alarm_time + timedelta(days=1)
                        else:
                            alarm["active"] = False
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in alarm scheduler: {e}", exc_info=True)
                time.sleep(1)
    
    def _trigger_alarm(self, alarm_name: str):
        if alarm_name not in self.alarms:
            return
        
        alarm = self.alarms[alarm_name]
        alarm["last_triggered"] = datetime.now()
        
        logger.info(f"Triggering alarm '{alarm_name}'")
        
        # Play alarm sound
        if self.audio_controller and os.path.exists(self.alarm_sound):
            try:
                # Play alarm sound in a loop for 30 seconds or until stopped
                alarm_thread = threading.Thread(
                    target=self._play_alarm_sound,
                    args=(alarm_name,)
                )
                alarm_thread.daemon = True
                alarm_thread.start()
                self.alarm_threads[alarm_name] = alarm_thread
                
            except Exception as e:
                logger.error(f"Failed to play alarm sound: {e}")
        else:
            logger.warning("Audio controller not available or alarm sound file not found")
        
        # Log the alarm trigger
        label_str = f" - {alarm['label']}" if alarm['label'] else ""
        logger.info(f"ALARM: {alarm_name}{label_str} triggered at {datetime.now().strftime('%H:%M:%S')}")
    
    def _play_alarm_sound(self, alarm_name: str):
        """Play alarm sound for 30 seconds or until stopped/snoozed"""
        start_time = time.time()
        max_duration = 30  # seconds
        
        while time.time() - start_time < max_duration:
            if alarm_name not in self.alarms:
                break
            
            alarm = self.alarms[alarm_name]
            if not alarm["active"] or alarm["snoozed"]:
                break
            
            # Play the alarm sound
            self.audio_controller.play_file({"file": self.alarm_sound})
            time.sleep(2)  # Wait 2 seconds between plays
        
        # Clean up thread reference
        if alarm_name in self.alarm_threads:
            del self.alarm_threads[alarm_name]
    
    def stop_alarm_sound(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop currently playing alarm sound"""
        name = params.get("name")
        
        if name and name in self.alarm_threads:
            # Stop specific alarm
            if name in self.alarms:
                self.alarms[name]["snoozed"] = True  # This will stop the sound loop
                self.alarms[name]["snooze_until"] = datetime.now()  # Immediately expire snooze
            return {
                "success": True,
                "message": f"Alarm sound for '{name}' stopped"
            }
        else:
            # Stop all alarm sounds
            for alarm_name in list(self.alarm_threads.keys()):
                if alarm_name in self.alarms:
                    self.alarms[alarm_name]["snoozed"] = True
                    self.alarms[alarm_name]["snooze_until"] = datetime.now()
            
            if self.audio_controller:
                self.audio_controller.stop({})
            
            return {
                "success": True,
                "message": "All alarm sounds stopped"
            }
    
    def clear_all_alarms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.alarms.clear()
        self.alarm_threads.clear()
        
        return {
            "success": True,
            "message": "All alarms cleared"
        }
    
    def shutdown(self):
        """Clean shutdown of the alarm controller"""
        self.running = False
        if hasattr(self, 'scheduler_thread'):
            self.scheduler_thread.join(timeout=2)