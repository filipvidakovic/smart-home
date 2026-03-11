"""
LCD 1602 Display Simulator
Simulates a 16x2 character LCD display by printing to console
"""
import time
import threading


class LCD1602Simulator:
    """
    Simulates a 16x2 character LCD display.
    Displays output to console in a formatted box.
    """
    
    def __init__(self, i2c_address=0x27, i2c_bus=1):
        """
        Initialize LCD simulator.
        
        Args:
            i2c_address: Simulated I2C address (for compatibility)
            i2c_bus: Simulated I2C bus (for compatibility)
        """
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.backlight = True
        self.lock = threading.Lock()
        
        # Display buffer - 2 rows of 16 characters
        self.buffer = [
            [' '] * 16,  # Row 0
            [' '] * 16   # Row 1
        ]
        
        self.cursor_row = 0
        self.cursor_col = 0
        
        print(f"LCD1602 Simulator: Initialized (simulated address 0x{i2c_address:02X})")
        self._render_display()
    
    def _render_display(self):
        """Render the LCD display to console."""
        with self.lock:
            border = "╔" + "═" * 16 + "╗"
            print("\n" + border)
            for row in self.buffer:
                print("║" + ''.join(row) + "║")
            print("╚" + "═" * 16 + "╝")
            if self.backlight:
                print("  [Backlight: ON]")
            else:
                print("  [Backlight: OFF]")
    
    def clear(self):
        """Clear the display."""
        with self.lock:
            self.buffer = [
                [' '] * 16,
                [' '] * 16
            ]
            self.cursor_row = 0
            self.cursor_col = 0
        print("\n[LCD] Display cleared")
        self._render_display()
    
    def set_cursor(self, row, col):
        """
        Set cursor position.
        
        Args:
            row: Row number (0 or 1)
            col: Column number (0-15)
        """
        if 0 <= row < 2 and 0 <= col < 16:
            self.cursor_row = row
            self.cursor_col = col
    
    def write_string(self, text, row=0, col=0):
        """
        Write string to LCD at specified position.
        
        Args:
            text: Text to display
            row: Row number (0 or 1)
            col: Column number (0-15)
        """
        self.set_cursor(row, col)
        
        with self.lock:
            for char in text:
                if self.cursor_col < 16:
                    self.buffer[self.cursor_row][self.cursor_col] = char
                    self.cursor_col += 1
                else:
                    break
        
        print(f"\n[LCD] Writing at ({row},{col}): '{text}'")
        self._render_display()
    
    def backlight_on(self):
        """Turn backlight on."""
        self.backlight = True
        print("\n[LCD] Backlight ON")
        self._render_display()
    
    def backlight_off(self):
        """Turn backlight off."""
        self.backlight = False
        print("\n[LCD] Backlight OFF")
        self._render_display()
    
    def cleanup(self):
        """Clean up resources."""
        self.clear()
        self.backlight_off()
        print("LCD1602 Simulator: Cleaned up")
