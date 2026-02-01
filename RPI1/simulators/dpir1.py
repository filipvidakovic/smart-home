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


def run_dpir1_simulator(callback: Callable, stop_event):
    print("DPIR1 Simulator: Starting motion event generation")
    
    try:
        for motion_detected, timestamp in generate_motion_events():
            if stop_event.is_set():
                print("DPIR1 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(motion_detected, timestamp)
            except Exception as e:
                print(f"DPIR1 Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("DPIR1 Simulator: Interrupted by user")
    finally:
        print("DPIR1 Simulator: Stopped")