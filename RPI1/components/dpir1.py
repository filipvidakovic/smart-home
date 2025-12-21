import threading
from simulators.dpir1 import run_dpir1_simulator

import time

def dpir1_callback(motion_detected, timestamp):
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("Motion detected near the door")



def run_dpir1(settings, threads, stop_event):
    if settings['simulated']:
        print("Starting dpir1 simulator")
        dpir1_thread = threading.Thread(
            target=run_dpir1_simulator,
            args=(dpir1_callback, stop_event),
            daemon=True
        )
        dpir1_thread.start()
        threads.append(dpir1_thread)
        print("dpir1 simulator started")
    else:
        from sensors.dpir1 import run_dpir1_loop, DPIR1
        print("Starting dpir1 loop")
        dpir1 = DPIR1(settings['pin'])
        dpir1_thread = threading.Thread(
            target=run_dpir1_loop,
            args=(dpir1, dpir1_callback, stop_event),
            daemon=True
        )
        dpir1_thread.start()
        threads.append(dpir1_thread)
        print("DPIR1 loop started")
