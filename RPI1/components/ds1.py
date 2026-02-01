import threading
import time
from typing import Callable, Optional

door_led = None

def ds1_callback(door_open, timestamp, mqtt_publisher=None, settings=None):
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

def run_ds1(settings, threads, stop_event, mqtt_publisher=None):

    def callback_wrapper(door_open, timestamp):
        ds1_callback(door_open, timestamp, mqtt_publisher, settings)
    
    if settings['simulated']:
        from simulators.ds1 import run_ds1_simulator
        print("Starting DS1 simulator")
        ds1_thread = threading.Thread(
            target=run_ds1_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 simulator started")
    else:
        from sensors.ds1 import run_ds1_loop, DS1
        from sensors.dl import DoorLED
        global door_led
        door_led = DoorLED(settings['led_pin'])
        print("Starting DS1 loop")
        ds1 = DS1(settings['pin'])
        ds1_thread = threading.Thread(
            target=run_ds1_loop,
            args=(ds1, callback_wrapper, stop_event),
            daemon=True
        )
        ds1_thread.start()
        threads.append(ds1_thread)
        print("DS1 loop started")