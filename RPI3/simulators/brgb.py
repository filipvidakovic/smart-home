import random
import time
import threading
from typing import Callable


class SimulatedRGBLamp:
    """Simulated RGB LED lamp that cycles through random colors"""
    
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
    
    COLOR_EMOJIS = {
        'red': '🔴',
        'green': '🟢',
        'blue': '🔵',
        'yellow': '💛',
        'cyan': '🟦',
        'magenta': '💜',
        'white': '⚪',
        'orange': '🟠',
        'purple': '🟪',
        'pink': '🩷',
        'off': '⚫',
    }
    
    def __init__(self):
        self.current_color = 'off'
        self.last_color_change = time.time()
        self.color_change_interval = random.uniform(2, 5)  # Change color every 2-5 seconds
        self.available_colors = list(self.COLORS.keys())
        print("💡 Simulated RGB Lamp initialized - will cycle through colors")
    
    def _update_color_if_needed(self):
        """Automatically change color if interval has passed"""
        current_time = time.time()
        if current_time - self.last_color_change > self.color_change_interval:
            # Pick a random color (including off)
            new_color = random.choice(self.available_colors)
            if new_color != self.current_color:
                self.set_color(new_color)
            self.last_color_change = current_time
            self.color_change_interval = random.uniform(2, 5)  # Set new interval
    
    def set_rgb(self, red, green, blue):
        """Set RGB values (0-255)"""
        print(f"💡 RGB Lamp: RGB=({red}, {green}, {blue})")
    
    def set_color(self, color_name):
        """Set color by name"""
        color_name = color_name.lower()
        if color_name in self.COLORS:
            r, g, b = self.COLORS[color_name]
            self.current_color = color_name
            emoji = self.COLOR_EMOJIS.get(color_name, '💡')
            print(f"{emoji} RGB Lamp: Color set to {color_name.upper()} (RGB: {r}, {g}, {b})")
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
        self._update_color_if_needed()  # Check if color should change
        return self.current_color
    
    def cleanup(self):
        """Cleanup"""
        print("💡 RGB Lamp: Cleanup complete")


def run_brgb_simulator(lamp: SimulatedRGBLamp, interval: float, stop_event):
    """Run RGB lamp simulator loop that periodically changes colors"""
    print(f"💡 RGB Lamp Simulator: Starting color cycle loop (interval={interval}s)")
    
    try:
        while not stop_event.is_set():
            # Check and update color if needed
            lamp._update_color_if_needed()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("💡 RGB Lamp Simulator: Interrupted")
    finally:
        print("💡 RGB Lamp Simulator: Stopped")
