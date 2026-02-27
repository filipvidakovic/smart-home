import random
import time


class SimulatedIRRemote:
    """Simulated IR Remote - sends and receives IR signals"""
    
    DEVICES = {
        'brgb': 'BRGB Lamp',
    }
    
    COMMANDS = {
        'power': 'POWER',
        'on': 'ON',
        'off': 'OFF',
        'color_next': 'COLOR_NEXT',
        'color_prev': 'COLOR_PREV',
    }
    
    DEVICE_EMOJIS = {
        'brgb': '💡',
    }
    
    COLOR_SPECTRUM = [
        'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'white', 'orange', 'purple', 'pink'
    ]
    
    def __init__(self, brgb_lamp=None, auto_demo=False):
        """Initialize simulated IR remote
        
        Args:
            brgb_lamp: Optional reference to BRGB lamp for direct control
            auto_demo: If True, automatically send commands in timesteps
        """
        self.last_command_sent = None
        self.last_device_controlled = None
        self.device_states = {device: False for device in self.DEVICES.keys()}
        self.brgb_lamp = brgb_lamp
        self.brgb_color_index = 0
        self.auto_demo = auto_demo
        self.demo_step = 0
        self.last_demo_time = time.time()
        print("🔴 Simulated IR Remote initialized")
        if brgb_lamp:
            print("🔴 IR Remote: BRGB lamp connected for direct control")
        if auto_demo:
            print("🔴 IR Remote: Auto-demo mode enabled - will send commands every 5s")
    
    def send_command(self, device, command):
        """Send IR command to a device
        
        Args:
            device: Target device (e.g., 'tv', 'ac', 'brgb')
            command: Command to send (e.g., 'power', 'volume_up', 'color_next')
        
        Returns:
            bool: True if command sent successfully
        """
        device = device.lower()
        command = command.lower()
        
        if device not in self.DEVICES:
            print(f"🔴 IR Remote: Unknown device '{device}'")
            return False
        
        if command not in self.COMMANDS:
            print(f"🔴 IR Remote: Unknown command '{command}'")
            return False
        
        # Only BRGB lamp is supported
        if device == 'brgb' and self.brgb_lamp:
            return self._control_brgb(command)
        else:
            print(f"🔴 IR Remote: Only BRGB device is supported")
            return False
    
    def run_auto_demo(self):
        """Run automatic demo - send commands to BRGB in timesteps"""
        if not self.auto_demo or not self.brgb_lamp:
            return
        
        current_time = time.time()
        if current_time - self.last_demo_time < 5:  # 5 second intervals
            return
        
        self.last_demo_time = current_time
        self.demo_step += 1
        
        print(f"\n⏱️  IR Auto-Demo Step {self.demo_step}:")
        
        # Demo sequence
        if self.demo_step == 1:
            print("   → Turning ON BRGB")
            self.send_command('brgb', 'power')
        elif self.demo_step == 2:
            print("   → Changing to next color")
            self.send_command('brgb', 'color_next')
        elif self.demo_step == 3:
            print("   → Changing to next color")
            self.send_command('brgb', 'color_next')
        elif self.demo_step == 4:
            print("   → Going to previous color")
            self.send_command('brgb', 'color_prev')
        elif self.demo_step == 5:
            print("   → Turning OFF BRGB")
            self.send_command('brgb', 'power')
        elif self.demo_step == 6:
            print("   → Turning ON BRGB")
            self.send_command('brgb', 'power')
        elif self.demo_step >= 7:
            # Continue cycling colors
            print("   → Cycling colors")
            self.send_command('brgb', 'color_next')
            if self.demo_step >= 12:
                self.demo_step = 5  # Reset to loop
    
    def _control_brgb(self, command):
        """Control BRGB lamp via IR
        
        Available commands:
        - power: Toggle on/off
        - color_next: Next color (only if on)
        - color_prev: Previous color (only if on)
        """
        if command == 'power':
            # Toggle BRGB power
            if self.device_states['brgb']:
                self.brgb_lamp.off()
                self.device_states['brgb'] = False
                print(f"🔴 IR Remote: 💡 BRGB Lamp OFF (via IR)")
            else:
                current_color = self.COLOR_SPECTRUM[self.brgb_color_index]
                self.brgb_lamp.on(current_color)
                self.device_states['brgb'] = True
                print(f"🔴 IR Remote: 💡 BRGB Lamp ON - {current_color.upper()} (via IR)")
        
        elif command == 'color_next':
            # Change to next color (only if on)
            if self.device_states['brgb']:
                self.brgb_color_index = (self.brgb_color_index + 1) % len(self.COLOR_SPECTRUM)
                next_color = self.COLOR_SPECTRUM[self.brgb_color_index]
                self.brgb_lamp.set_color(next_color)
                print(f"🔴 IR Remote: 💡 BRGB Color → {next_color.upper()} (via IR)")
            else:
                print(f"🔴 IR Remote: 💡 BRGB is OFF - turn on first")
                return False
        
        elif command == 'color_prev':
            # Change to previous color (only if on)
            if self.device_states['brgb']:
                self.brgb_color_index = (self.brgb_color_index - 1) % len(self.COLOR_SPECTRUM)
                prev_color = self.COLOR_SPECTRUM[self.brgb_color_index]
                self.brgb_lamp.set_color(prev_color)
                print(f"🔴 IR Remote: 💡 BRGB Color ← {prev_color.upper()} (via IR)")
            else:
                print(f"🔴 IR Remote: 💡 BRGB is OFF - turn on first")
                return False
        
        self.last_command_sent = command
        self.last_device_controlled = 'brgb'
        return True
    
    def send_power_toggle(self, device):
        """Toggle power on a device"""
        return self.send_command(device, 'power')
    
    def send_color_next(self):
        """Next color on BRGB lamp"""
        return self.send_command('brgb', 'color_next')
    
    def send_color_prev(self):
        """Previous color on BRGB lamp"""
        return self.send_command('brgb', 'color_prev')
    
    def get_device_state(self, device):
        """Get device power state"""
        device = device.lower()
        return self.device_states.get(device, False)
    
    def get_all_states(self):
        """Get all device states"""
        return self.device_states.copy()
    
    def get_brgb_current_color(self):
        """Get current BRGB color"""
        if self.device_states['brgb']:
            return self.COLOR_SPECTRUM[self.brgb_color_index]
        return 'off'
    
    def get_last_command(self):
        """Get last command sent"""
        return {
            'command': self.last_command_sent,
            'device': self.last_device_controlled
        }
    
    def cleanup(self):
        """Cleanup"""
        print("🔴 IR Remote: Cleanup complete")


def run_ir_simulator(ir_remote, interval=5, stop_event=None):
    """Run IR simulator with auto-demo in loop
    
    Args:
        ir_remote: SimulatedIRRemote instance
        interval: Check interval in seconds
        stop_event: Threading event to stop the loop
    """
    print(f"🔴 IR Simulator: Starting auto-demo loop (interval={interval}s)")
    
    while not (stop_event and stop_event.is_set()):
        try:
            ir_remote.run_auto_demo()
            time.sleep(1)  # Check every second
        except Exception as e:
            print(f"✗ IR Simulator: Error in auto-demo: {e}")
            break
    
    print("🔴 IR Simulator: Auto-demo loop stopped")
