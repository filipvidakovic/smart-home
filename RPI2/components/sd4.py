import threading
import time
import json
import paho.mqtt.client as mqtt


class SD4Controller:
    """Timer display controller - syncs with server via MQTT"""
    
    def __init__(self, settings, stop_event):
        self.settings = settings
        self.stop_event = stop_event
        self.lock = threading.Lock()
        
        # Timer state
        self.seconds = 0
        self.running = False
        self.expired = False
        self.blinking = False
        self.start_time = None
        
        # Blink animation
        self.blink_state = True
        self.last_blink = time.time()
        self.blink_interval = 0.5
        
        # Display throttling
        self.last_display_update = 0
        self.display_update_interval = 0.5  # Update display every 500ms
        
        # MQTT
        self.mqtt_client = None
        self.mqtt_connected = False
        
        # Initialize hardware display
        if not settings['simulated']:
            from RPI2.sensors.sd4 import SD4
            self.display = SD4(settings['clk_pin'], settings['dio_pin'])
        else:
            self.display = None
        
        print("SD4: Controller initialized")
    
    def start_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client = mqtt.Client(client_id="PI2_SD4_Controller")
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            print("SD4: MQTT started")
        except Exception as e:
            print(f"SD4: MQTT failed - {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
            client.subscribe("commands/PI2/#")
            print("SD4: Subscribed to commands/PI2/#")
    
    def on_message(self, client, userdata, msg):
        """Handle MQTT commands from server"""
        print("RECEIVER SD4: Command received - processing, message: ", msg)
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            with self.lock:
                if topic.endswith("timer_set"):
                    seconds = payload.get("seconds", 0)
                    self.seconds = seconds
                    self.running = False
                    self.expired = False
                    self.blinking = False
                    self.start_time = None
                    print(f"SD4: Timer set to {seconds}s")
                
                elif topic.endswith("timer_start"):
                    if self.seconds > 0:
                        self.running = True
                        self.start_time = time.time()
                        self.expired = False
                        self.blinking = False
                        print("SD4: Timer started")
                
                elif topic.endswith("timer_stop"):
                    self.running = False
                    self.start_time = None
                    self.blinking = False
                    print("SD4: Timer stopped")
                
                elif topic.endswith("timer_add"):
                    add_seconds = payload.get("seconds", 10)
                    
                    if self.blinking:
                        # Stop blinking
                        self.blinking = False
                        self.expired = False
                        self.seconds = 0
                        print("SD4: Blinking stopped")
                    else:
                        self.seconds += add_seconds
                        # Adjust start time if running
                        if self.running and self.start_time:
                            self.start_time -= add_seconds
                        print(f"SD4: Added {add_seconds}s, total: {self.seconds}s")
                
                elif topic.endswith("timer_expired"):
                    self.expired = True
                    self.blinking = True
                    self.running = False
                    self.seconds = 0
                    print("SD4: Timer EXPIRED - blinking")
        
        except Exception as e:
            print(f"SD4: Error processing command - {e}")
    
    def get_current_seconds(self):
        """Calculate current remaining seconds (thread-safe)"""
        with self.lock:
            if not self.running or not self.start_time:
                return self.seconds
            
            elapsed = int(time.time() - self.start_time)
            remaining = max(0, self.seconds - elapsed)
            
            # Check if expired
            if remaining == 0 and not self.expired:
                self.expired = True
                self.blinking = True
                self.running = False
                self.send_timer_expired()
                print("SD4: Timer expired locally")
            
            return remaining
    
    def send_timer_expired(self):
        """Notify server that timer expired"""
        if self.mqtt_client and self.mqtt_connected:
            self.mqtt_client.publish(
                "events/PI2/timer_expired",
                json.dumps({"timestamp": time.time()})
            )
    
    def run(self):
        """Main display loop"""
        print("SD4: Starting display loop")
        self.start_mqtt()
        
        # Wait for MQTT to connect
        time.sleep(1)
        
        last_print_time = 0
        print_interval = 2.0  # Print to console every 2 seconds
        
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # Update display
            if current_time - self.last_display_update >= self.display_update_interval:
                self.last_display_update = current_time
                
                with self.lock:
                    if self.blinking:
                        self.handle_blink()
                    else:
                        self.show_time()
                
                # Throttled console output
                if current_time - last_print_time >= print_interval:
                    with self.lock:
                        if self.blinking:
                            print("SD4: [BLINKING] 00:00")
                        else:
                            current_secs = self.get_current_seconds()
                            mins = current_secs // 60
                            secs = current_secs % 60
                            status = "▶️" if self.running else "⏸️"
                            print(f"SD4: {status} {mins:02d}:{secs:02d}")
                    
                    last_print_time = current_time
            
            time.sleep(0.1)
        
        # Cleanup
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        if self.display:
            self.display.cleanup()
        
        print("SD4: Stopped")
    
    def show_time(self):
        """Display current time on 7-segment display"""
        current_secs = self.get_current_seconds()
        minutes = current_secs // 60
        seconds = current_secs % 60
        value = minutes * 100 + seconds
        
        if self.display:
            self.display.show_number(value, colon=True)
    
    def handle_blink(self):
        """Handle blinking animation when timer expired"""
        current = time.time()
        
        if current - self.last_blink >= self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink = current
        
        if self.display:
            if self.blink_state:
                self.display.show_number(0, colon=True)
            else:
                self.display.clear()
    
    def button_pressed(self):
        """
        Called when physical button is pressed
        Send event to server to handle timer logic
        """
        print("SD4: Button pressed - sending event to server")
        if self.mqtt_client and self.mqtt_connected:
            self.mqtt_client.publish(
                "events/PI2/button_pressed",
                json.dumps({"timestamp": time.time()})
            )


def run_sd4_controller(settings, threads, stop_event):
    """Run SD4 controller in a thread"""
    controller = SD4Controller(settings, stop_event)
    
    sd4_thread = threading.Thread(
        target=controller.run,
        daemon=True
    )
    sd4_thread.start()
    threads.append(sd4_thread)
    
    print("SD4: Controller thread started")
    
    return controller  # Return so BTN can call button_pressed()