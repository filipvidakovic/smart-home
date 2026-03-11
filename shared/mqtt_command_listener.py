import paho.mqtt.client as mqtt
import json
import threading
from typing import Callable, Dict


class MQTTCommandListener:
    """Listens for commands from Flask server and executes them"""
    
    def __init__(self, broker='localhost', port=1883, device_id='PI1'):
        self.broker = broker
        self.port = port
        self.device_id = device_id
        self.client = None
        self.connected = False
        self.callbacks = {}
        
    def register_callback(self, command_type: str, callback: Callable):
        """Register callback for specific command type"""
        self.callbacks[command_type] = callback
        print(f"📝 Registered callback for: {command_type}")
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            print(f"✓ Command Listener: Connected to MQTT broker")
            
            # Subscribe only to commands for this device
            topic = f"commands/{self.device_id}/#"
            client.subscribe(topic)
            print(f"✓ Command Listener: Subscribed to {topic}")
        else:
            self.connected = False
            print(f"Command Listener: Connection failed (code {rc})")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming command messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"Command received: {topic}")
            
            # Extract command type from topic
            # Example: "commands/timer/set" -> "timer_set"
            parts = topic.split('/')
            if len(parts) >= 3:
                command_type = f"{parts[1]}_{parts[2]}"
                
                # Execute registered callback if exists
                if command_type in self.callbacks:
                    self.callbacks[command_type](payload)
                else:
                    print(f" No callback registered for: {command_type}")
            
        except Exception as e:
            print(f"✗ Error processing command: {e}")
            import traceback
            traceback.print_exc()
    
    def connect(self):
        """Connect to MQTT broker and start listening"""
        try:
            self.client = mqtt.Client(
                client_id=f"cmd_listener_{self.device_id}", 
                clean_session=False  # Keep session to avoid disconnection issues
            )
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            print(f"✓ Command Listener initialized for {self.device_id}")
            return True
        except Exception as e:
            print(f"✗ Command Listener connection failed: {e}")
            return False
    
    def on_disconnect(self, client, userdata, rc):
        """Handle unexpected disconnection"""
        if rc != 0:
            print(f"⚠️  Command Listener: Unexpected disconnection (code {rc}), attempting to reconnect...")
            # Attempt to reconnect
            try:
                client.reconnect()
            except Exception as e:
                print(f"✗ Command Listener: Reconnection failed - {e}")
    
    def disconnect(self):
        """Disconnect from MQTT"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("Command Listener: Disconnected")