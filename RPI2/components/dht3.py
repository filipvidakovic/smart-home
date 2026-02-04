import threading
import time
from typing import Callable, Optional


def dht3_callback(temperature, humidity, timestamp, mqtt_publisher=None, settings=None):

    t = time.localtime(timestamp)
    print("=" * 20)
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


def run_dht3(settings, threads, stop_event, mqtt_publisher=None):

    def callback_wrapper(temperature, humidity, timestamp):
        dht3_callback(temperature, humidity, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI2.simulators.dht3 import run_dht3_simulator
        print("Starting DHT3 simulator")
        dht3_thread = threading.Thread(
            target=run_dht3_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dht3_thread.start()
        threads.append(dht3_thread)
        print("DHT3 simulator started")
    else:
        from RPI2.sensors.dht3 import run_dht3_loop, DHT3
        print("Starting DHT3 loop")

        dht3 = DHT3(settings['pin'])
        interval = settings.get('read_interval', 2)
        
        dht3_thread = threading.Thread(
            target=run_dht3_loop,
            args=(dht3, interval, callback_wrapper, stop_event),
            daemon=True
        )
        dht3_thread.start()
        threads.append(dht3_thread)
        print("DHT3 loop started")