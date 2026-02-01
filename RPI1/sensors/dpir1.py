import time
import RPi.GPIO as GPIO
from typing import Callable
import threading


class DPIR1:
    
    def __init__(self, pin):
        self.pin = pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        print(f"DPIR1: Initialized on pin {self.pin}")

    def read(self):
        with self.lock:
            return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup(self.pin)


def run_dpir1_loop(dpir1: DPIR1, callback: Callable, stop_event, debounce_ms=500):

    
    def gpio_callback(channel):
        if stop_event.is_set():
            return

        motion_detected = dpir1.read()
        timestamp = time.time()

        if motion_detected:
            try:
                callback(motion_detected, timestamp)
            except Exception as e:
                print(f"DPIR1: Error in callback: {e}")

    GPIO.add_event_detect(
        dpir1.pin,
        GPIO.RISING,
        callback=gpio_callback,
        bouncetime=debounce_ms
    )
    
    print(f"DPIR1: Event detection setup on pin {dpir1.pin}")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        print("DPIR1: Cleaning up...")
        GPIO.remove_event_detect(dpir1.pin)
        dpir1.cleanup()
        print("DPIR1: Cleanup complete")