import threading
import time
from typing import Callable, Optional


def dus1_callback(distance, timestamp, mqtt_publisher=None, settings=None):

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


def run_dus1(settings, threads, stop_event, mqtt_publisher=None):
    def callback_wrapper(distance, timestamp):
        dus1_callback(distance, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from simulators.dus1 import run_dus1_simulator
        print("Starting DUS1 simulator")
        dus1_thread = threading.Thread(
            target=run_dus1_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 simulator started")
    else:
        from sensors.dus1 import run_dus1_loop, DUS1
        print("Starting DUS1 loop")

        dus1 = DUS1(
            settings['trigger_pin'],
            settings['echo_pin']
        )

        interval = settings.get('read_interval', 1)
        
        dus1_thread = threading.Thread(
            target=run_dus1_loop,
            args=(dus1, interval, callback_wrapper, stop_event),
            daemon=True
        )
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 loop started")