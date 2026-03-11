import time
import random
from typing import Callable, Generator, Tuple


def generate_motion_events(
    min_interval: float = 2.0,
    max_interval: float = 8.0
) -> Generator[Tuple[bool, float], None, None]:

    while True:
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)

        yield True, time.time()


def run_dpir3_simulator(callback: Callable, stop_event):
    print("DPIR3 Simulator: Starting motion event generation")
    
    try:
        for motion_detected, timestamp in generate_motion_events():
            if stop_event.is_set():
                print("DPIR3 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(motion_detected, timestamp)
            except Exception as e:
                print(f"DPIR3 Simulator: Error in callback: {e}")
    except Exception as e:
        print(f"DPIR3 Simulator: Fatal error: {e}")
    finally:
        print("DPIR3 Simulator: Stopped")
