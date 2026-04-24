import threading
import time
import sys
import os

# Allow running as script: python RPI3/main.py
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RPI3.settings.settings import load_settings
from RPI3.components.dht1 import run_dht1
from RPI3.components.dht2 import run_dht2
from RPI3.components.dpir3 import run_dpir3
from RPI3.components.lcd import run_lcd
from RPI3.components.brgb import run_brgb
from RPI3.components.ir import run_ir
from mqtt.publisher import MQTTPublisher
from shared.mqtt_command_listener import MQTTCommandListener

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    print("RPi.GPIO not available, running in simulation mode")
except Exception as e:
    print(f"GPIO setup warning: {e}")


BRGB_COLOR_TO_INDEX = {
    'off': 0,
    'red': 1,
    'green': 2,
    'blue': 3,
    'yellow': 4,
    'cyan': 5,
    'magenta': 6,
    'white': 7,
    'orange': 8,
    'purple': 9,
    'pink': 10
}


def publish_brgb_state(rgb_lamp, mqtt_publisher, stop_event, interval=1.0):
    """Continuously publish BRGB state so backend/frontend can track simulator changes."""
    print("🌈 BRGB state publisher started")
    last_color = None

    while not stop_event.is_set():
        try:
            color = rgb_lamp.get_current_color() if rgb_lamp else 'off'
            if color != last_color:
                mqtt_publisher.publish_reading_now(
                    sensor_type='brgb_color',
                    value=BRGB_COLOR_TO_INDEX.get(color, 0),
                    simulated=True,
                    sensor_id='BRGB'
                )
                mqtt_publisher.publish_reading_now(
                    sensor_type='brgb_power',
                    value=0 if color == 'off' else 1,
                    simulated=True,
                    sensor_id='BRGB'
                )
                last_color = color
        except Exception as e:
            print(f"⚠️ BRGB state publish error: {e}")

        time.sleep(interval)


