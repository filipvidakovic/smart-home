import time
import RPi.GPIO as GPIO
from typing import Callable
import threading


class DPIR2:
    
    def __init__(self, pin):
        self.pin = pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        print(f"DPIR2: Initialized on pin {self.pin}")

    def read(self):
        with self.lock:
            return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup(self.pin)


def run_dpir2_loop(dpir2: DPIR2, callback: Callable, stop_event, debounce_ms=500):

    
    def gpio_callback(channel):
        if stop_event.is_set():
            return

        motion_detected = dpir2.read()
        timestamp = time.time()

        if motion_detected:
            try:
                callback(motion_detected, timestamp)
            except Exception as e:
                print(f"DPIR2: Error in callback: {e}")

    GPIO.add_event_detect(
        dpir2.pin,
        GPIO.RISING,
        callback=gpio_callback,
        bouncetime=debounce_ms
    )
    
    print(f"DPIR2: Event detection setup on pin {dpir2.pin}")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        print("DPIR2: Cleaning up...")
        GPIO.remove_event_detect(dpir2.pin)
        dpir2.cleanup()
        print("DPIR2: Cleanup complete")