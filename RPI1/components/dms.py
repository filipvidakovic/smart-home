import threading


def run_dms_console(settings, stop_event, led_actuator, buzzer_actuator):
    if settings['simulated']:

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

                    if entered_pin == correct_pin:
                        print("\n" + "=" * 20)
                        print(">>> ACCESS GRANTED")
                        print("=" * 20 + "\n")

                        if led_actuator:
                            threading.Thread(
                                target=led_actuator.turn_on,
                                args=(3,),
                                daemon=True
                            ).start()
                    else:
                        print("\n" + "x" * 20)
                        print(">>> INVALID PASSWORD")
                        print("x" * 20 + "\n")

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
    else:
        
        from sensors.dms import DMS
        dms = DMS(settings['rows'], settings['cols'])
        dms.run_dms_loop(callback=callback, stop_event=stop_event)

def callback(key):
    print("Key pressed: " + key)