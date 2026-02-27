import threading


def create_ir_remote(settings, brgb_lamp=None):
    """Factory function to create IR remote instance
    
    Args:
        settings: IR configuration
        brgb_lamp: Optional reference to BRGB lamp for IR control
    """
    if settings.get('simulated', False):
        from RPI3.simulators.ir import SimulatedIRRemote
        print("Using simulated IR remote")
        return SimulatedIRRemote(brgb_lamp=brgb_lamp)
    else:
        from RPI3.sensors.ir import IRRemote
        print("Using real IR remote")
        return IRRemote(
            tx_pin=settings.get('tx_pin', None),
            rx_pin=settings.get('rx_pin', None)
        )


def run_ir(settings, command_listener=None, brgb_lamp=None, threads=None, stop_event=None):
    """Initialize IR remote and register command callback
    
    Args:
        settings: IR configuration
        command_listener: MQTT command listener
        brgb_lamp: Optional reference to BRGB lamp for IR control
        threads: List to append IR thread to
        stop_event: Threading event to stop simulator loops
    """
    
    # Enable auto-demo for simulated mode
    auto_demo = settings.get('simulated', False) and settings.get('auto_demo', True)
    
    if settings.get('simulated', False):
        from RPI3.simulators.ir import SimulatedIRRemote
        print("Using simulated IR remote")
        ir_remote = SimulatedIRRemote(brgb_lamp=brgb_lamp, auto_demo=auto_demo)
    else:
        from RPI3.sensors.ir import IRRemote
        print("Using real IR remote")
        ir_remote = IRRemote(
            tx_pin=settings.get('tx_pin', None),
            rx_pin=settings.get('rx_pin', None)
        )
    
    def handle_ir_command(payload):
        """Handle IR control commands"""
        try:
            command = payload.get('command', '')
            device = payload.get('device', '')
            
            if command == 'send':
                ir_cmd = payload.get('ir_command', '')
                ir_remote.send_command(device, ir_cmd)
            elif command == 'power_toggle':
                ir_remote.send_power_toggle(device)
            elif command == 'color_next':
                ir_remote.send_color_next()
            elif command == 'color_prev':
                ir_remote.send_color_prev()
            else:
                print(f"⚠️  IR Remote: Unknown command '{command}'")
        
        except Exception as e:
            print(f"✗ IR Remote: Error handling command: {e}")
            import traceback
            traceback.print_exc()
    
    # Register command callback if command listener exists
    if command_listener:
        command_listener.register_callback('ir_command', handle_ir_command)
        print("✓ IR Remote: Registered command callback")
    
    # Start auto-demo thread if enabled
    if auto_demo and threads is not None and stop_event is not None:
        from RPI3.simulators.ir import run_ir_simulator
        ir_thread = threading.Thread(
            target=run_ir_simulator,
            args=(ir_remote, 1, stop_event),
            daemon=True
        )
        ir_thread.start()
        threads.append(ir_thread)
        print("✓ IR Remote: Auto-demo thread started")
    
    return ir_remote
