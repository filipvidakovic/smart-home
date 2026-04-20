import threading
import time


def db_callback(timestamp, mqtt_publisher=None):
    """Callback for buzzer activation events"""
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("🔔 Doorbell Buzzer Activated")


def run_db(settings, threads, stop_event, mqtt_publisher=None):
    """Run doorbell buzzer component"""
    
    def callback_wrapper(timestamp):
        db_callback(timestamp, mqtt_publisher)
    
    if settings.get('simulated', True):
        from RPI1.simulators.db import run_db_simulator
        print("Starting DB buzzer simulator")
        db_thread = threading.Thread(
            target=run_db_simulator,
            args=(callback_wrapper, stop_event, mqtt_publisher),
            daemon=True
        )
        db_thread.start()
        threads.append(db_thread)
        print("DB buzzer simulator started")
    else:
        # Real buzzer - no separate thread needed, it's event-driven
        print("DB buzzer initialized (real GPIO)")
