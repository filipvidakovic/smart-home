import threading
import queue
import time
import json
import paho.mqtt.client as mqtt
from typing import Dict, Any
from datetime import datetime


class MQTTPublisher:
    def __init__(self, settings: Dict[str, Any]):
        self.broker = settings['mqtt']['broker']
        self.port = settings['mqtt']['port']
        self.client_id = settings['mqtt']['client_id']
        self.topics = settings['mqtt']['topics']
        self.batch_size = settings['mqtt']['batch_size']
        self.batch_interval = settings['mqtt']['batch_interval']
        self.device_info = settings['device']
        
        self.client = None
        self.connected = False
        self.message_queue = queue.Queue()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.daemon_thread = None
        
        self.batches = {
            'temperature': [],
            'humidity': [],
            'motion': [],
            'distance': [],
            'door': [],
            'button': [],
            'accel_x': [],
            'accel_y': [],
            'accel_z': [],
            'gyro_x': [],
            'gyro_y': [],
            'gyro_z': []
        }
        self.last_send_time = {
            'temperature': time.time(),
            'humidity': time.time(),
            'motion': time.time(),
            'distance': time.time(),
            'door': time.time(),
            'button': time.time(),
            'accel_x': time.time(),
            'accel_y': time.time(),
            'accel_z': time.time(),
            'gyro_x': time.time(),
            'gyro_y': time.time(),
            'gyro_z': time.time()
        }
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✓ MQTT: Connected to {self.broker}:{self.port}")
        else:
            self.connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            print(f"✗ MQTT: Connection failed - {error_messages.get(rc, f'Unknown error {rc}')}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            print(f"✗ MQTT: Unexpected disconnection (code {rc})")

    def _on_publish(self, client, userdata, mid):
        pass
        
    def connect(self, retry_count=3, retry_delay=2):
        """Connect to MQTT broker with retry logic"""
        for attempt in range(retry_count):
            try:
                print(f"MQTT: Connection attempt {attempt + 1}/{retry_count} to {self.broker}:{self.port}")
                
                # Create new client
                self.client = mqtt.Client(client_id=self.client_id, clean_session=True)
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                self.client.on_publish = self._on_publish
                
                # Set connection timeout
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
                
                # Wait for connection
                timeout = 5
                start_time = time.time()
                while not self.connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.connected:
                    return True
                else:
                    print(f"✗ MQTT: Connection timeout on attempt {attempt + 1}")
                    self.client.loop_stop()
                    
            except Exception as e:
                print(f"✗ MQTT: Connection error on attempt {attempt + 1}: {e}")
            
            if attempt < retry_count - 1:
                print(f"MQTT: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        print("✗ MQTT: All connection attempts failed")
        return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        print("MQTT: Disconnecting...")
        self.stop_event.set()
        
        if self.daemon_thread and self.daemon_thread.is_alive():
            self.daemon_thread.join(timeout=2.0)
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        print("MQTT: Disconnected")
    
    def add_reading(self, sensor_type: str, value: Any, simulated: bool):
        """Add sensor reading to queue (thread-safe)"""
        reading = {
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': self.device_info['pi_id'],
            'device_name': self.device_info['device_name'],
            'location': self.device_info['location'],
            'sensor_type': sensor_type,
            'value': value,
            'simulated': simulated
        }
        self.message_queue.put(reading)
    
    def _process_batches(self):
        """Daemon thread that processes batches"""
        print("MQTT: Batch processing daemon started")
        
        while not self.stop_event.is_set():
            try:
                try:
                    reading = self.message_queue.get(timeout=0.5)
                except queue.Empty:
                    self._check_batch_timeouts()
                    continue
                
                sensor_type = reading['sensor_type']
                
                # FIKSOVANO: Bolji error handling
                with self.lock:
                    if sensor_type not in self.batches:
                        print(f"⚠️  MQTT: Unknown sensor type '{sensor_type}', skipping")
                        self.message_queue.task_done()
                        continue
                    
                    self.batches[sensor_type].append(reading)
                    batch_full = len(self.batches[sensor_type]) >= self.batch_size
                
                if batch_full:
                    self._send_batch(sensor_type)
                
                self.message_queue.task_done()
                
            except Exception as e:
                print(f"✗ MQTT: Error in batch processing - {e}")
                import traceback
                traceback.print_exc()
        
        self._flush_all_batches()
        print("MQTT: Batch processing daemon stopped")
    
    def _check_batch_timeouts(self):
        """Check if any batch needs to be sent due to time interval"""
        current_time = time.time()
        
        for sensor_type in list(self.batches.keys()):  # FIKSOVANO: list() za thread safety
            with self.lock:
                has_data = len(self.batches[sensor_type]) > 0
                time_elapsed = current_time - self.last_send_time[sensor_type]
            
            if has_data and time_elapsed >= self.batch_interval:
                self._send_batch(sensor_type)
    
    def _send_batch(self, sensor_type: str):
        """Send batch for specific sensor type"""
        if not self.connected:
            with self.lock:
                self.batches[sensor_type].clear()
                self.last_send_time[sensor_type] = time.time()
            return
        
        with self.lock:
            if not self.batches[sensor_type]:
                return
            batch_data = self.batches[sensor_type].copy()
            self.batches[sensor_type].clear()
            self.last_send_time[sensor_type] = time.time()
        
        topic = self.topics.get(sensor_type, f"sensors/{sensor_type}")
        payload = json.dumps({
            'batch_size': len(batch_data),
            'readings': batch_data
        })
        
        try:
            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✓ MQTT: Published {len(batch_data)} {sensor_type} readings → {topic}")
            else:
                print(f"✗ MQTT: Publish failed for {sensor_type} (rc={result.rc})")
        except Exception as e:
            print(f"✗ MQTT: Failed to publish batch - {e}")
    
    def _flush_all_batches(self):
        """Send all remaining batches"""
        if self.connected:
            print("MQTT: Flushing all remaining batches...")
            for sensor_type in list(self.batches.keys()):
                self._send_batch(sensor_type)
    
    def start_daemon(self):
        """Start the daemon thread for batch processing"""
        self.daemon_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.daemon_thread.start()