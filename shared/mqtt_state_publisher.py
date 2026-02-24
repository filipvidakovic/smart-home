import paho.mqtt.client as mqtt
import json
import time
import threading


class MQTTStatePublisher:
    """Publishes system state changes to MQTT for Flask server to consume"""
    
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.client = None
        self.connected = False
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id="state_publisher", clean_session=True)
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            self.connected = True
            print("✓ State Publisher: Connected to MQTT")
            return True
        except Exception as e:
            print(f"✗ State Publisher: Connection failed - {e}")
            return False
    
    def publish_people_count(self, count):
        """Publish people count update"""
        if self.connected:
            self.client.publish("system/state/people_count", 
                              json.dumps({"count": count}))
    
    def publish_security_state(self, armed):
        """Publish security system state"""
        if self.connected:
            self.client.publish("system/state/security", 
                              json.dumps({"armed": armed}))
    
    def publish_alarm_state(self, active, reason=None):
        """Publish alarm state"""
        if self.connected:
            self.client.publish("system/state/alarm", 
                              json.dumps({"active": active, "reason": reason}))
    
    def publish_timer_state(self, seconds, running, expired, blinking):
        """Publish timer state"""
        if self.connected:
            self.client.publish("system/state/timer", 
                              json.dumps({
                                  "seconds": seconds,
                                  "running": running,
                                  "expired": expired,
                                  "blinking": blinking
                              }))
    
    def publish_door_state(self, door_id, open_state, open_since):
        """Publish door state"""
        if self.connected:
            self.client.publish("system/state/door", 
                              json.dumps({
                                  "door_id": door_id,
                                  "open": open_state,
                                  "open_since": open_since
                              }))
    
    def publish_full_state(self, state_dict):
        """Publish complete system state"""
        if self.connected:
            self.client.publish("system/state/full", json.dumps(state_dict))
    
    def disconnect(self):
        """Disconnect from MQTT"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("State Publisher: Disconnected")


# Global instance
state_publisher = MQTTStatePublisher()