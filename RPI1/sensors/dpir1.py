import time
import RPi.GPIO as GPIO


class DPIR1:
    def __init__(self, pin):
        self.pin = pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def read(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup(self.pin)


def run_dpir1_loop(dpir1, callback, stop_event, debounce_ms=500):
    """
    PIR motion sensor loop
    """

    def gpio_callback(channel):
        if stop_event.is_set():
            return

        motion_detected = dpir1.read()
        timestamp = time.time()

        if motion_detected:
            callback(motion_detected, timestamp)

    GPIO.add_event_detect(
        dpir1.pin,
        GPIO.RISING,
        callback=gpio_callback,
        bouncetime=debounce_ms
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(dpir1.pin)
        dpir1.cleanup()
