"""
LCD Controller Component
Manages LCD display for any DHT temperature/humidity sensor
"""
import threading
import time
from typing import Optional


class LCDController:
    """
    High-level LCD controller for displaying DHT sensor data.
    Works with any DHT sensor (DHT1, DHT2, etc).
    Displays temperature and humidity readings.
    """
    
    def __init__(self, lcd, dht_sensor, update_interval=3.0):
        """
        Initialize LCD controller.
        
        Args:
            lcd: LCD display instance (real or simulated)
            dht_sensor: DHT sensor instance (DHT1, DHT2, etc)
            update_interval: Seconds between display updates
        """
        self.lcd = lcd
        self.dht_sensor = dht_sensor
        self.update_interval = update_interval
        self.lock = threading.Lock()
        
        # Sensor data storage
        self.sensor_data = {'temperature': None, 'humidity': None, 'timestamp': None}
        
        # Control flags
        self.running = False
        self.update_thread = None
        
        # Initialize display
        self.lcd.backlight_on()
        self.lcd.clear()
        self.show_welcome()
    
    def show_welcome(self):
        """Display welcome message."""
        self.lcd.clear()
        self.lcd.write_string("Smart Home LCD", row=0, col=1)
        self.lcd.write_string("DHT Sensor", row=1, col=3)
        time.sleep(2)
    
    def update_sensor(self, temperature: float, humidity: float):
        """
        Update DHT sensor data.
        
        Args:
            temperature: Temperature in Celsius
            humidity: Relative humidity in percent
        """
        with self.lock:
            self.sensor_data = {
                'temperature': temperature,
                'humidity': humidity,
                'timestamp': time.time()
            }
    
    def display_sensor(self):
        """Display DHT sensor data."""
        with self.lock:
            data = self.sensor_data
            if data['temperature'] is not None:
                line1 = f"Temp {data['temperature']:5.1f}C"
                line2 = f"Hum  {data['humidity']:5.1f}%"
            else:
                line1 = "DHT Sensor"
                line2 = "No data yet"
        
        self.lcd.clear()
        self.lcd.write_string(line1, row=0, col=0)
        self.lcd.write_string(line2, row=1, col=0)
    
    def display_custom(self, line1: str, line2: str = ""):
        """
        Display custom text.
        
        Args:
            line1: Text for first line (max 16 chars)
            line2: Text for second line (max 16 chars)
        """
        self.lcd.clear()
        self.lcd.write_string(line1[:16], row=0, col=0)
        if line2:
            self.lcd.write_string(line2[:16], row=1, col=0)
    
    def _auto_update_loop(self, stop_event):
        """
        Background thread for auto-updating display.
        Continuously displays DHT sensor data.
        """
        print("LCD Controller: Auto-update loop started (DHT sensor mode)")
        
        while not stop_event.is_set():
            try:
                self.display_sensor()
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"LCD Controller: Error in auto-update loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start auto-update thread."""
        if not self.running:
            self.running = True
            self.stop_event = threading.Event()
            self.update_thread = threading.Thread(
                target=self._auto_update_loop,
                args=(self.stop_event,),
                daemon=True
            )
            self.update_thread.start()
            print("LCD Controller: Started")
    
    def stop(self):
        """Stop auto-update thread."""
        if self.running:
            self.running = False
            if hasattr(self, 'stop_event'):
                self.stop_event.set()
            if self.update_thread:
                self.update_thread.join(timeout=2)
            print("LCD Controller: Stopped")
    
    def show_goodbye(self):
        """Display goodbye message."""
        self.lcd.clear()
        self.lcd.write_string("Goodbye!", row=0, col=5)
        self.lcd.write_string("Powering down", row=1, col=1)
        time.sleep(2)
        self.lcd.clear()
        self.lcd.backlight_off()
    
    def cleanup(self):
        """Clean up LCD resources."""
        self.stop()
        self.show_goodbye()
        print("LCD Controller: Cleaned up")


def run_lcd(settings, stop_event, dht_sensor=None, mqtt_publisher=None):
    """
    Initialize and start LCD controller.
    
    Args:
        settings: LCD configuration settings
        stop_event: Threading event for shutdown
        dht_sensor: DHT sensor instance (DHT1, DHT2, etc) required for display
        mqtt_publisher: Optional MQTT publisher (for future expansion)
    
    Returns:
        LCDController instance or None if dht_sensor not provided
    """
    if dht_sensor is None:
        print("LCD: DHT sensor not available, skipping LCD initialization")
        return None
    
    if settings.get('simulated', False):
        from RPI3.simulators.lcd import LCD1602Simulator
        print("Starting LCD simulator")
        lcd = LCD1602Simulator(
            i2c_address=settings.get('i2c_address', 0x27),
            i2c_bus=settings.get('i2c_bus', 1)
        )
    else:
        from RPI3.sensors.lcd import LCD1602
        print("Starting LCD hardware")
        lcd = LCD1602(
            i2c_address=settings.get('i2c_address', 0x27),
            i2c_bus=settings.get('i2c_bus', 1)
        )
    
    # Create controller with DHT sensor
    controller = LCDController(
        lcd=lcd,
        dht_sensor=dht_sensor,
        update_interval=settings.get('update_interval', 3.0)
    )
    
    # Start auto-update
    controller.start()
    
    print("LCD Controller ready")
    return controller
