import threading


def run_dms_console(settings, stop_event, led_actuator, buzzer_actuator):
    correct_pin = settings.get('pin_code', '1234')

    print("--- DMS & DB Console Active ---")
    print("Commands: 'dms [code]', 'db' (doorbell), 'exit'")

    while not stop_event.is_set():
        try:
            # Čeka unos u terminalu
            user_input = input().strip().split()

            if not user_input: continue

            command = user_input[0].lower()

            if command == "exit":
                stop_event.set()
                break

            if command == "db":
                if buzzer_actuator:
                    # Pokrećemo u novoj niti da ne blokiramo konzolu dok zvoni
                    threading.Thread(target=buzzer_actuator.ring).start()
                else:
                    print("[SYSTEM] Buzzer not connected.")

            if command == "dms" and len(user_input) > 1:
                entered_pin = user_input[1]
                if entered_pin == correct_pin:
                    print("\n" + "=" * 20)
                    print(">>> ACCESS GRANTED")
                    print("=" * 20 + "\n")
                    # Ako imamo LED, upali ga na 3 sekunde
                    if led_actuator:
                        threading.Thread(target=led_actuator.turn_on, args=(3,)).start()
                else:
                    print("\n" + "x" * 20)
                    print(">>> INVALID PASSWORD")
                    print("x" * 20 + "\n")

        except EOFError:
            break