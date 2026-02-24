import threading
import time
import sys

from RPI1.components.dms import run_dms_console
from RPI1.sensors.db import Buzzer
from RPI1.settings.settings import load_settings
from RPI1.components.ds1 import run_ds1
from RPI1.components.dpir1 import run_dpir1
from RPI1.components.dus1 import run_dus1
from RPI1.components.dl import create_led_bulb
from mqtt.publisher import MQTTPublisher
from shared.mqtt_state_publisher import MQTTStatePublisher
from shared.mqtt_command_listener import MQTTCommandListener

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")
except Exception as e:
    print(f"GPIO setup warning: {e}")


def cleanup_resources(led_bulb, buzzer, mqtt_publisher, state_publisher, command_listener):
    """Cleanup all resources"""
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
    
    if state_publisher:
        try:
            state_publisher.disconnect()
            print("State publisher disconnected")
        except Exception as e:
            print(f"Error disconnecting state publisher: {e}")
    
    if command_listener:
        try:
            command_listener.disconnect()
            print("Command listener disconnected")
        except Exception as e:
            print(f"Error disconnecting command listener: {e}")


if __name__ == "__main__":
    print('='*60)
    print('🏠 Starting IoT Device Application - PI1 (Entrance)')
    print('='*60)
    
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    
    device_info = settings.get('device', {})
    print(f"\n📋 Device Configuration:")
    print(f"  PI ID: {device_info.get('pi_id', 'N/A')}")
    print(f"  Device Name: {device_info.get('device_name', 'N/A')}")
    print(f"  Location: {device_info.get('location', 'N/A')}")
    
    led_bulb = None
    buzzer = None
    mqtt_publisher = None
    state_publisher = None
    command_listener = None
    dms_thread = None
    
    try:
        # Initialize MQTT State Publisher
        print("\n📡 Initializing MQTT State Publisher...")
        state_publisher = MQTTStatePublisher(
            broker=settings['mqtt']['broker'],
            port=settings['mqtt']['port']
        )
        if state_publisher.connect():
            print("State Publisher ready")
        else:
            print("State Publisher failed")
            state_publisher = None
        
        # Initialize MQTT Command Listener
        print("\nInitializing MQTT Command Listener...")
        command_listener = MQTTCommandListener(
            broker=settings['mqtt']['broker'],
            port=settings['mqtt']['port'],
            device_id=device_info.get('pi_id', 'PI1')
        )
        
        if command_listener.connect():
            print("✓ Command Listener ready")
        else:
            print("✗ Command Listener failed")
            command_listener = None
        
        # Initialize MQTT Publisher for sensor data
        print("\n📡 Initializing MQTT Data Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("✓ MQTT Data Publisher ready")
        else:
            print("✗ MQTT Data Publisher failed")
            mqtt_publisher = None
        
        # Initialize LED
        print("\n💡 Initializing LED...")
        if 'DL1' in settings:
            led_bulb = create_led_bulb(settings['DL1'])
            led_bulb.on()
            time.sleep(0.5)
            led_bulb.off()
            print("✓ LED initialized")
        
        # Initialize Buzzer
        if 'DB' in settings:
            buzzer = Buzzer(settings['DB']['pin'])
            print("✓ Buzzer initialized")
        
        # Start Alarm Monitor
        print("\n🚨 Starting Alarm Monitor...")
        alarm_thread = threading.Thread(
            #TODO Manage alarm
            target=lambda print_func, stop_evt: print_func("Alarm monitor running (no buzzer on PI1)"),
            args=(print, stop_event),
            daemon=True
        )
        alarm_thread.start()
        threads.append(alarm_thread)
        print("✓ Alarm monitor started")
        
        # Start Sensors
        print("\n🔌 Starting Sensors...")
        
        if 'DUS1' in settings:
            run_dus1(settings['DUS1'], threads, stop_event, mqtt_publisher)
            print("✓ DUS1 Distance Sensor started")
        
        if 'DPIR1' in settings:
            run_dpir1(settings['DPIR1'], threads, stop_event, mqtt_publisher, led_bulb)
            print("✓ DPIR1 Motion Sensor started (with LED integration)")
        
        if 'DS1' in settings:
            run_ds1(settings['DS1'], threads, stop_event, mqtt_publisher)
            print("✓ DS1 Door Sensor started")
        
        # Start DMS Console
        if 'DMS1' in settings:
            dms_thread = threading.Thread(
                target=run_dms_console,
                args=(settings['DMS1'], stop_event, led_bulb, buzzer)
            )
            dms_thread.daemon = True
            dms_thread.start()
            threads.append(dms_thread)
            print("✓ DMS Console started")
        
        print("\n" + "="*60)
        print("✅ System running... Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        heartbeat_counter = 0
        while True:
            time.sleep(2)
            
            heartbeat_counter += 1
            if heartbeat_counter % 30 == 0:
                print(f"💓 [Heartbeat] Running: {heartbeat_counter * 2}s | "
                      #f"People: {system_state.people_count} | "
                      #f"Alarm: {'ACTIVE' if system_state.alarm_active else 'Clear'}"
                      )
    
    except KeyboardInterrupt:
        print('\n\n Received shutdown signal (Ctrl+C)')
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
        
        cleanup_resources(led_bulb, buzzer, mqtt_publisher, state_publisher, command_listener)
        
        print("\n" + "="*60)
        print("Application stopped successfully")
        print("="*60)
        sys.exit(0)