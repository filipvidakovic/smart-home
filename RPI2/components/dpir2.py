import threading
import time
from typing import Callable, Optional

def dpir2_callback(motion_detected, timestamp, mqtt_publisher=None, settings=None):

    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("Motion detected near the door")
    
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='motion',
            value=2 if motion_detected else 0,
            simulated=settings.get('simulated', False)
        )


def run_dpir2(settings, threads, stop_event, mqtt_publisher=None):
    def callback_wrapper(motion_detected, timestamp):
        dpir2_callback(motion_detected, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI2.simulators.dpir2 import run_dpir2_simulator
        print("Starting DPIR2 simulator")
        dpir2_thread = threading.Thread(
            target=run_dpir2_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dpir2_thread.start()
        threads.append(dpir2_thread)
        print("DPIR2 simulator started")
    else:
        from RPI2.sensors.dpir2 import run_dpir2_loop, DPIR2
        print("Starting DPIR2 loop")
        dpir2 = DPIR2(settings['pin'])
        dpir2_thread = threading.Thread(
            target=run_dpir2_loop,
            args=(dpir2, callback_wrapper, stop_event),
            daemon=True
        )
        dpir2_thread.start()
        threads.append(dpir2_thread)
        print("DPIR2 loop started")