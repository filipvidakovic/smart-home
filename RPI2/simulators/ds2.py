import time
import random
from typing import Callable, Generator, Tuple


def generate_door_events(
    initial_state: bool = False,
    min_interval: float = 2.0,
    max_interval: float = 8.0
) -> Generator[Tuple[bool, float], None, None]:
    door_open = initial_state

    while True:
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)

        door_open = not door_open

        yield door_open, time.time()


def run_ds2_simulator(callback: Callable, stop_event):
    print("DS2 Simulator: Starting door event generation")
    
    try:
        for door_open, timestamp in generate_door_events():
            if stop_event.is_set():
                print("DS2 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(door_open, timestamp)
            except Exception as e:
                print(f"DS2 Simulator: Error in callback: {e}")

    except KeyboardInterrupt:
        print("DS2 Simulator: Interrupted by user")
    finally:
        print("DS2 Simulator: Stopped")