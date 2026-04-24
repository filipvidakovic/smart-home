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
        self.alarm_source = None
        self.alarm_metadata = {}
        
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

        self.led_states = {
            'DL1': {'on': False, 'last_changed': None},
            'DL2': {'on': False, 'last_changed': None}
        }

        # BRGB lamp state (PI3)
        self.brgb_state = {
            'on': False,
            'color': 'off',
            'color_index': 0,
            'last_changed': None
        }
        
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
            
            # If no distance data at all, assume entering (person approaching to trigger motion)
            if len(history) == 0:
                return 'entering'
            
            # With 1 reading, use a default or require more data
            if len(history) == 1:
                return None  # Not enough data yet
            
            distances = [d for d, t in history]
            
            # For 2 readings, compare first and last
            if len(history) == 2:
                diff = distances[-1] - distances[0]
                if abs(diff) > 10:  # 10cm threshold
                    return 'entering' if diff < 0 else 'exiting'
                return None  # Motion but distance not changing enough
            
            # For 3+ readings, use averages (more stable)
            first_avg = sum(distances[:3]) / 3
            last_avg = sum(distances[-3:]) / 3
            diff = last_avg - first_avg
            
            if abs(diff) > 15:  # 15cm threshold
                return 'entering' if diff < 0 else 'exiting'
            
            return None
    
    def update_people_count(self, delta: int):
        """Update people count"""
        with self.lock:
            old_count = self.people_count
            self.people_count = max(0, self.people_count + delta)
            
            # SIMULATION: Reset to 0 when reaching 3 people
            if self.people_count == 3:
                print(f"🔄 SIMULATION: Building reached capacity (3), resetting to 0 (simulating evacuation)")
                self.people_count = 0
            
            if self.people_count != old_count:
                print(f"👥 People count: {old_count} → {self.people_count}")
                self.trigger_callbacks('people_count_changed', self.people_count)
                
                # Trigger alarm if motion detected with 0 people
                if self.people_count == 0:
                    self.trigger_callbacks('building_empty', None)
            
            return self.people_count
        
    def update_led_state(self, led_id: str, is_on: bool):
        """Update LED state"""
        with self.lock:
            if led_id not in self.led_states:
                self.led_states[led_id] = {'on': False, 'last_changed': None}
            
            was_on = self.led_states[led_id]['on']
            
            if is_on != was_on:
                self.led_states[led_id]['on'] = is_on
                self.led_states[led_id]['last_changed'] = time.time()
                print(f"💡 {led_id}: {'ON' if is_on else 'OFF'}")
                self.trigger_callbacks('led_state_changed', {'led_id': led_id, 'on': is_on})

    def update_brgb_state(self, *, on: Optional[bool] = None, color: Optional[str] = None, color_index: Optional[int] = None):
        """Update BRGB lamp state."""
        with self.lock:
            changed = False

            if on is not None and self.brgb_state['on'] != on:
                self.brgb_state['on'] = on
                changed = True

            if color is not None and self.brgb_state['color'] != color:
                self.brgb_state['color'] = color
                changed = True

            if color_index is not None and self.brgb_state['color_index'] != color_index:
                self.brgb_state['color_index'] = color_index
                changed = True

            if changed:
                self.brgb_state['last_changed'] = time.time()
                print(f"🌈 BRGB: {'ON' if self.brgb_state['on'] else 'OFF'} - {self.brgb_state['color'].upper()}")
                self.trigger_callbacks('brgb_state_changed', self.brgb_state.copy())
    
    
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

                # Auto-clear only door-timeout alarm when that same door changes state
                if (
                    self.alarm_active
                    and self.alarm_source == 'door_timeout'
                    and self.alarm_metadata.get('door_id') == door_id
                ):
                    print(f"✅ {door_id} state changed -> clearing door-timeout alarm")
                    self.clear_alarm()
    
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
    
    def trigger_alarm(self, reason: str, source: str = 'generic', metadata: Optional[Dict] = None):
        """Trigger alarm"""
        with self.lock:
            if not self.alarm_active:
                self.alarm_active = True
                self.alarm_reason = reason
                self.alarm_source = source
                self.alarm_metadata = metadata or {}
                print(f"ALARM TRIGGERED: {reason}")
                self.trigger_callbacks('alarm_triggered', {'reason': reason})
    
    def clear_alarm(self):
        """Clear alarm"""
        with self.lock:
            if self.alarm_active:
                self.alarm_active = False
                self.alarm_reason = None
                self.alarm_source = None
                self.alarm_metadata = {}
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
            timer_state = self.get_timer_state()
            return {
                'people_count': self.people_count,
                'security_armed': self.security_armed,
                'alarm_active': self.alarm_active,
                'alarm_reason': self.alarm_reason,
                'alarm_source': self.alarm_source,
                'door_states': self.door_states.copy(),
                'led_states': self.led_states.copy(),
                'brgb_state': self.brgb_state.copy(),
                'timer': timer_state,
                'timer_seconds': timer_state['seconds'],
                'timer_running': timer_state['running'],
                'timer_expired': timer_state['expired'],
                'timer_blinking': timer_state['blinking'],
                'timer_button_add_seconds': self.timer_button_add_seconds
            }


system_state = SystemState()