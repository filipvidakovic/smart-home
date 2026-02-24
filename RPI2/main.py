import threading
import time
import sys

from RPI2.settings.settings import load_settings
from RPI2.components.ds2 import run_ds2
from RPI2.components.dpir2 import run_dpir2
from RPI2.components.dus2 import run_dus2
from RPI2.components.dht3 import run_dht3
from RPI2.components.sd4 import SD4Controller
from RPI2.components.btn import run_btn
from RPI2.components.gsg import run_gsg
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
    print('Starting IoT Device Application - PI2 (Kitchen)')
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
    
    try:
        # Initialize MQTT
        print("\nInitializing MQTT Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("MQTT Publisher ready")
        else:
            print("MQTT connection failed, continuing without MQTT")
            mqtt_publisher = None

        # Start Alarm Monitor (shared with PI1)
        print("\nStarting Alarm Monitor...")
        alarm_thread = threading.Thread(
            #TODO Manage alarm
            target=lambda print_func: print_func("Alarm monitor running (no buzzer on PI2)"),
            args=(print),  # No buzzer on PI2
            daemon=True
        )
        alarm_thread.start()
        threads.append(alarm_thread)
        print("Alarm monitor started")

        print("\nStarting Sensors...")
        
        # Distance Sensor (must start before motion for direction detection)
        if 'DUS2' in settings:
            run_dus2(settings['DUS2'], threads, stop_event, mqtt_publisher)
            print("DUS2 Ultrasonic Distance Sensor started")
        
        # Door Sensor
        if 'DS2' in settings:
            run_ds2(settings['DS2'], threads, stop_event, mqtt_publisher)
            print("DS2 Door Sensor started")

        # Motion Sensor (with distance integration)
        if 'DPIR2' in settings:
            run_dpir2(settings['DPIR2'], threads, stop_event, mqtt_publisher)
            print("DPIR2 Motion Sensor started (with tracking)")
        
        # Temperature & Humidity Sensor
        if 'DHT3' in settings:
            run_dht3(settings['DHT3'], threads, stop_event, mqtt_publisher)
            print("DHT3 Temperature & Humidity Sensor started")
        
        # 7-Segment Display Timer
        if 'SD4' in settings:
            SD4Controller(settings['SD4'], stop_event)
            print("SD4 7-Segment Display Timer started")
        
        # Button (for timer control)
        if 'BTN' in settings:
            run_btn(settings['BTN'], threads, stop_event, mqtt_publisher)
            print("BTN Kitchen Button started")
        
        # Gyroscope (Icon protection)
        if 'GSG' in settings:
            run_gsg(settings['GSG'], threads, stop_event, mqtt_publisher)
            print("GSG Gyroscope & Accelerometer started (Icon monitor)")

        print("\n" + "="*60)
        print("System running... Press Ctrl+C to stop")
        # print(f"People in building: {system_state.people_count}")
        # print(f"Security system: {'ARMED' if system_state.security_system_armed else 'DISARMED'}")
        # print(f"Timer: {system_state.timer_seconds}s")
        print("="*60 + "\n")
        
        heartbeat_counter = 0
        while True:
            time.sleep(2)
            
            heartbeat_counter += 1
            if heartbeat_counter % 30 == 0:
                # timer_remaining = system_state.get_timer_remaining()
                print(f"💓 [Heartbeat] Running: {heartbeat_counter * 2}s | "
                    #   f"People: {system_state.people_count} | "
                    #   f"Timer: {timer_remaining}s | "
                    #   f"Alarm: {'ACTIVE' if system_state.alarm_active else 'Clear'}"
                      )
    
    except KeyboardInterrupt:
        print('\n\n  Received shutdown signal (Ctrl+C)')
    except Exception as e:
        print(f'\n\n Unexpected error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("\n Initiating shutdown sequence...")
        stop_event.set()
        
        print(" Waiting for threads to finish...")
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        cleanup_resources(mqtt_publisher)
        
        print("\n" + "="*60)
        print("Application stopped successfully")
        print("="*60)
        sys.exit(0)