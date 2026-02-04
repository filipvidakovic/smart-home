import time
import RPi.GPIO as GPIO
from typing import Callable
import threading


class BTN:
    
    def __init__(self, pin):
        self.pin = pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print(f"BTN: Initialized on pin {self.pin}")

    def is_pressed(self):
        with self.lock:
            return GPIO.input(self.pin) == GPIO.LOW 

    def cleanup(self):
        GPIO.cleanup(self.pin)


def run_btn_loop(btn: BTN, callback: Callable, stop_event, debounce_ms=300):
    
    def gpio_callback(channel):
        if stop_event.is_set():
            return

        if btn.is_pressed():
            timestamp = time.time()
            try:
                callback(timestamp)
            except Exception as e:
                print(f"BTN: Error in callback: {e}")

    GPIO.add_event_detect(
        btn.pin,
        GPIO.FALLING, 
        callback=gpio_callback,
        bouncetime=debounce_ms
    )
    
    print(f"BTN: Event detection setup on pin {btn.pin}")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        print("BTN: Cleaning up...")
        GPIO.remove_event_detect(btn.pin)
        btn.cleanup()
        print("BTN: Cleanup complete")