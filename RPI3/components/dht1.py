import threading
import time
from typing import Callable, Optional


def dht1_callback(temperature, humidity, timestamp, mqtt_publisher=None, settings=None, lcd_controller=None):
    """
    DHT1 callback for Bedroom temperature and humidity sensor.
    """
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"[DHT1 - Bedroom]")
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
    
    # TODO: Update LCD display when LCD controller is implemented
    # if lcd_controller:
    #     lcd_controller.update_dht1(temperature, humidity)


def run_dht1(settings, threads, stop_event, mqtt_publisher=None, lcd_controller=None):
    """
    Start DHT1 sensor for Bedroom.
    """
    def callback_wrapper(temperature, humidity, timestamp):
        dht1_callback(temperature, humidity, timestamp, mqtt_publisher, settings, lcd_controller)
    
    if settings['simulated']:
        from RPI3.simulators.dht1 import run_dht1_simulator
        print("Starting DHT1 simulator (Bedroom)")
        dht1_thread = threading.Thread(
            target=run_dht1_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dht1_thread.start()
        threads.append(dht1_thread)
        print("DHT1 simulator started")
    else:
        from RPI3.sensors.dht1 import run_dht_loop, DHT
        print("Starting DHT1 loop (Bedroom)")

        dht1 = DHT(settings['pin'])
        interval = settings.get('read_interval', 2)
        
        dht1_thread = threading.Thread(
            target=run_dht_loop,
            args=(dht1, interval, callback_wrapper, stop_event),
            daemon=True
        )
        dht1_thread.start()
        threads.append(dht1_thread)
        print("DHT1 loop started")
