"""
Centralized System State Manager
ONLY runs on Flask server - single source of truth
"""
import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime


class SystemState:
    """Centralized system state - lives ONLY on server"""
    
    def __init__(self):
        self.lock = threading.RLock()
        
        # Person counting
        self.people_count = 0
        self.distance_history = {
            'PI1': [],  # [(distance, timestamp), ...]
            'PI2': []
        }
        
        # Alarm system
        self.alarm_active = False
        self.security_armed = False
        self.arming_countdown = None
        self.alarm_reason = None
        
        # Door states
        self.door_states = {
            'DS1': {'open': False, 'open_since': None},
            'DS2': {'open': False, 'open_since': None}
        }
        
        # Timer (PI2 kitchen timer)
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_start_time = None
        self.timer_expired = False
        self.timer_blinking = False
        self.timer_button_add_seconds = 10
        
        # Callbacks for state changes
        self.callbacks = {}
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for state changes"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def trigger_callbacks(self, event: str, data=None):
        """Trigger all callbacks for an event"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in callback: {e}")
    
    # ============ DISTANCE & MOTION TRACKING ============
    
    def add_distance_reading(self, device_id: str, distance: float):
        """Add distance reading for motion direction detection"""
        with self.lock:
            timestamp = time.time()
            history = self.distance_history.get(device_id, [])
            history.append((distance, timestamp))
            
            # Keep only last 5 seconds
            cutoff = timestamp - 5.0
            history = [(d, t) for d, t in history if t > cutoff]
            
            # Keep max 10 readings
            if len(history) > 10:
                history = history[-10:]
            
            self.distance_history[device_id] = history
    
    def detect_motion_direction(self, device_id: str) -> Optional[str]:
        """Detect if person entering or exiting based on distance trend"""
        with self.lock:
            history = self.distance_history.get(device_id, [])
            
            if len(history) < 3:
                return None
            
            distances = [d for d, t in history]
            first_avg = sum(distances[:3]) / 3
            last_avg = sum(distances[-3:]) / 3
            diff = last_avg - first_avg
            
            if abs(diff) > 20:  # 20cm threshold
                return 'entering' if diff < 0 else 'exiting'
            
            return None
    
    def update_people_count(self, delta: int):
        """Update people count"""
        with self.lock:
            old_count = self.people_count
            self.people_count = max(0, self.people_count + delta)
            
            if self.people_count != old_count:
                print(f"👥 People count: {old_count} → {self.people_count}")
                self.trigger_callbacks('people_count_changed', self.people_count)
                
                # Trigger alarm if motion detected with 0 people
                if self.people_count == 0:
                    self.trigger_callbacks('building_empty', None)
            
            return self.people_count
    
    # ============ DOOR MANAGEMENT ============
    
    def update_door_state(self, door_id: str, is_open: bool):
        """Update door state"""
        with self.lock:
            if door_id not in self.door_states:
                self.door_states[door_id] = {'open': False, 'open_since': None}
            
            was_open = self.door_states[door_id]['open']
            
            if is_open and not was_open:
                # Door just opened
                self.door_states[door_id]['open'] = True
                self.door_states[door_id]['open_since'] = time.time()
                print(f"🚪 {door_id}: OPENED")
                self.trigger_callbacks('door_opened', {'door_id': door_id})
                
            elif not is_open and was_open:
                # Door just closed
                self.door_states[door_id]['open'] = False
                self.door_states[door_id]['open_since'] = None
                print(f"🚪 {door_id}: CLOSED")
                self.trigger_callbacks('door_closed', {'door_id': door_id})
    
    def check_door_alarms(self):
        """Check if any door open too long"""
        with self.lock:
            for door_id, state in self.door_states.items():
                if state['open'] and state['open_since']:
                    duration = time.time() - state['open_since']
                    if duration > 5.0:
                        return door_id, duration
        return None, 0
    
    # ============ SECURITY SYSTEM ============
    
    def arm_security(self):
        """Arm security system with 10 second countdown"""
        with self.lock:
            if self.arming_countdown:
                return False  # Already arming
            
            def countdown():
                for i in range(10, 0, -1):
                    print(f"Arming in {i}...")
                    time.sleep(1)
                
                with self.lock:
                    self.security_armed = True
                    self.arming_countdown = None
                    print("Security system ARMED")
                    self.trigger_callbacks('security_armed', True)
            
            self.arming_countdown = threading.Thread(target=countdown, daemon=True)
            self.arming_countdown.start()
            return True
    
    def disarm_security(self):
        """Disarm security system"""
        with self.lock:
            if self.arming_countdown:
                self.arming_countdown = None  # Cancel countdown
            
            was_armed = self.security_armed
            self.security_armed = False
            
            if was_armed:
                print("🔓 Security system DISARMED")
                self.trigger_callbacks('security_armed', False)
            
            # Also clear alarm
            if self.alarm_active:
                self.clear_alarm()
    
    # ============ ALARM SYSTEM ============
    
    def trigger_alarm(self, reason: str):
        """Trigger alarm"""
        with self.lock:
            if not self.alarm_active:
                self.alarm_active = True
                self.alarm_reason = reason
                print(f"ALARM TRIGGERED: {reason}")
                self.trigger_callbacks('alarm_triggered', {'reason': reason})
    
    def clear_alarm(self):
        """Clear alarm"""
        with self.lock:
            if self.alarm_active:
                self.alarm_active = False
                self.alarm_reason = None
                print("Alarm cleared")
                self.trigger_callbacks('alarm_cleared', None)
    
    # ============ TIMER SYSTEM ============
    
    def set_timer(self, seconds: int):
        """Set timer duration"""
        with self.lock:
            self.timer_seconds = seconds
            self.timer_expired = False
            self.timer_blinking = False
            print(f"Timer set: {seconds}s")
            self.trigger_callbacks('timer_updated', self.get_timer_state())
    
    def start_timer(self):
        """Start timer"""
        with self.lock:
            if self.timer_seconds > 0:
                self.timer_running = True
                self.timer_start_time = time.time()
                print("Timer started")
                self.trigger_callbacks('timer_updated', self.get_timer_state())
    
    def stop_timer(self):
        """Stop timer"""
        with self.lock:
            self.timer_running = False
            self.timer_start_time = None
            self.timer_blinking = False
            print("Timer stopped")
            self.trigger_callbacks('timer_updated', self.get_timer_state())
    
    def get_timer_remaining(self) -> int:
        """Get remaining time"""
        with self.lock:
            if not self.timer_running or not self.timer_start_time:
                return self.timer_seconds
            
            elapsed = time.time() - self.timer_start_time
            remaining = max(0, self.timer_seconds - int(elapsed))
            
            if remaining == 0 and not self.timer_expired:
                self.timer_expired = True
                self.timer_blinking = True
                self.timer_running = False
                print("Timer EXPIRED!")
                self.trigger_callbacks('timer_expired', None)
            
            return remaining
    
    def add_timer_seconds(self, seconds: int):
        """Add seconds to timer"""
        with self.lock:
            if self.timer_blinking:
                # Stop blinking
                self.timer_blinking = False
                self.timer_expired = False
                self.timer_seconds = 0
            else:
                self.timer_seconds += seconds
                if self.timer_running and self.timer_start_time:
                    self.timer_start_time -= seconds
            
            print(f"Added {seconds}s. Total: {self.timer_seconds}s")
            self.trigger_callbacks('timer_updated', self.get_timer_state())
    
    def get_timer_state(self) -> dict:
        """Get timer state"""
        return {
            'seconds': self.get_timer_remaining() if self.timer_running else self.timer_seconds,
            'running': self.timer_running,
            'expired': self.timer_expired,
            'blinking': self.timer_blinking
        }
    
    # ============ STATE EXPORT ============
    
    def get_full_state(self) -> dict:
        """Get complete system state (thread-safe)"""
        with self.lock:
            return {
                'people_count': self.people_count,
                'security_armed': self.security_armed,
                'alarm_active': self.alarm_active,
                'alarm_reason': self.alarm_reason,
                'door_states': self.door_states.copy(),
                'timer': self.get_timer_state()
            }


system_state = SystemState()