import threading
import time
from typing import Callable, Optional


def dht2_callback(temperature, humidity, timestamp, mqtt_publisher=None, settings=None, lcd_controller=None):
    """
    DHT2 callback for Master Bedroom temperature and humidity sensor.
    """
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"[DHT2 - Master Bedroom]")
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Temperature: {temperature}°C")
    print(f"Humidity: {humidity}%")
    
    # Send temperature to MQTT if publisher is available
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='temperature',
            value=temperature,
            simulated=settings.get('simulated', False)
        )
        
        # Send humidity to MQTT
        mqtt_publisher.add_reading(
            sensor_type='humidity',
            value=humidity,
            simulated=settings.get('simulated', False)
        )
    
    # Update LCD display if available
    if lcd_controller:
        lcd_controller.update_sensor(temperature, humidity)


def run_dht2(settings, threads, stop_event, mqtt_publisher=None, lcd_controller=None):
    """
    Start DHT2 sensor for Master Bedroom.
    Returns the DHT sensor instance.
    """
    dht2_sensor = None
    
    def callback_wrapper(temperature, humidity, timestamp):
        dht2_callback(temperature, humidity, timestamp, mqtt_publisher, settings, lcd_controller)
    
    if settings['simulated']:
        from RPI3.simulators.dht2 import run_dht2_simulator
        print("Starting DHT2 simulator (Master Bedroom)")
        dht2_thread = threading.Thread(
            target=run_dht2_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dht2_thread.start()
        threads.append(dht2_thread)
        print("DHT2 simulator started")
    else:
        from RPI3.sensors.dht2 import run_dht_loop, DHT
        print("Starting DHT2 loop (Master Bedroom)")

        dht2_sensor = DHT(settings['pin'])
        interval = settings.get('read_interval', 2)
        
        dht2_thread = threading.Thread(
            target=run_dht_loop,
            args=(dht2_sensor, interval, callback_wrapper, stop_event),
            daemon=True
        )
        dht2_thread.start()
        threads.append(dht2_thread)
        print("DHT2 loop started")
    
    return dht2_sensor
