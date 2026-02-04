import time
import RPi.GPIO as GPIO
from typing import Callable
import threading


class DS2:
    def __init__(self, pin):
        self.pin = pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        with self.lock:
            return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup(self.pin)


def run_ds2_loop(ds2: DS2, callback: Callable, stop_event, debounce_ms=200):    
    def gpio_callback(channel):
        if stop_event.is_set():
            return

        door_open = ds2.read()
        timestamp = time.time()
        
        try:
            callback(door_open, timestamp)
        except Exception as e:
            print(f"Error in DS2 callback: {e}")

    GPIO.add_event_detect(
        ds2.pin,
        GPIO.BOTH,
        callback=gpio_callback,
        bouncetime=debounce_ms
    )
    
    print(f"DS2 event detection setup on pin {ds2.pin}")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        print("Cleaning up ds2...")
        GPIO.remove_event_detect(ds2.pin)
        ds2.cleanup()
        print("ds2 cleanup complete")