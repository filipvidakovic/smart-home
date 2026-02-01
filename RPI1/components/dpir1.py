import threading
import time
from typing import Callable, Optional

def dpir1_callback(motion_detected, timestamp, mqtt_publisher=None, settings=None):

    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("Motion detected near the door")
    
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='motion',
            value=1 if motion_detected else 0,
            simulated=settings.get('simulated', False)
        )


def run_dpir1(settings, threads, stop_event, mqtt_publisher=None):
    def callback_wrapper(motion_detected, timestamp):
        dpir1_callback(motion_detected, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from simulators.dpir1 import run_dpir1_simulator
        print("Starting DPIR1 simulator")
        dpir1_thread = threading.Thread(
            target=run_dpir1_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dpir1_thread.start()
        threads.append(dpir1_thread)
        print("DPIR1 simulator started")
    else:
        from sensors.dpir1 import run_dpir1_loop, DPIR1
        print("Starting DPIR1 loop")
        dpir1 = DPIR1(settings['pin'])
        dpir1_thread = threading.Thread(
            target=run_dpir1_loop,
            args=(dpir1, callback_wrapper, stop_event),
            daemon=True
        )
        dpir1_thread.start()
        threads.append(dpir1_thread)
        print("DPIR1 loop started")