import time
import random


def generate_motion_events(min_interval=1, max_interval=10):
    while True:
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)

        yield True, time.time()


def run_dpir1_simulator(callback, stop_event):
    for motion_detected, timestamp in generate_motion_events():
        if stop_event.is_set():
            break

        callback(motion_detected, timestamp)
