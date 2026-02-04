import time
from typing import Callable


def run_sd4_simulator(stop_event):
    print("SD4 Simulator: Starting timer display simulation")
    
    try:
        seconds = 0
        while not stop_event.is_set():
            minutes = seconds // 60
            secs = seconds % 60
            
            print(f"SD4 Display: {minutes:02d}:{secs:02d}")
            
            time.sleep(1)
            seconds += 1
            
            if seconds >= 6000:
                seconds = 0
                
    except KeyboardInterrupt:
        print("SD4 Simulator: Interrupted by user")
    finally:
        print("SD4 Simulator: Stopped")