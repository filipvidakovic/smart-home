import time
import RPi.GPIO as GPIO


class DS1:
    def __init__(self, pin):
        self.pin = pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup(self.pin)

def run_ds1_loop(ds1, callback, stop_event, debounce_ms=200):

    def gpio_callback(channel):
        if stop_event.is_set():
            return

        door_open = ds1.read()
        timestamp = time.time()
        callback(door_open, timestamp)

    GPIO.add_event_detect(
        ds1.pin,
        GPIO.BOTH,
        callback=gpio_callback,
        bouncetime=debounce_ms
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(ds1.pin)
        ds1.cleanup()
