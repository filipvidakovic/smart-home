import threading
import time
from typing import Callable, Optional


def dpir3_callback(motion_detected, timestamp, mqtt_publisher=None, settings=None):
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"[DPIR3 - Bedroom Motion]")
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Motion: {'Detected' if motion_detected else 'Clear'}")
    
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='motion',
            value=1 if motion_detected else 0,
            simulated=settings.get('simulated', False),
            sensor_id='dpir3'
        )


def run_dpir3(settings, threads, stop_event, mqtt_publisher=None):
    """
    Start DPIR3 motion sensor for Bedroom.
    Returns the DPIR sensor instance.
    """
    dpir3_sensor = None
    
    def callback_wrapper(motion_detected, timestamp):
        dpir3_callback(motion_detected, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI3.simulators.dpir3 import run_dpir3_simulator
        print("Starting DPIR3 simulator (Bedroom)")
        dpir3_thread = threading.Thread(
            target=run_dpir3_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        dpir3_thread.start()
        threads.append(dpir3_thread)
        print("DPIR3 simulator started")
    else:
        from RPI3.sensors.dpir3 import run_dpir3_loop, DPIR3
        print("Starting DPIR3 loop (Bedroom)")
        
        dpir3_sensor = DPIR3(settings['pin'])
        dpir3_thread = threading.Thread(
            target=run_dpir3_loop,
            args=(dpir3_sensor, callback_wrapper, stop_event),
            daemon=True
        )
        dpir3_thread.start()
        threads.append(dpir3_thread)
        print("DPIR3 loop started")
    
    return dpir3_sensor
