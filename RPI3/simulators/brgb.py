class SimulatedRGBLamp:
    """Simulated RGB LED lamp"""
    
    COLORS = {
        'off': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'white': (255, 255, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
    }
    
    def __init__(self):
        self.current_color = 'off'
        print("💡 Simulated RGB Lamp initialized")
    
    def set_rgb(self, red, green, blue):
        """Set RGB values (0-255)"""
        print(f"💡 RGB Lamp: RGB=({red}, {green}, {blue})")
    
    def set_color(self, color_name):
        """Set color by name"""
        color_name = color_name.lower()
        if color_name in self.COLORS:
            r, g, b = self.COLORS[color_name]
            self.current_color = color_name
            print(f"💡 RGB Lamp: Color set to {color_name.upper()} ({r}, {g}, {b})")
            return True
        else:
            print(f"💡 RGB Lamp: Unknown color '{color_name}'")
            return False
    
    def on(self, color='white'):
        """Turn lamp on with specified color"""
        self.set_color(color)
    
    def off(self):
        """Turn lamp off"""
        self.set_color('off')
    
    def is_on(self):
        """Check if lamp is on"""
        return self.current_color != 'off'
    
    def get_current_color(self):
        """Get current color name"""
        return self.current_color
    
    def cleanup(self):
        """Cleanup"""
        print("💡 RGB Lamp: Cleanup complete")
