import threading
import time
import sys
import paho.mqtt.client as mqtt
import json

from RPI2.settings.settings import load_settings
from RPI2.components.ds2 import run_ds2
from RPI2.components.dpir2 import run_dpir2
from RPI2.components.dus2 import run_dus2
from RPI2.components.dht3 import run_dht3
from RPI2.components.sd4 import SD4Controller  # Import directly
from RPI2.components.btn import run_btn
from RPI2.components.gsg import run_gsg
from mqtt.publisher import MQTTPublisher

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")


def cleanup_resources(mqtt_publisher):
    print("\nCleaning up resources...")
    
    if mqtt_publisher:
        try:
            mqtt_publisher.disconnect()
            print("MQTT disconnected")
        except Exception as e:
            print(f"Error disconnecting MQTT: {e}")


if __name__ == "__main__":
    print('='*60)
    print('Starting IoT Device Application - PI2 (Kitchen)')
    print('='*60)
    
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    
    device_info = settings.get('device', {})
    print(f"\nDevice Configuration:")
    print(f"  PI ID: {device_info.get('pi_id', 'N/A')}")
    print(f"  Device Name: {device_info.get('device_name', 'N/A')}")
    print(f"  Location: {device_info.get('location', 'N/A')}")
    
    mqtt_publisher = None
    sd4_controller = None
    
    try:
        # Initialize MQTT Publisher for sensor data
        print("\nInitializing MQTT Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("MQTT Publisher ready")
        else:
            print("MQTT connection failed")
            mqtt_publisher = None

        print("\nStarting Sensors...")
        
        # Distance Sensor (must start before motion)
        if 'DUS2' in settings:
            run_dus2(settings['DUS2'], threads, stop_event, mqtt_publisher)
            print("DUS2 Distance Sensor started")
        
        # Door Sensor
        if 'DS2' in settings:
            run_ds2(settings['DS2'], threads, stop_event, mqtt_publisher)
            print("DS2 Door Sensor started")

        # Motion Sensor
        if 'DPIR2' in settings:
            run_dpir2(settings['DPIR2'], threads, stop_event, mqtt_publisher)
            print("DPIR2 Motion Sensor started")
        
        # Temperature & Humidity Sensor
        if 'DHT3' in settings:
            run_dht3(settings['DHT3'], threads, stop_event, mqtt_publisher)
            print("DHT3 Temperature & Humidity Sensor started")
        
        # SD4 Timer Display Controller with MQTT integration
        if 'SD4' in settings:
            print("\nInitializing SD4 Timer Display...")
            sd4_controller = SD4Controller(settings['SD4'], stop_event)
            
            sd4_thread = threading.Thread(
                target=sd4_controller.run,
                daemon=True
            )
            sd4_thread.start()
            threads.append(sd4_thread)
            
            print("SD4 Timer Display started")
            print("  - Listening on: commands/PI2/#")
            print("  - SD4 will now receive timer commands from server")
        
        # Button (pass sd4_controller so it can notify on press)
        if 'BTN' in settings:
            run_btn(settings['BTN'], threads, stop_event, mqtt_publisher, sd4_controller)
            print("BTN Kitchen Button started")
        
        # Gyroscope
        if 'GSG' in settings:
            run_gsg(settings['GSG'], threads, stop_event, mqtt_publisher)
            print("GSG Gyroscope started")

        print("\n" + "="*60)
        print("PI2 System running... Press Ctrl+C to stop")
        print("="*60)
        print("\nDebug Info:")
        print(f"  - SD4 subscribed to: commands/PI2/#")
        print(f"  - Server should publish to: commands/PI2/timer_set, timer_start, etc.")
        print("="*60 + "\n")
        
        heartbeat_counter = 0
        while True:
            time.sleep(2)
            
            heartbeat_counter += 1
            if heartbeat_counter % 30 == 0:
                print(f"💓 [PI2 Heartbeat] Running: {heartbeat_counter * 2}s")
                if sd4_controller and sd4_controller.mqtt_connected:
                    print(f"   SD4 MQTT: ✓ Connected")
                else:
                    print(f"   SD4 MQTT: ✗ Disconnected")
    
    except KeyboardInterrupt:
        print('\n\nReceived shutdown signal (Ctrl+C)')
    except Exception as e:
        print(f'\n\n❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("\nInitiating shutdown sequence...")
        stop_event.set()
        
        print("Waiting for threads to finish...")
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        cleanup_resources(mqtt_publisher)
        
        print("\n" + "="*60)
        print("PI2 Application stopped successfully")
        print("="*60)
        sys.exit(0)