def cleanup_resources(mqtt_publisher, command_listener=None):
    print("\nCleaning up resources...")
    
    if mqtt_publisher:
        try:
            mqtt_publisher.disconnect()
            print("MQTT disconnected")
        except Exception as e:
            print(f"Error disconnecting MQTT: {e}")
    
    if command_listener:
        try:
            command_listener.disconnect()
            print("Command listener disconnected")
        except Exception as e:
            print(f"Error disconnecting command listener: {e}")


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
    command_listener = None
    lcd_controller = None
    rgb_lamp = None
    ir_remote = None
    dht1_sensor = None
    dht2_sensor = None
    dpir3_sensor = None
    brgb_state_thread = None
    
    # Create a mutable wrapper for LCD controller (can be updated later)
    class LCDWrapper:
        def __init__(self):
            self.controller = None
        
        def update_sensor(self, temperature, humidity):
            if self.controller:
                self.controller.update_sensor(temperature, humidity)
    
    lcd_wrapper = LCDWrapper()
    
    try:
        # Initialize MQTT Publisher
        print("\nInitializing MQTT Publisher...")
        mqtt_publisher = MQTTPublisher(settings)
        if mqtt_publisher.connect():
            mqtt_publisher.start_daemon()
            print("✓ MQTT Publisher ready")
        else:
            print("⚠ MQTT connection failed, continuing without MQTT")
            mqtt_publisher = None
        
        # Initialize MQTT Command Listener
        print("\nInitializing MQTT Command Listener...")
        mqtt_settings = settings.get('mqtt', {})
        command_listener = MQTTCommandListener(
            broker=mqtt_settings.get('broker', 'localhost'),
            port=mqtt_settings.get('port', 1883),
            device_id=settings.get('device', {}).get('pi_id', 'PI3')
        )
        if command_listener.connect():
            print("✓ Command Listener ready")
        else:
            print("⚠ Command Listener failed, continuing without commands")
            command_listener = None

        print("\nStarting Sensors...")
        
        # DHT1 - Bedroom Temperature & Humidity Sensor
        if 'DHT1' in settings:
            dht1_sensor = run_dht1(settings['DHT1'], threads, stop_event, mqtt_publisher, lcd_wrapper)
            print("✓ DHT1 Temperature & Humidity Sensor started (Bedroom)")
        
        # DHT2 - Master Bedroom Temperature & Humidity Sensor
        if 'DHT2' in settings:
            dht2_sensor = run_dht2(settings['DHT2'], threads, stop_event, mqtt_publisher, lcd_wrapper)
            print("✓ DHT2 Temperature & Humidity Sensor started (Master Bedroom)")

        # DPIR3 - Bedroom Motion Sensor
        if 'DPIR3' in settings:
            dpir3_sensor = run_dpir3(settings['DPIR3'], threads, stop_event, mqtt_publisher)
            print("✓ DPIR3 Motion Sensor started (Bedroom)")
        
        # Check if IR is simulated - it will control BRGB exclusively
        ir_controls_brgb = 'IR' in settings and settings['IR'].get('simulated', False)
        
        # BRGB - RGB LED Lamp
        if 'BRGB' in settings:
            brgb_settings = settings['BRGB'].copy()
            
            if ir_controls_brgb:
                # IR controls BRGB - disable BRGB's own simulation
                print("⚠️  IR simulator detected - BRGB auto-cycling disabled (IR will control it)")
                brgb_settings['simulated'] = False  # Disable BRGB auto-simulation
                # Create BRGB but don't start its thread - IR will control it
                from RPI3.simulators.brgb import SimulatedRGBLamp
                rgb_lamp = SimulatedRGBLamp()
                print("✓ BRGB RGB Lamp initialized (controlled by IR)")
            else:
                # Normal BRGB operation with auto-cycling
                rgb_lamp = run_brgb(brgb_settings, threads, stop_event, command_listener)
                print("✓ BRGB RGB Lamp initialized")
        
        # IR - Infrared Remote
        if 'IR' in settings:
            ir_remote = run_ir(settings['IR'], command_listener, brgb_lamp=rgb_lamp, threads=threads, stop_event=stop_event)
            print("✓ IR Remote initialized")

        if rgb_lamp and mqtt_publisher:
            brgb_state_thread = threading.Thread(
                target=publish_brgb_state,
                args=(rgb_lamp, mqtt_publisher, stop_event, 1.0),
                daemon=True
            )
            brgb_state_thread.start()
            threads.append(brgb_state_thread)
            print("✓ BRGB state sync publisher started")

        print("\nInitializing LCD Display...")
        if 'LCD' in settings:
            # Create a dummy sensor object for LCD if DHT1 is available (even if simulated)
            dummy_sensor = dht1_sensor if dht1_sensor else object()  # Use dummy object if no real sensor
            try:
                lcd_controller = run_lcd(settings['LCD'], stop_event, dht_sensor=dummy_sensor, mqtt_publisher=mqtt_publisher)
                if lcd_controller:
                    lcd_wrapper.controller = lcd_controller  # Update wrapper so DHT sensors can use it
                    print("✓ LCD Display ready")
                else:
                    print("⚠ LCD Display skipped")
            except Exception as e:
                print(f"⚠ LCD initialization error: {e}")
                import traceback
                traceback.print_exc()
        
        # TODO: Add other sensors when ready:
        # - IR (Infrared sensor)
        
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
        cleanup_resources(mqtt_publisher, command_listener)
        
        if lcd_controller:
            try:
                lcd_controller.cleanup()
            except Exception as e:
                print(f"Error cleaning up LCD: {e}")
        
        
        if ir_remote:
            try:
                ir_remote.cleanup()
            except Exception as e:
                print(f"Error cleaning up IR Remote: {e}")
        if rgb_lamp:
            try:
                rgb_lamp.cleanup()
            except Exception as e:
                print(f"Error cleaning up RGB Lamp: {e}")
        
        try:
            GPIO.cleanup()
            print("GPIO cleaned up")
        except:
            pass
        
        print("\n" + "="*60)
        print("PI3 Application stopped cleanly")
        print("="*60)
        sys.exit(0)
