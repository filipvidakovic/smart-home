import time
import random
from typing import Callable, Generator, Tuple


def generate_distance_events(
    min_interval: float = 1.0,
    max_interval: float = 3.0,
    min_dist: float = 10.0,
    max_dist: float = 200.0
) -> Generator[Tuple[float, float], None, None]:
    current_distance = random.uniform(min_dist, max_dist)
    
    while True:
        change = random.uniform(-20, 20)
        current_distance += change
        
        current_distance = max(min_dist, min(max_dist, current_distance))
        
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)
        
        yield round(current_distance, 2), time.time()


def run_dus2_simulator(callback: Callable, stop_event):
    print("DUS2 Simulator: Starting distance measurement generation")

    try:
        for distance, timestamp in generate_distance_events():
            if stop_event.is_set():
                print("DUS2 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(distance, timestamp)
            except Exception as e:
                print(f"DUS2 Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("DUS2 Simulator: Interrupted by user")
    finally:
        print("DUS2 Simulator: Stopped")