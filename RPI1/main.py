import threading
import time
import sys
import paho.mqtt.client as mqtt
import json

from RPI1.components.dms import run_dms_console
from RPI1.sensors.db import Buzzer
from RPI1.settings.settings import load_settings
from RPI1.components.ds1 import run_ds1
from RPI1.components.dpir1 import run_dpir1
from RPI1.components.dus1 import run_dus1
from RPI1.components.dl import create_led_bulb
from mqtt.publisher import MQTTPublisher

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")


# Simple command listener for PI1
command_mqtt_client = None

def on_connect_commands(client, userdata, flags, rc):
    if rc == 0:
        # PI1 ONLY subscribes to PI1 commands and "all" broadcasts
        client.subscribe("commands/PI1/#")
        client.subscribe("commands/all/#")
        print("✓ PI1: Subscribed to commands/PI1/# and commands/all/#")

def on_message_commands(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        print(f"PI1 Command received: {topic}")
        
        # Handle security commands
        if "security_armed" in topic or "alarm_cleared" in topic:
            print(f"✓ PI1: Processed {topic}")
        
    except Exception as e:
        print(f"PI1: Error processing command - {e}")

def start_command_listener_pi1():
    global command_mqtt_client
    command_mqtt_client = mqtt.Client(client_id="PI1_command_listener")
    command_mqtt_client.on_connect = on_connect_commands
    command_mqtt_client.on_message = on_message_commands
    command_mqtt_client.connect("localhost", 1883, 60)
    command_mqtt_client.loop_start()


def cleanup_resources(led_bulb, buzzer, mqtt_publisher):
    print("\nCleaning up resources...")
    
    if led_bulb:
        try:
            led_bulb.cleanup()
        except Exception as e:
            print(f"Error cleaning up LED: {e}")
    
    if buzzer:
        try:
            buzzer.cleanup()
        except Exception as e:
            print(f"Error cleaning up Buzzer: {e}")
    
    if mqtt_publisher:
        try:
            mqtt_publisher.disconnect()
        except Exception as e:
            print(f"Error disconnecting MQTT: {e}")
    
    if command_mqtt_client:
        try:
            command_mqtt_client.loop_stop()
            command_mqtt_client.disconnect()
        except:
            pass


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
    dms_thread = None
    
    try:
        # Start PI1 command listener
        print("\n Starting PI1 Command Listener...")
        start_command_listener_pi1()
        
        # Initialize MQTT Publisher for sensor data
        print("\n Initializing MQTT Data Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("✓ MQTT Data Publisher ready")
        else:
            print("✗ MQTT Data Publisher failed")
            mqtt_publisher = None
        
        # Initialize LED
        print("\n Initializing LED...")
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
        
        print("\n Starting Sensors...")
        
        # Distance Sensor (for motion direction)
        if 'DUS1' in settings:
            run_dus1(settings['DUS1'], threads, stop_event, mqtt_publisher)
            print("✓ DUS1 Distance Sensor started")
        
        # Motion Sensor
        if 'DPIR1' in settings:
            run_dpir1(settings['DPIR1'], threads, stop_event, mqtt_publisher, led_bulb)
            print("✓ DPIR1 Motion Sensor started")
        
        # Door Sensor
        if 'DS1' in settings:
            run_ds1(settings['DS1'], threads, stop_event, mqtt_publisher)
            print("✓ DS1 Door Sensor started")
        
        # Start DMS Console (optional)
        # if 'DMS1' in settings:
        #     dms_thread = threading.Thread(
        #         target=run_dms_console,
        #         args=(settings['DMS1'], stop_event, led_bulb, buzzer)
        #     )
        #     dms_thread.daemon = True
        #     dms_thread.start()
        #     threads.append(dms_thread)
        #     print("✓ DMS Console started")
        
        print("\n" + "="*60)
        print("PI1 System running... Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        heartbeat_counter = 0
        while True:
            time.sleep(2)
            
            heartbeat_counter += 1
            if heartbeat_counter % 30 == 0:
                print(f"💓 [PI1 Heartbeat] Running: {heartbeat_counter * 2}s")
    
    except KeyboardInterrupt:
        print('\n\n  Received shutdown signal (Ctrl+C)')
    except Exception as e:
        print(f'\n\n Unexpected error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("\n Initiating shutdown sequence...")
        stop_event.set()
        
        print("Waiting for threads to finish...")
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        cleanup_resources(led_bulb, buzzer, mqtt_publisher)
        
        print("\n" + "="*60)
        print("PI1 Application stopped successfully")
        print("="*60)
        sys.exit(0)