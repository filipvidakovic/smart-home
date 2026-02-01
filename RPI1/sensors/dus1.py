import time
import RPi.GPIO as GPIO
from typing import Callable, Optional
import threading


class DUS1:
    
    def __init__(self, trig_pin, echo_pin):
        self.trig = trig_pin
        self.echo = echo_pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

        GPIO.output(self.trig, GPIO.LOW)
        time.sleep(0.1)
        
        print(f"DUS1: Initialized (TRIG={self.trig}, ECHO={self.echo})")

    def measure_distance(self, timeout=0.02) -> Optional[float]:
        with self.lock:
            # Send 10us pulse to trigger
            GPIO.output(self.trig, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.trig, GPIO.LOW)

            start_time = time.time()

            # Wait for echo to go HIGH
            while GPIO.input(self.echo) == GPIO.LOW:
                if time.time() - start_time > timeout:
                    return None

            pulse_start = time.time()

            # Wait for echo to go LOW
            while GPIO.input(self.echo) == GPIO.HIGH:
                if time.time() - pulse_start > timeout:
                    return None

            pulse_end = time.time()

            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            # Speed of sound = 343 m/s = 34300 cm/s
            # Distance = (Time × Speed) / 2 (round trip)
            distance = (pulse_duration * 34300) / 2
            
            return round(distance, 2)

    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup([self.trig, self.echo])


def run_dus1_loop(dus1: DUS1, interval: float, callback: Callable, stop_event):
    print(f"DUS1: Starting measurement loop (interval={interval}s)")
    
    try:
        while not stop_event.is_set():
            distance = dus1.measure_distance()
            timestamp = time.time()

            if distance is not None:
                try:
                    callback(distance, timestamp)
                except Exception as e:
                    print(f"DUS1: Error in callback: {e}")
            else:
                print("DUS1: Measurement timeout (no obstacle detected)")

            time.sleep(interval)
    except Exception as e:
        print(f"DUS1: Error in measurement loop: {e}")
    finally:
        print("DUS1: Cleaning up...")
        dus1.cleanup()
        print("DUS1: Cleanup complete")