import time
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    GPIO = None

class Buzzer:
    def __init__(self, pin):
        self.pin = pin
        if GPIO:
            GPIO.setup(self.pin, GPIO.OUT)

    def ring(self, times=3):
        print("[ACTUATOR] Buzzer: RINGING (Doorbell)")
        for _ in range(times):
            if GPIO: GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.2)  # Zvuk traje 0.2s
            if GPIO: GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.1)  # Pauza 0.1s
    def cleanup(self):
        if GPIO:
            GPIO.cleanup(self.pin)