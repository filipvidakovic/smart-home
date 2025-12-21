import time
import RPi.GPIO as GPIO


class DUS1:
    def __init__(self, trig_pin, echo_pin):
        self.trig = trig_pin
        self.echo = echo_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

        GPIO.output(self.trig, GPIO.LOW)
        time.sleep(0.1)

    def measure_distance(self, timeout=0.02):
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trig, GPIO.LOW)

        start_time = time.time()

        while GPIO.input(self.echo) == GPIO.LOW:
            if time.time() - start_time > timeout:
                return None

        pulse_start = time.time()

        while GPIO.input(self.echo) == GPIO.HIGH:
            if time.time() - pulse_start > timeout:
                return None

        pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        distance = (pulse_duration * 34300) / 2
        return round(distance, 2)

    def cleanup(self):
        GPIO.cleanup([self.trig, self.echo])

def run_ds3_loop(ds3, interval, callback, stop_event):
    try:
        while not stop_event.is_set():
            distance = ds3.measure_distance()
            timestamp = time.time()

            if distance is not None:
                callback(distance, timestamp)

            time.sleep(interval)
    finally:
        ds3.cleanup()
