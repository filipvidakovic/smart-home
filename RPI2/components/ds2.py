import threading
import time
from typing import Callable, Optional


def ds2_callback(door_open, timestamp, mqtt_publisher=None, settings=None):

    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Kitchen Door: {'Open' if door_open else 'Closed'}")
    
    #TODO Update system state
    
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='door',
            value=1 if door_open else 0,
            simulated=settings.get('simulated', False)
        )

def run_ds2(settings, threads, stop_event, mqtt_publisher=None):

    def callback_wrapper(door_open, timestamp):
        ds2_callback(door_open, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI2.simulators.ds2 import run_ds2_simulator
        print("Starting DS2 simulator")
        ds2_thread = threading.Thread(
            target=run_ds2_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        ds2_thread.start()
        threads.append(ds2_thread)
        print("DS2 simulator started")
    else:
        from RPI2.sensors.ds2 import run_ds2_loop, DS2
        print("Starting DS2 loop")
        ds2 = DS2(settings['pin'])
        ds2_thread = threading.Thread(
            target=run_ds2_loop,
            args=(ds2, callback_wrapper, stop_event),
            daemon=True
        )
        ds2_thread.start()
        threads.append(ds2_thread)
        print("DS2 loop started")