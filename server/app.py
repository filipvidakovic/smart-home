from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime
import threading
import os
import time

app = Flask(__name__)

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'adminadmin')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'myorg')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'iot')

# MQTT Configuration  
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))

# Global variables
influx_client = None
write_api = None
mqtt_connected = False

def init_influxdb(retry_count=5, retry_delay=2):
    """Initialize InfluxDB client with retry logic"""
    global influx_client, write_api
    
    for attempt in range(retry_count):
        try:
            print(f"InfluxDB: Connection attempt {attempt + 1}/{retry_count} to {INFLUXDB_URL}")
            influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
            write_api = influx_client.write_api(write_options=SYNCHRONOUS)
            
            # Test connection
            influx_client.ping()
            print(f"✓ Connected to InfluxDB at {INFLUXDB_URL}")
            return True
        except Exception as e:
            print(f"✗ InfluxDB connection attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print("✗ Failed to connect to InfluxDB after all attempts")
    return False

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    
    if rc == 0:
        mqtt_connected = True
        print(f"✓ MQTT: Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to all sensor topics
        client.subscribe("sensors/#")
        print("✓ MQTT: Subscribed to sensors/#")
    else:
        mqtt_connected = False
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        print(f"✗ MQTT: Connection failed - {error_messages.get(rc, f'Unknown error {rc}')}")

def on_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    global mqtt_connected
    mqtt_connected = False
    
    if rc != 0:
        print(f"✗ MQTT: Unexpected disconnection (code {rc})")
    else:
        print("MQTT: Disconnected")

def on_message(client, userdata, msg):
    """Process incoming MQTT messages and store in InfluxDB"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        batch_size = payload.get('batch_size', 0)
        print(f"📥 MQTT: Received on '{topic}': {batch_size} readings")
        
        if not write_api:
            print("⚠️  InfluxDB not available, skipping write")
            return
        
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
            print(f"✓ InfluxDB: Wrote {len(points)} {readings[0]['sensor_type']} points")
    
    except json.JSONDecodeError as e:
        print(f"✗ JSON decode error: {e}")
    except KeyError as e:
        print(f"✗ Missing key in message: {e}")
    except Exception as e:
        print(f"✗ Error processing message: {e}")
        import traceback
        traceback.print_exc()

def start_mqtt_client():
    """Start MQTT client with retry logic"""
    retry_count = 10
    retry_delay = 3
    
    mqtt_client = mqtt.Client(client_id="flask_iot_server", clean_session=True)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    
    for attempt in range(retry_count):
        try:
            print(f"MQTT: Connection attempt {attempt + 1}/{retry_count} to {MQTT_BROKER}:{MQTT_PORT}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"✓ MQTT: Connected successfully")
            mqtt_client.loop_forever()
            break  # If loop_forever exits, break the retry loop
            
        except ConnectionRefusedError:
            print(f"✗ MQTT: Connection refused (broker not ready yet)")
            if attempt < retry_count - 1:
                print(f"MQTT: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("✗ MQTT: All connection attempts failed")
        except Exception as e:
            print(f"✗ MQTT: Connection error: {e}")
            if attempt < retry_count - 1:
                print(f"MQTT: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("✗ MQTT: All connection attempts failed")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "service": "IoT Data Server",
        "influxdb": "connected" if influx_client else "disconnected",
        "mqtt": "connected" if mqtt_connected else "disconnected"
    }
    return jsonify(status), 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get database statistics"""
    if not influx_client:
        return jsonify({"error": "InfluxDB not available"}), 503
    
    try:
        query_api = influx_client.query_api()
        
        # Count records per sensor type
        stats = {}
        for sensor_type in ['temperature', 'motion', 'distance', 'door']:
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

@app.route('/recent/<sensor_type>', methods=['GET'])
def recent_readings(sensor_type):
    """Get recent readings for a specific sensor type"""
    if not influx_client:
        return jsonify({"error": "InfluxDB not available"}), 503
    
    try:
        query_api = influx_client.query_api()
        
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r["_measurement"] == "{sensor_type}")
            |> filter(fn: (r) => r["_field"] == "value")
            |> limit(n: 100)
        '''
        
        result = query_api.query(query, org=INFLUXDB_ORG)
        
        readings = []
        for table in result:
            for record in table.records:
                readings.append({
                    'time': record.get_time().isoformat(),
                    'value': record.get_value(),
                    'device_id': record.values.get('device_id'),
                    'device_name': record.values.get('device_name'),
                    'location': record.values.get('location'),
                    'simulated': record.values.get('simulated')
                })
        
        return jsonify({
            'sensor_type': sensor_type,
            'count': len(readings),
            'readings': readings
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Starting IoT Flask Server")
    print("=" * 60)
    
    # Initialize InfluxDB
    print("\nInitializing InfluxDB connection...")
    init_influxdb()
    
    # Start MQTT client in background thread
    print("\nStarting MQTT client...")
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    # Give MQTT client time to connect
    time.sleep(2)
    
    # Start Flask server
    print("\n" + "=" * 60)
    print("Flask server starting on port 5000...")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)