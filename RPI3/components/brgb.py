import threading


def create_rgb_lamp(settings):
    """Factory function to create RGB lamp instance"""
    if settings.get('simulated', False):
        from RPI3.simulators.brgb import SimulatedRGBLamp
        print("Using simulated RGB lamp")
        return SimulatedRGBLamp()
    else:
        from RPI3.sensors.brgb import RGBLamp
        print("Using real RGB lamp")
        # Assuming RGB pins are provided in settings
        return RGBLamp(
            red_pin=settings.get('red_pin', 17),
            green_pin=settings.get('green_pin', 27),
            blue_pin=settings.get('blue_pin', 22)
        )


def run_brgb(settings, command_listener=None):
    """Initialize RGB lamp and register command callback"""
    
    lamp = create_rgb_lamp(settings)
    
    def handle_lamp_command(payload):
        """Handle lamp control commands"""
        try:
            command = payload.get('command', '')
            
            if command == 'on':
                color = payload.get('color', 'white')
                lamp.on(color)
            elif command == 'off':
                lamp.off()
            elif command == 'set_color':
                color = payload.get('color', 'white')
                lamp.set_color(color)
            else:
                print(f"⚠️  RGB Lamp: Unknown command '{command}'")
        
        except Exception as e:
            print(f"✗ RGB Lamp: Error handling command: {e}")
            import traceback
            traceback.print_exc()
    
    # Register command callback if command listener exists
    if command_listener:
        command_listener.register_callback('lamp_control', handle_lamp_command)
        print("✓ RGB Lamp: Registered command callback")
    
    return lamp
