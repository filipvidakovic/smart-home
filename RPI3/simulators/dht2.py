import time
import random
from typing import Callable, Generator, Tuple


def generate_dht_events(
    min_interval: float = 2.0,
    max_interval: float = 5.0,
    base_temp: float = 21.0,
    base_humidity: float = 48.0
) -> Generator[Tuple[float, float, float], None, None]:
    """
    Generate DHT2 master bedroom temperature and humidity events.
    Master bedroom typically slightly warmer, similar humidity to regular bedroom.
    """
    current_temp = base_temp
    current_humidity = base_humidity
    
    while True:
        temp_change = random.uniform(-0.5, 0.5)
        humidity_change = random.uniform(-2, 2)
        
        current_temp += temp_change
        current_humidity += humidity_change
        
        # Master bedroom temperature range: 19-25°C
        current_temp = max(19.0, min(25.0, current_temp))
        # Master bedroom humidity range: 38-58%
        current_humidity = max(38.0, min(58.0, current_humidity))
        
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)
        
        yield round(current_temp, 2), round(current_humidity, 2), time.time()


def run_dht2_simulator(callback: Callable, stop_event):
    """DHT2 Simulator for Master Bedroom"""
    print("DHT2 Simulator (Master Bedroom): Starting temperature and humidity generation")
    
    try:
        for temperature, humidity, timestamp in generate_dht_events():
            if stop_event.is_set():
                print("DHT2 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(temperature, humidity, timestamp)
            except Exception as e:
                print(f"DHT2 Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("DHT2 Simulator: Interrupted by user")
    finally:
        print("DHT2 Simulator: Stopped")
