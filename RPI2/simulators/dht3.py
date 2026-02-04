import time
import random
from typing import Callable, Generator, Tuple


def generate_dht_events(
    min_interval: float = 2.0,
    max_interval: float = 5.0,
    base_temp: float = 22.0,
    base_humidity: float = 50.0
) -> Generator[Tuple[float, float, float], None, None]:

    current_temp = base_temp
    current_humidity = base_humidity
    
    while True:
        temp_change = random.uniform(-0.5, 0.5)
        humidity_change = random.uniform(-2, 2)
        
        current_temp += temp_change
        current_humidity += humidity_change
        
        current_temp = max(15.0, min(30.0, current_temp))

        current_humidity = max(30.0, min(70.0, current_humidity))
        
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)
        
        yield round(current_temp, 2), round(current_humidity, 2), time.time()


def run_dht3_simulator(callback: Callable, stop_event):
    print("DHT3 Simulator: Starting temperature and humidity generation")
    
    try:
        for temperature, humidity, timestamp in generate_dht_events():
            if stop_event.is_set():
                print("DHT3 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(temperature, humidity, timestamp)
            except Exception as e:
                print(f"DHT3 Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("DHT3 Simulator: Interrupted by user")
    finally:
        print("DHT3 Simulator: Stopped")