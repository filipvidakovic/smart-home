import time
import random


def generate_door_events(
    initial_state=False,
    min_interval=1,
    max_interval=10
):
    door_open = initial_state

    while True:
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)

        door_open = not door_open

        yield door_open, time.time()


def run_ds1_simulator(callback, stop_event):
    for door_open, timestamp in generate_door_events():
        if stop_event.is_set():
            break

        callback(door_open, timestamp)
