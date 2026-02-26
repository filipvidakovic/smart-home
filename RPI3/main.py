import threading
import time
import sys

from RPI3.settings.settings import load_settings
from RPI3.components.dht1 import run_dht1
from RPI3.components.dht2 import run_dht2
from mqtt.publisher import MQTTPublisher

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")
except Exception as e:
    print(f"GPIO setup warning: {e}")


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
    print('Starting IoT Device Application - PI3 (Bedrooms)')
    print('='*60)
    
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    
    device_info = settings.get('device', {})
    print(f"\n Device Configuration:")
    print(f"  PI ID: {device_info.get('pi_id', 'N/A')}")
    print(f"  Device Name: {device_info.get('device_name', 'N/A')}")
    print(f"  Location: {device_info.get('location', 'N/A')}")
    print(f"  Description: {device_info.get('description', 'N/A')}")
    
    mqtt_publisher = None
    lcd_controller = None  # TODO: Implement LCD controller later
    
    try:
        # Initialize MQTT
        print("\nInitializing MQTT Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("✓ MQTT Publisher ready")
        else:
            print("⚠ MQTT connection failed, continuing without MQTT")
            mqtt_publisher = None

        print("\nStarting Sensors...")
        
        # DHT1 - Bedroom Temperature & Humidity Sensor
        if 'DHT1' in settings:
            run_dht1(settings['DHT1'], threads, stop_event, mqtt_publisher, lcd_controller)
            print("✓ DHT1 Temperature & Humidity Sensor started (Bedroom)")
        
        # DHT2 - Master Bedroom Temperature & Humidity Sensor
        if 'DHT2' in settings:
            run_dht2(settings['DHT2'], threads, stop_event, mqtt_publisher, lcd_controller)
            print("✓ DHT2 Temperature & Humidity Sensor started (Master Bedroom)")
        
        # TODO: Add other sensors when ready:
        # - DPIR3 (Motion sensor)
        # - IR (Infrared sensor)
        # - BRGB (RGB LED)
        # - LCD (Display controller)
        
        print("\n" + "="*60)
        print("All components initialized successfully!")
        print("Press Ctrl+C to stop...")
        print("="*60 + "\n")
        
        # Keep main thread alive
        while not stop_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        stop_event.set()
        
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        stop_event.set()
        
    finally:
        # Wait for threads
        print("\nWaiting for threads to complete...")
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=2)
        
        # Cleanup
        cleanup_resources(mqtt_publisher)
        
        try:
            GPIO.cleanup()
            print("GPIO cleaned up")
        except:
            pass
        
        print("\n" + "="*60)
        print("PI3 Application stopped cleanly")
        print("="*60)
        sys.exit(0)
