def create_led_bulb(settings):
    if settings['simulated']:
        from RPI1.simulators.dl import SimulatedLEDBulb
        print("Using simulated LED bulb")
        return SimulatedLEDBulb()
    else:
        from RPI1.sensors.dl import DoorLED
        print("Using real LED bulb")
        return DoorLED(
            pin=settings['pin'],
        )