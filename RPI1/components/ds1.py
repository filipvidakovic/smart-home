from simulators.ds1 import run_ds1_simulator
import threading
import time

door_led = None

def ds1_callback(door_open, timestamp):
    global door_led
    t = time.localtime(timestamp)
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Door Open: {'Yes' if door_open else 'No'}")
    print(f"LED bulb: {'On' if door_open else 'Off'}")
    if door_led:
        door_led.set_state(door_open)


def run_ds1(settings, threads, stop_event):
    if settings['simulated']:
        print("Starting ds1 simulator")
        ds1_thread = threading.Thread(
            target=run_ds1_simulator,
            args=(ds1_callback, stop_event),
            daemon=True
        )
        ds1_thread.start()
        threads.append(ds1_thread)
        print("Ds1 simulator started")
    else:
        from sensors.ds1 import run_ds1_loop, DS1
        from sensors.dl import DoorLED
        global door_led
        door_led = DoorLED(settings['led_pin'])
        print("Starting ds1 loop")
        ds1 = DS1(settings['pin'])
        ds1_thread = threading.Thread(
            target=run_ds1_loop,
            args=(ds1, 2, ds1_callback, stop_event),
            daemon=True
        )
        ds1_thread.start()
        threads.append(ds1_thread)
        print("Ds1 loop started")
