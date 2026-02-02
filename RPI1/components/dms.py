import threading
import time


def _activate_led(led_actuator, seconds=3):
    if not led_actuator:
        return
    led_actuator.on()
    time.sleep(seconds)
    led_actuator.off()


def _handle_pin_entry(entered_pin, correct_pin, led_actuator, buzzer_actuator):
    if entered_pin == correct_pin:
        print("\n" + "=" * 20)
        print(">>> ACCESS GRANTED")
        print("=" * 20 + "\n")
        if led_actuator:
            threading.Thread(
                target=_activate_led,
                args=(led_actuator, 3),
                daemon=True
            ).start()
    else:
        print("\n" + "x" * 20)
        print(">>> INVALID PASSWORD")
        print("x" * 20 + "\n")
        if buzzer_actuator:
            threading.Thread(
                target=buzzer_actuator.ring,
                kwargs={"times": 2},
                daemon=True
            ).start()


def _keypad_callback_factory(settings, led_actuator, buzzer_actuator, mqtt_publisher=None):
    correct_pin = settings.get('pin_code', '1234')
    pin_buffer = {"value": ""}
    
    # Map keys to numeric values for MQTT
    key_map = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
        '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        '*': 10, '#': 11
    }

    def callback(key, timestamp=None):
        # Publish key press to MQTT
        if mqtt_publisher and settings:
            mqtt_publisher.add_reading(
                sensor_type='membrane',
                value=key_map.get(key, -1),
                simulated=settings.get('simulated', False)
            )
        
        t = time.localtime(timestamp if timestamp else time.time())
        print("=" * 20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Membrane key pressed: {key}")
        
        if key == '*':
            pin_buffer["value"] = ""
            print("[DMS] PIN cleared")
            return
        if key == '#':
            _handle_pin_entry(
                pin_buffer["value"],
                correct_pin,
                led_actuator,
                buzzer_actuator
            )
            pin_buffer["value"] = ""
            return
        pin_buffer["value"] += key
        print(f"[DMS] PIN: {'*' * len(pin_buffer['value'])}")

    return callback


def run_dms_console(settings, stop_event, led_actuator, buzzer_actuator, mqtt_publisher=None):
    correct_pin = settings.get('pin_code', '1234')
    print("--- DMS & DB Console Active ---")
    print("Commands:")
    print("  dms [code]  -> unlock (LED on for 3s)")
    print("  db          -> doorbell")
    print("  led_on      -> LED bulb ON")
    print("  led_off     -> LED bulb OFF")
    print("  exit")

    while not stop_event.is_set():
        try:
            user_input = input("> ").strip().split()
            if not user_input:
                continue

            command = user_input[0].lower()

            # Exit app
            if command == "exit":
                stop_event.set()
                break

            # Doorbell
            elif command == "db":
                if buzzer_actuator:
                    threading.Thread(
                        target=buzzer_actuator.ring,
                        daemon=True
                    ).start()
                else:
                    print("[SYSTEM] Buzzer not connected.")

            # Door management system
            elif command == "dms" and len(user_input) > 1:
                entered_pin = user_input[1]
                _handle_pin_entry(
                    entered_pin,
                    correct_pin,
                    led_actuator,
                    buzzer_actuator
                )

            # LED manual control
            elif command == "led_on":
                if led_actuator:
                    led_actuator.on()
                else:
                    print("[SYSTEM] LED not connected.")

            elif command == "led_off":
                if led_actuator:
                    led_actuator.off()
                else:
                    print("[SYSTEM] LED not connected.")

            else:
                print("[SYSTEM] Unknown command.")

        except EOFError:
            stop_event.set()
            break


def run_dms(settings, threads, stop_event, led_actuator=None, buzzer_actuator=None, mqtt_publisher=None):
    callback = _keypad_callback_factory(settings, led_actuator, buzzer_actuator, mqtt_publisher)
    
    if settings['simulated']:
        from RPI1.simulators.dms import run_dms_simulator
        print("Starting DMS simulator")
        delay = settings.get('delay', 2)
        dms_thread = threading.Thread(
            target=run_dms_simulator,
            args=(delay, callback, stop_event),
            daemon=True
        )
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS simulator started")
        
        # Also start console for manual commands
        console_thread = threading.Thread(
            target=run_dms_console,
            args=(settings, stop_event, led_actuator, buzzer_actuator, mqtt_publisher),
            daemon=True
        )
        console_thread.start()
        threads.append(console_thread)
    else:
        from sensors.dms import DMS
        dms = DMS(settings['rows'], settings['cols'])
        print("Starting DMS keypad loop")
        dms_thread = threading.Thread(
            target=dms.run_dms_loop,
            args=(callback, stop_event),
            daemon=True
        )
        dms_thread.start()
        threads.append(dms_thread)
        print("DMS keypad loop started")