import time
import random


def generate_door_state(initial_state=False, change_probability=0.5): # Da se vide promene 0.5

    door_open = initial_state

    while True:
        if random.random() < change_probability:
            door_open = not door_open

        yield door_open


def run_ds1_simulator(delay, callback, stop_event):

    for door_open in generate_door_state():
        time.sleep(delay)

        timestamp = time.time()
        callback(door_open, timestamp)

        if stop_event.is_set():
            break
