def create_led_bulb(settings):
    if settings['simulated']:
        from simulators.dl import SimulatedLEDBulb
        print("Using simulated LED bulb")
        return SimulatedLEDBulb()
    else:
        from sensors.dl import DoorLED
        print("Using real LED bulb")
        return DoorLED(
            pin=settings['pin'],
        )