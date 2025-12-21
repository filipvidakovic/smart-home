import threading
from simulators.dus1 import run_dus1_simulator

import time

def dus1_callback(distance, timestamp):
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Distance: {distance} cm")


def run_dus1(settings, threads, stop_event):
    if settings['simulated']:
        print("Starting dus1 simulator")
        dus1_thread = threading.Thread(
            target=run_dus1_simulator,
            args=(dus1_callback, stop_event),
            daemon=True
        )
        dus1_thread.start()
        threads.append(dus1_thread)
        print("dus1 simulator started")
    else:
        from sensors.dus1 import run_dus1_loop, DUS1
        print("Starting dus1 loop")

        dus1 = DUS1(
            settings['trig_pin'],
            settings['echo_pin']
        )

        dus1_thread = threading.Thread(
            target=run_dus1_loop,
            args=(dus1, settings.get('interval', 1), dus1_callback, stop_event),
            daemon=True
        )
        dus1_thread.start()
        threads.append(dus1_thread)
        print("DUS1 loop started")
