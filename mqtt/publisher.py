import threading
import queue
import time
import json
import paho.mqtt.client as mqtt
from typing import Dict, Any, List
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
        
        self.client = mqtt.Client(client_id=self.client_id)
        self.message_queue = queue.Queue()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.daemon_thread = None
        
        # Batch storage per sensor type
        self.batches = {
            'temperature': [],
            'motion': [],
            'distance': []
        }
        self.last_send_time = {
            'temperature': time.time(),
            'motion': time.time(),
            'distance': time.time()
        }
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            print(f"Connected to MQTT broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.stop_event.set()
        if self.daemon_thread:
            self.daemon_thread.join()
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")
    
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
        while not self.stop_event.is_set():
            try:
                # Non-blocking get with timeout
                try:
                    reading = self.message_queue.get(timeout=0.5)
                except queue.Empty:
                    # Check if any batch needs to be sent due to timeout
                    self._check_batch_timeouts()
                    continue
                
                sensor_type = reading['sensor_type']
                
                # Critical section - minimize lock time
                with self.lock:
                    self.batches[sensor_type].append(reading)
                    batch_full = len(self.batches[sensor_type]) >= self.batch_size
                
                # Send batch if full (outside of lock)
                if batch_full:
                    self._send_batch(sensor_type)
                
                self.message_queue.task_done()
                
            except Exception as e:
                print(f"Error in batch processing: {e}")
        
        # Send remaining batches before stopping
        self._flush_all_batches()
    
    def _check_batch_timeouts(self):
        """Check if any batch needs to be sent due to time interval"""
        current_time = time.time()
        
        for sensor_type in self.batches.keys():
            with self.lock:
                has_data = len(self.batches[sensor_type]) > 0
                time_elapsed = current_time - self.last_send_time[sensor_type]
            
            if has_data and time_elapsed >= self.batch_interval:
                self._send_batch(sensor_type)
    
    def _send_batch(self, sensor_type: str):
        """Send batch for specific sensor type"""
        # Get batch data with minimal lock time
        with self.lock:
            if not self.batches[sensor_type]:
                return
            batch_data = self.batches[sensor_type].copy()
            self.batches[sensor_type].clear()
            self.last_send_time[sensor_type] = time.time()
        
        # Publish outside of lock
        topic = self.topics.get(sensor_type, f"sensors/{sensor_type}")
        payload = json.dumps({
            'batch_size': len(batch_data),
            'readings': batch_data
        })
        
        try:
            self.client.publish(topic, payload, qos=1)
            print(f"Published batch of {len(batch_data)} {sensor_type} readings to {topic}")
        except Exception as e:
            print(f"Failed to publish batch: {e}")
    
    def _flush_all_batches(self):
        """Send all remaining batches"""
        for sensor_type in self.batches.keys():
            self._send_batch(sensor_type)
    
    def start_daemon(self):
        """Start the daemon thread for batch processing"""
        self.daemon_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.daemon_thread.start()
        print("MQTT batch processing daemon started")