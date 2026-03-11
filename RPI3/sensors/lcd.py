"""
LCD 1602 Display Driver with I2C Interface
Supports real hardware via I2C communication
"""
import time
import smbus2
import threading


class LCD1602:
    """
    LCD1602 display driver for I2C interface.
    Standard 16x2 character LCD with PCF8574 I2C backpack.
    """
    
    # LCD Commands
    LCD_CLEAR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_DISPLAY_CONTROL = 0x08
    LCD_CURSOR_SHIFT = 0x10
    LCD_FUNCTION_SET = 0x20
    LCD_SET_CGRAM = 0x40
    LCD_SET_DDRAM = 0x80
    
    # Flags for display entry mode
    LCD_ENTRY_RIGHT = 0x00
    LCD_ENTRY_LEFT = 0x02
    LCD_ENTRY_SHIFT_INCREMENT = 0x01
    LCD_ENTRY_SHIFT_DECREMENT = 0x00
    
    # Flags for display on/off control
    LCD_DISPLAY_ON = 0x04
    LCD_DISPLAY_OFF = 0x00
    LCD_CURSOR_ON = 0x02
    LCD_CURSOR_OFF = 0x00
    LCD_BLINK_ON = 0x01
    LCD_BLINK_OFF = 0x00
    
    # Flags for function set
    LCD_8BIT_MODE = 0x10
    LCD_4BIT_MODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10_DOTS = 0x04
    LCD_5x8_DOTS = 0x00
    
    # Backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00
    
    # Enable bit
    ENABLE = 0b00000100
    
    def __init__(self, i2c_address=0x27, i2c_bus=1):
        """
        Initialize LCD display.
        
        Args:
            i2c_address: I2C address of the LCD (default 0x27)
            i2c_bus: I2C bus number (default 1)
        """
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.bus = smbus2.SMBus(i2c_bus)
        self.backlight_state = self.LCD_BACKLIGHT
        self.lock = threading.Lock()
        
        # Initialize display
        self._init_display()
        print(f"LCD1602: Initialized at address 0x{i2c_address:02X} on I2C bus {i2c_bus}")
    
    def _init_display(self):
        """Initialize the LCD display with 4-bit mode."""
        time.sleep(0.05)  # Wait for LCD to power up
        
        # Put LCD into 4-bit mode
        self._write_4bits(0x03 << 4)
        time.sleep(0.005)
        self._write_4bits(0x03 << 4)
        time.sleep(0.005)
        self._write_4bits(0x03 << 4)
        time.sleep(0.001)
        self._write_4bits(0x02 << 4)
        
        # Configure display
        self._command(self.LCD_FUNCTION_SET | self.LCD_4BIT_MODE | self.LCD_2LINE | self.LCD_5x8_DOTS)
        self._command(self.LCD_DISPLAY_CONTROL | self.LCD_DISPLAY_ON | self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF)
        self._command(self.LCD_CLEAR)
        time.sleep(0.002)
        self._command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_LEFT | self.LCD_ENTRY_SHIFT_DECREMENT)
    
    def _write_4bits(self, data):
        """Write 4 bits to LCD."""
        with self.lock:
            self.bus.write_byte(self.i2c_address, data | self.backlight_state)
            self._pulse_enable(data)
    
    def _pulse_enable(self, data):
        """Pulse the enable bit."""
        self.bus.write_byte(self.i2c_address, data | self.ENABLE | self.backlight_state)
        time.sleep(0.0001)
        self.bus.write_byte(self.i2c_address, (data & ~self.ENABLE) | self.backlight_state)
        time.sleep(0.0001)
    
    def _command(self, cmd):
        """Send command to LCD."""
        self._write_4bits(cmd & 0xF0)
        self._write_4bits((cmd << 4) & 0xF0)
    
    def _write_char(self, char):
        """Write a single character to LCD."""
        self._write_4bits(0x01 | (char & 0xF0))
        self._write_4bits(0x01 | ((char << 4) & 0xF0))
    
    def clear(self):
        """Clear the display."""
        self._command(self.LCD_CLEAR)
        time.sleep(0.002)
    
    def set_cursor(self, row, col):
        """
        Set cursor position.
        
        Args:
            row: Row number (0 or 1)
            col: Column number (0-15)
        """
        row_offsets = [0x00, 0x40]
        if row < 0 or row > 1:
            row = 0
        self._command(self.LCD_SET_DDRAM | (col + row_offsets[row]))
    
    def write_string(self, text, row=0, col=0):
        """
        Write string to LCD at specified position.
        
        Args:
            text: Text to display (max 16 chars per line)
            row: Row number (0 or 1)
            col: Column number (0-15)
        """
        self.set_cursor(row, col)
        for char in text[:16 - col]:  # Don't exceed line length
            self._write_char(ord(char))
    
    def backlight_on(self):
        """Turn backlight on."""
        self.backlight_state = self.LCD_BACKLIGHT
        with self.lock:
            self.bus.write_byte(self.i2c_address, self.backlight_state)
    
    def backlight_off(self):
        """Turn backlight off."""
        self.backlight_state = self.LCD_NOBACKLIGHT
        with self.lock:
            self.bus.write_byte(self.i2c_address, self.backlight_state)
    
    def cleanup(self):
        """Clean up resources."""
        self.clear()
        self.backlight_off()
        self.bus.close()
        print("LCD1602: Cleaned up")
