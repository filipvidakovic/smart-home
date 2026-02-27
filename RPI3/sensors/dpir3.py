import threading
import time
from typing import Callable


class DPIR3:
    """Digital PIR (Passive Infrared) motion sensor for Bedroom"""
    
    def __init__(self, pin):
        self.pin = pin
        self.motion_detected = False
        print(f"DPIR3 initialized on pin {pin}")
    
    def read(self):
        """Read motion state from GPIO"""
        try:
            import RPi.GPIO as GPIO
            state = GPIO.input(self.pin)
            self.motion_detected = bool(state)
            return self.motion_detected
        except Exception as e:
            print(f"DPIR3 read error: {e}")
            return False


def run_dpir3_loop(dpir3_sensor: DPIR3, callback: Callable, stop_event):
    """
    Main loop for DPIR3 motion sensor.
    Reads sensor state and triggers callback.
    """
    print("DPIR3 Sensor: Loop started")
    
    last_state = False
    debounce_time = 0
    debounce_delay = 0.5  # 500ms debounce
    
    try:
        while not stop_event.is_set():
            current_state = dpir3_sensor.read()
            current_time = time.time()
            
            # Debounce motion detection
            if current_state != last_state:
                if current_time - debounce_time > debounce_delay:
                    last_state = current_state
                    debounce_time = current_time
                    
                    try:
                        callback(current_state, time.time())
                    except Exception as e:
                        print(f"DPIR3 Sensor: Error in callback: {e}")
            
            time.sleep(0.1)  # 100ms polling interval
    
    except Exception as e:
        print(f"DPIR3 Sensor: Fatal error: {e}")
    finally:
        print("DPIR3 Sensor: Loop stopped")
