import threading
import time
from typing import Callable


def btn_callback(timestamp, mqtt_publisher=None, settings=None, sd4_controller=None):
    """Callback for button press events"""
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("🔘 Kitchen Button Pressed!")
    
    # Notify SD4 controller to send event to server
    if sd4_controller:
        sd4_controller.button_pressed()
    
    # Still publish to MQTT for InfluxDB logging
    if mqtt_publisher and settings:
        mqtt_publisher.add_reading(
            sensor_type='button',
            value=1,
            simulated=settings.get('simulated', False)
        )


def run_btn(settings, threads, stop_event, mqtt_publisher=None, sd4_controller=None):
    """Run BTN button with SD4 controller integration"""
    def callback_wrapper(timestamp):
        btn_callback(timestamp, mqtt_publisher, settings, sd4_controller)
    
    if settings['simulated']:
        from RPI2.simulators.btn import run_btn_simulator
        print("Starting BTN simulator")
        btn_thread = threading.Thread(
            target=run_btn_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        btn_thread.start()
        threads.append(btn_thread)
        print("BTN simulator started")
    else:
        from RPI2.sensors.btn import run_btn_loop, BTN
        print("Starting BTN loop")
        btn = BTN(settings['pin'])
        btn_thread = threading.Thread(
            target=run_btn_loop,
            args=(btn, callback_wrapper, stop_event),
            daemon=True
        )
        btn_thread.start()
        threads.append(btn_thread)
        print("BTN loop started")