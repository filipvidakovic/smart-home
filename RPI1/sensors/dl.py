import RPi.GPIO as GPIO

class DoorLED:
    def __init__(self, pin):
        self.pin = pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

    def set_state(self, door_open: bool):
        if door_open:
            self.on()
        else:
            self.off()

    def cleanup(self):
        GPIO.output(self.pin, GPIO.LOW)
        GPIO.cleanup(self.pin)
