import threading
import time
from typing import Callable, Optional

door_led = None

def ds2_callback(door_open, timestamp, mqtt_publisher=None, settings=None):
    global door_led
    t = time.localtime(timestamp)
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Door Open: {'Yes' if door_open else 'No'}")
    print(f"LED bulb: {'On' if door_open else 'Off'}")
    
    if door_led:
        door_led.set_state(door_open)
    
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
        print("Starting ds2 simulator")
        ds2_thread = threading.Thread(
            target=run_ds2_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        ds2_thread.start()
        threads.append(ds2_thread)
        print("ds2 simulator started")
    else:
        from RPI2.sensors.ds2 import run_ds2_loop, ds2
        from RPI2.sensors.dl import DoorLED
        global door_led
        door_led = DoorLED(settings['led_pin'])
        print("Starting ds2 loop")
        ds2 = ds2(settings['pin'])
        ds2_thread = threading.Thread(
            target=run_ds2_loop,
            args=(ds2, callback_wrapper, stop_event),
            daemon=True
        )
        ds2_thread.start()
        threads.append(ds2_thread)
        print("ds2 loop started")