import time
import random
from typing import Callable


def run_btn_simulator(callback: Callable, stop_event):
    print("BTN Simulator: Starting button press generation")
    
    try:
        while not stop_event.is_set():
            wait_time = random.uniform(5.0, 15.0)
            time.sleep(wait_time)
            
            if stop_event.is_set():
                break
            
            timestamp = time.time()
            try:
                callback(timestamp)
            except Exception as e:
                print(f"BTN Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("BTN Simulator: Interrupted by user")
    finally:
        print("BTN Simulator: Stopped")