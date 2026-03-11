import time
import random
from typing import Callable, Generator, Tuple


def generate_dht_events(
    min_interval: float = 2.0,
    max_interval: float = 5.0,
    base_temp: float = 20.0,
    base_humidity: float = 45.0
) -> Generator[Tuple[float, float, float], None, None]:
    """
    Generate DHT1 bedroom temperature and humidity events.
    Bedroom typically cooler at night, moderate humidity.
    """
    current_temp = base_temp
    current_humidity = base_humidity
    
    while True:
        temp_change = random.uniform(-0.5, 0.5)
        humidity_change = random.uniform(-2, 2)
        
        current_temp += temp_change
        current_humidity += humidity_change
        
        # Bedroom temperature range: 18-24°C
        current_temp = max(18.0, min(24.0, current_temp))
        # Bedroom humidity range: 35-55%
        current_humidity = max(35.0, min(55.0, current_humidity))
        
        wait_time = random.uniform(min_interval, max_interval)
        time.sleep(wait_time)
        
        yield round(current_temp, 2), round(current_humidity, 2), time.time()


def run_dht1_simulator(callback: Callable, stop_event):
    """DHT1 Simulator for Bedroom"""
    print("DHT1 Simulator (Bedroom): Starting temperature and humidity generation")
    
    try:
        for temperature, humidity, timestamp in generate_dht_events():
            if stop_event.is_set():
                print("DHT1 Simulator: Stop event detected, shutting down")
                break

            try:
                callback(temperature, humidity, timestamp)
            except Exception as e:
                print(f"DHT1 Simulator: Error in callback: {e}")
                
    except KeyboardInterrupt:
        print("DHT1 Simulator: Interrupted by user")
    finally:
        print("DHT1 Simulator: Stopped")
