from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime
import threading

app = Flask(__name__)

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "adminadmin"
INFLUXDB_ORG = "myorg"
INFLUXDB_BUCKET = "iot"

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # Subscribe to all sensor topics
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    """Process incoming MQTT messages and store in InfluxDB"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        print(f"Received message on topic '{topic}': {len(payload.get('readings', []))} readings")
        
        # Process batch of readings
        readings = payload.get('readings', [])
        points = []
        
        for reading in readings:
            # Create InfluxDB point
            point = Point(reading['sensor_type']) \
                .tag("device_id", reading['device_id']) \
                .tag("device_name", reading['device_name']) \
                .tag("location", reading['location']) \
                .tag("simulated", str(reading['simulated'])) \
                .field("value", float(reading['value'])) \
                .time(reading['timestamp'])
            
            points.append(point)
        
        # Write batch to InfluxDB
        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
            print(f"Wrote {len(points)} points to InfluxDB")
    
    except Exception as e:
        print(f"Error processing message: {e}")

def start_mqtt_client():
    """Start MQTT client in separate thread"""
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "IoT Data Server"}), 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get database statistics"""
    try:
        query_api = influx_client.query_api()
        
        # Count records per sensor type
        stats = {}
        for sensor_type in ['temperature', 'motion', 'distance']:
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "{sensor_type}")
                |> count()
            '''
            result = query_api.query(query, org=INFLUXDB_ORG)
            
            count = 0
            for table in result:
                for record in table.records:
                    count += record.get_value()
            
            stats[sensor_type] = count
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start MQTT client in background thread
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    # Start Flask server
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)