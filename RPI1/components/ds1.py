from simulators.ds1 import run_ds1_simulator
import threading
import time

def ds1_callback(door_open, timestamp):
    t = time.localtime(timestamp)
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Door Open: {'Yes' if door_open else 'No'}")


def run_ds1(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting ds1 simulator")
            ds1_thread = threading.Thread(target = run_ds1_simulator, args=(2, ds1_callback, stop_event))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("Ds1 simulator started")
        else:
            from sensors.ds1 import run_ds1_loop, DS1
            print("Starting ds1 loop")
            ds1 = DS1(settings['pin'])
            ds1_thread = threading.Thread(target=run_ds1_loop, args=(ds1, 2, ds1_callback, stop_event))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("Ds1 loop started")
