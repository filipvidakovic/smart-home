import time
import random


def generate_distance_events(min_interval=1, max_interval=10, min_dist=10, max_dist=200):
    while True:
        time.sleep(random.uniform(min_interval, max_interval))
        yield round(random.uniform(min_dist, max_dist), 2), time.time()


def run_dus1_simulator(callback, stop_event):
    for distance, timestamp in generate_distance_events():
        if stop_event.is_set():
            break

        callback(distance, timestamp)
