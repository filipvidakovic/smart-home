try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available")


class RGBLamp:
    """RGB LED lamp controller using PWM"""
    
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
    
    def __init__(self, red_pin, green_pin, blue_pin):
        if not GPIO_AVAILABLE:
            raise ImportError("RPi.GPIO is required for RGB lamp")
        
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.current_color = 'off'
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        
        # Initialize PWM (100 Hz frequency)
        self.red_pwm = GPIO.PWM(self.red_pin, 100)
        self.green_pwm = GPIO.PWM(self.green_pin, 100)
        self.blue_pwm = GPIO.PWM(self.blue_pin, 100)
        
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
        
        print(f"RGB Lamp: Initialized on pins R={red_pin}, G={green_pin}, B={blue_pin}")
    
    def set_rgb(self, red, green, blue):
        """Set RGB values (0-255)"""
        # Convert to duty cycle (0-100%)
        red_duty = (red / 255) * 100
        green_duty = (green / 255) * 100
        blue_duty = (blue / 255) * 100
        
        self.red_pwm.ChangeDutyCycle(red_duty)
        self.green_pwm.ChangeDutyCycle(green_duty)
        self.blue_pwm.ChangeDutyCycle(blue_duty)
    
    def set_color(self, color_name):
        """Set color by name"""
        color_name = color_name.lower()
        if color_name in self.COLORS:
            r, g, b = self.COLORS[color_name]
            self.set_rgb(r, g, b)
            self.current_color = color_name
            print(f"RGB Lamp: Color set to {color_name} ({r}, {g}, {b})")
            return True
        else:
            print(f"RGB Lamp: Unknown color '{color_name}'")
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
        """Cleanup GPIO"""
        try:
            self.red_pwm.stop()
            self.green_pwm.stop()
            self.blue_pwm.stop()
            GPIO.cleanup([self.red_pin, self.green_pin, self.blue_pin])
            print("RGB Lamp: Cleanup complete")
        except:
            pass
