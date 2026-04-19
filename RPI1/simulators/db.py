import threading
import time
import random


def run_db_simulator(callback, stop_event, mqtt_publisher=None):
    """
    Simulate doorbell buzzer activation events.
    Occasionally triggers the buzzer event callback.
    """
    print("DB Buzzer Simulator: Starting doorbell event generation")
    
    try:
        event_counter = 0
        while not stop_event.is_set():
            # Randomly decide if buzzer should activate (low probability)
            if random.random() < 0.05:  # 5% chance every second
                event_counter += 1
                timestamp = time.time()
                
                print(f"🔔 DB Buzzer Simulator: Doorbell activated (Event #{event_counter})")
                
                # Publish buzzer event
                if mqtt_publisher:
                    mqtt_publisher.add_reading(
                        sensor_type='buzzer',
                        value=1,
                        simulated=True
                    )
                
                # Call the callback
                if callback:
                    try:
                        callback(timestamp)
                    except Exception as e:
                        print(f"DB Buzzer Simulator: Error in callback: {e}")
                
                # Sleep after event
                time.sleep(2)
            
            time.sleep(1)
    
    except Exception as e:
        print(f"DB Buzzer Simulator: Error - {e}")
    finally:
        print("DB Buzzer Simulator: Stopped")
