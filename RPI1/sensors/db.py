import time
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    GPIO = None

class Buzzer:
    def __init__(self, pin, mqtt_publisher=None):
        self.pin = pin
        self.mqtt_publisher = mqtt_publisher
        if GPIO:
            GPIO.setup(self.pin, GPIO.OUT)

    def ring(self, times=3):
        print("[ACTUATOR] Buzzer: RINGING (Doorbell)")
        
        # Publish buzzer activation event to MQTT
        if self.mqtt_publisher:
            self.mqtt_publisher.add_reading(
                sensor_type='buzzer',
                value=1,
                simulated=False
            )
        
        for _ in range(times):
            if GPIO: GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.2)  # Zvuk traje 0.2s
            if GPIO: GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.1)  # Pauza 0.1s
    
    def cleanup(self):
        if GPIO:
            GPIO.cleanup(self.pin)