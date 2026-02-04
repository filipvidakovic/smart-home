import threading
import time
from typing import Callable, Optional


def dus2_callback(distance, timestamp, mqtt_publisher=None, settings=None):

    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Distance: {distance} cm")
    
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='distance',
            value=distance,
            simulated=settings.get('simulated', False)
        )


def run_dus2(settings, threads, stop_event, mqtt_publisher=None):
    def callback_wrapper(distance, timestamp):
        dus2_callback(distance, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI2.simulators.dus2 import run_dus2_simulator
        print("Starting DUS2 simulator")
        dus2_thread = threading.Thread(
            target=run_dus2_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dus2_thread.start()
        threads.append(dus2_thread)
        print("DUS2 simulator started")
    else:
        from RPI2.sensors.dus2 import run_dus2_loop, DUS2
        print("Starting DUS2 loop")

        dus2 = DUS2(
            settings['trigger_pin'],
            settings['echo_pin']
        )

        interval = settings.get('read_interval', 1)
        
        dus2_thread = threading.Thread(
            target=run_dus2_loop,
            args=(dus2, interval, callback_wrapper, stop_event),
            daemon=True
        )
        dus2_thread.start()
        threads.append(dus2_thread)
        print("DUS2 loop started")