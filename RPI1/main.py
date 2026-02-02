import threading
import time
import sys

from components.dms import run_dms
from sensors.db import Buzzer
from settings.settings import load_settings
from components.ds1 import run_ds1
from components.dpir1 import run_dpir1
from components.dus1 import run_dus1
from components.dl import create_led_bulb
from mqtt.publisher import MQTTPublisher

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")
except Exception as e:
    print(f"GPIO setup warning: {e}")


def cleanup_resources(led_bulb, buzzer, mqtt_publisher):
    print("\nCleaning up resources...")
    
    if led_bulb:
        try:
            led_bulb.cleanup()
            print("LED cleaned up")
        except Exception as e:
            print(f"Error cleaning up LED: {e}")
    
    if buzzer:
        try:
            buzzer.cleanup()
            print("Buzzer cleaned up")
        except Exception as e:
            print(f"Error cleaning up Buzzer: {e}")
    
    if mqtt_publisher:
        try:
            mqtt_publisher.disconnect()
            print("MQTT disconnected")
        except Exception as e:
            print(f"Error disconnecting MQTT: {e}")


if __name__ == "__main__":
    print('='*50)
    print('Starting IoT Device Application')
    print('='*50)
    
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    
    device_info = settings.get('device', {})
    print(f"\nDevice Configuration:")
    print(f"  PI ID: {device_info.get('pi_id', 'N/A')}")
    print(f"  Device Name: {device_info.get('device_name', 'N/A')}")
    print(f"  Location: {device_info.get('location', 'N/A')}")
    print(f"  Description: {device_info.get('description', 'N/A')}")
    
    led_bulb = None
    buzzer = None
    mqtt_publisher = None
    dms_thread = None
    
    try:
        print("\nInitializing MQTT Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("+ MQTT Publisher ready")
        else:
            print("- MQTT connection failed, continuing without MQTT")
            mqtt_publisher = None
        
        print("\nInitializing LED...")
        if 'DL1' in settings:
            led_bulb = create_led_bulb(settings['DL1'])
            led_bulb.on()
            time.sleep(0.5)
            led_bulb.off()
            print("+ LED initialized")
        
        if 'DB' in settings:
            buzzer = Buzzer(settings['DB']['pin'])
            print("+ Buzzer initialized")

        print("\nStarting Sensors...")
        if 'DS1' in settings:
            run_ds1(settings['DS1'], threads, stop_event, mqtt_publisher)
            print("+ DS1 Door Sensor started")

        if 'DPIR1' in settings:
            run_dpir1(settings['DPIR1'], threads, stop_event, mqtt_publisher)
            print("+ DPIR1 Motion Sensor started")

        if 'DUS1' in settings:
            run_dus1(settings['DUS1'], threads, stop_event, mqtt_publisher)
            print("+ DUS1 Distance Sensor started")

        if 'DMS1' in settings:
            run_dms(settings['DMS1'], threads, stop_event, led_bulb, buzzer, mqtt_publisher)
            print("+ DMS started")

        print("\n" + "="*50)
        print("System running... Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        heartbeat_counter = 0
        while True:
            if led_bulb:
                led_bulb.on()
            time.sleep(1)
            if led_bulb:
                led_bulb.off()
            time.sleep(1)
            
            heartbeat_counter += 1
            if heartbeat_counter % 30 == 0:
                print(f"[Heartbeat] System running for {heartbeat_counter * 2} seconds...")
    
    except KeyboardInterrupt:
        print('\n\nReceived shutdown signal (Ctrl+C)')
    except Exception as e:
        print(f'\n\nUnexpected error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("\nInitiating shutdown sequence...")
        stop_event.set()
        
        print("Waiting for threads to finish...")
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        cleanup_resources(led_bulb, buzzer, mqtt_publisher)
        
        print("\n" + "="*50)
        print("Application stopped successfully")
        print("="*50)
        sys.exit(0)