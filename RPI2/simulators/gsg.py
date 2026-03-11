import time
import random
import math
from typing import Callable, Generator, Tuple


def generate_gyro_events(
    min_interval: float = 0.5,
    max_interval: float = 2.0
) -> Generator[Tuple[float, float, float, float, float, float, float], None, None]:

    angle = 0
    shake_counter = 0
    
    while True:
        shake_counter += 1
        
        # Every 10-15 readings, simulate a dangerous shake
        if shake_counter % random.randint(10, 15) == 0:
            # Greater movement - dangerous shake (> 1.5g)
            accel_x = random.uniform(-2.5, 2.5)
            accel_y = random.uniform(-2.5, 2.5)
            accel_z = 1.0 + random.uniform(-2.0, 2.0)
            print(f"⚠️  GSG SIMULATOR: Generating dangerous shake! accel_x={accel_x:.2f}g, accel_y={accel_y:.2f}g")
        else:
            # Normal slight movement/vibration
            accel_x = random.uniform(-0.1, 0.1)
            accel_y = random.uniform(-0.1, 0.1)
            accel_z = 1.0 + random.uniform(-0.05, 0.05)  # ~1g when stationary
        
        # Simulate rotation
        gyro_x = math.sin(angle) * 5 + random.uniform(-1, 1)
        gyro_y = math.cos(angle) * 5 + random.uniform(-1, 1)
        gyro_z = random.uniform(-2, 2)
        
        angle += 0.1
        if angle > 2 * math.pi:
            angle = 0
        
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)
        
        yield (
            round(accel_x, 3),
            round(accel_y, 3),
            round(accel_z, 3),
            round(gyro_x, 3),
            round(gyro_y, 3),
            round(gyro_z, 3),
            time.time()
        )


def run_gsg_simulator(callback: Callable, stop_event):
    print("GSG Simulator: Starting gyroscope data generation")
    
    try:
        for acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, timestamp in generate_gyro_events():
            if stop_event.is_set():
                print("GSG Simulator: Stop event detected, shutting down")
                break

            try:
                callback(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, timestamp)
            except Exception as e:
                print(f"GSG Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("GSG Simulator: Interrupted by user")
    finally:
        print("GSG Simulator: Stopped")