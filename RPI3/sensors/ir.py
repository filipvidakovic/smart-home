try:
    import RPi.GPIO as GPIO
    import lirc
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO or lirc not available")


class IRRemote:
    """Infrared Remote controller - sends and receives IR signals"""
    
    # Common IR device codes
    DEVICES = {
        'brgb': 'BRGB Lamp',
    }
    
    # Common IR commands
    COMMANDS = {
        'power': 'POWER',
        'on': 'ON',
        'off': 'OFF',
        'color_next': 'COLOR_NEXT',
        'color_prev': 'COLOR_PREV',
    }
    
    def __init__(self, tx_pin=None, rx_pin=None):
        """Initialize IR remote
        
        Args:
            tx_pin: GPIO pin for IR transmitter (optional)
            rx_pin: GPIO pin for IR receiver (optional)
        """
        if not GPIO_AVAILABLE:
            raise ImportError("RPi.GPIO and lirc are required for IR Remote")
        
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.last_command_sent = None
        self.last_device_controlled = None
        
        if tx_pin:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.tx_pin, GPIO.OUT)
            print(f"IR Remote: Transmitter initialized on pin {tx_pin}")
        
        print(f"IR Remote: Initialized (TX: {tx_pin}, RX: {rx_pin})")
    
    def send_command(self, device, command):
        """Send IR command to a device
        
        Args:
            device: Target device (e.g., 'tv', 'ac')
            command: Command to send (e.g., 'power', 'volume_up')
        
        Returns:
            bool: True if command sent successfully
        """
        if not self.tx_pin:
            print("IR Remote: No transmitter configured")
            return False
        
        try:
            # In real implementation, this would use lirc to send IR codes
            self.last_command_sent = command
            self.last_device_controlled = device
            print(f"🔴 IR Remote: Sent '{command}' to {device}")
            return True
        except Exception as e:
            print(f"IR Remote: Error sending command: {e}")
            return False
    
    def send_power_toggle(self, device):
        """Toggle power on a device"""
        return self.send_command(device, 'power')
    
    def send_color_next(self):
        """Next color on BRGB lamp"""
        return self.send_command('brgb', 'color_next')
    
    def send_color_prev(self):
        """Previous color on BRGB lamp"""
        return self.send_command('brgb', 'color_prev')
    
    def get_last_command(self):
        """Get last command sent"""
        return {
            'command': self.last_command_sent,
            'device': self.last_device_controlled
        }
    
    def cleanup(self):
        """Cleanup GPIO"""
        try:
            if self.tx_pin:
                GPIO.cleanup([self.tx_pin])
            print("IR Remote: Cleanup complete")
        except:
            pass
