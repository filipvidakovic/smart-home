class SimulatedLEDBulb:
    def on(self):
        print(" LED BULB ON")

    def off(self):
        print(" LED BULB OFF")

    def set(self, state: bool):
        print(f" LED BULB {'ON' if state else 'OFF'}")

    def cleanup(self):
        pass
