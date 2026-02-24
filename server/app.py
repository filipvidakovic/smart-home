from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime
import threading
import os
import time
from flask_cors import CORS
from state_manager import system_state

app = Flask(__name__)
CORS(app)

# Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'adminadmin')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'myorg')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'iot')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
SECURITY_PIN = os.getenv('SECURITY_PIN', '1234')

# Global MQTT clients
influx_client = None
write_api = None
data_mqtt_client = None  # Receives sensor data
command_mqtt_client = None  # Sends commands to RPIs
mqtt_connected = False

# Device tracking
device_last_seen = {'PI1': None, 'PI2': None}
device_sensors = {
    'PI1': {
        'door': {'type': 'door', 'last_value': None, 'last_reading': None},
        'motion': {'type': 'motion', 'last_value': None, 'last_reading': None},
        'distance': {'type': 'distance', 'last_value': None, 'last_reading': None}
    },
    'PI2': {
        'door': {'type': 'door', 'last_value': None, 'last_reading': None},
        'motion': {'type': 'motion', 'last_value': None, 'last_reading': None},
        'distance': {'type': 'distance', 'last_value': None, 'last_reading': None},
        'temperature': {'type': 'temperature', 'last_value': None, 'last_reading': None},
        'humidity': {'type': 'humidity', 'last_value': None, 'last_reading': None},
        'button': {'type': 'button', 'last_value': None, 'last_reading': None}
    }
}


def init_influxdb():
    """Initialize InfluxDB"""
    global influx_client, write_api
    try:
        influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        influx_client.ping()
        print(" InfluxDB connected")
        return True
    except Exception as e:
        print(f" InfluxDB failed: {e}")
        return False


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(" MQTT connected")
        
        # Subscribe to sensor data
        client.subscribe("sensors/#")
        
        # Subscribe to RPI events (motion detected, door opened, etc.)
        client.subscribe("events/#")
        
        print(" Subscribed to topics")
    else:
        print(f" MQTT failed: {rc}")


def on_message(client, userdata, msg):
    """Process MQTT messages and update SERVER state"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        # ========== SENSOR DATA ==========
        if topic.startswith("sensors/"):
            handle_sensor_data(payload)
        
        # ========== RPI EVENTS ==========
        elif topic.startswith("events/"):
            handle_rpi_event(topic, payload)
            
    except Exception as e:
        print(f" Error processing message: {e}")
        import traceback
        traceback.print_exc()


def handle_sensor_data(payload):
    """Handle sensor data batch"""
    if not write_api:
        return
    
    readings = payload.get('readings', [])
    points = []
    
    for reading in readings:
        device_id = reading.get('device_id')
        sensor_type = reading.get('sensor_type')
        value = reading.get('value')
        
        # Update device tracking
        if device_id in device_last_seen:
            device_last_seen[device_id] = datetime.now().isoformat()
        
        if device_id in device_sensors and sensor_type in device_sensors[device_id]:
            device_sensors[device_id][sensor_type]['last_value'] = value
            device_sensors[device_id][sensor_type]['last_reading'] = reading.get('timestamp')
        
        # ===== UPDATE SERVER STATE BASED ON SENSOR TYPE =====
        
        # Distance readings for motion tracking
        if sensor_type == 'distance':
            system_state.add_distance_reading(device_id, value)
        
        # Door state updates
        elif sensor_type == 'door':
            door_id = 'DS1' if device_id == 'PI1' else 'DS2'
            system_state.update_door_state(door_id, value == 1)
        
        # Create InfluxDB point
        point = Point(sensor_type) \
            .tag("device_id", device_id) \
            .tag("device_name", reading['device_name']) \
            .tag("location", reading['location']) \
            .tag("simulated", str(reading['simulated'])) \
            .field("value", float(value)) \
            .time(reading['timestamp'])
        
        points.append(point)
    
    if points:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)


def handle_rpi_event(topic, payload):
    """Handle RPI events that affect system state"""
    
    # events/PI1/motion_detected
    if 'motion_detected' in topic:
        device_id = topic.split('/')[1]
        direction = system_state.detect_motion_direction(device_id)
        
        if direction == 'entering':
            system_state.update_people_count(+1)
            print(f"➡️  Person ENTERING via {device_id}")
        elif direction == 'exiting':
            system_state.update_people_count(-1)
            print(f"⬅️  Person EXITING via {device_id}")
        
        # Check for alarm condition (motion with 0 people)
        if system_state.people_count == 0:
            system_state.trigger_alarm(f"Motion detected with empty building ({device_id})")
    
    # events/PI2/button_pressed
    elif 'button_pressed' in topic:
        seconds = system_state.timer_button_add_seconds
        system_state.add_timer_seconds(seconds)
        send_command("PI2", "timer_add", {"seconds": seconds})
    
    # events/PI2/gyro_movement
    elif 'gyro_movement' in topic:
        system_state.trigger_alarm("Significant gyroscope movement (Icon disturbed)")


def start_data_mqtt_client():
    """Start MQTT client for receiving data"""
    global data_mqtt_client
    
    data_mqtt_client = mqtt.Client(client_id="flask_data_client", clean_session=True)
    data_mqtt_client.on_connect = on_connect
    data_mqtt_client.on_message = on_message
    
    try:
        data_mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        data_mqtt_client.loop_forever()
    except Exception as e:
        print(f" MQTT error: {e}")


def init_command_mqtt_client():
    """Initialize MQTT client for sending commands"""
    global command_mqtt_client
    try:
        command_mqtt_client = mqtt.Client(client_id="flask_command_client")
        command_mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        command_mqtt_client.loop_start()
        print("Command MQTT ready")
        return True
    except Exception as e:
        print(f"Command MQTT failed: {e}")
        return False


def send_command(device_id, command, data=None):
    """Send command to RPI device"""
    if command_mqtt_client:
        topic = f"commands/{device_id}/{command}"
        payload = json.dumps(data or {})
        command_mqtt_client.publish(topic, payload, qos=1)
        print(f"📤 Command sent: {topic}")
        return True
    return False


# ==================== STATE MONITORING ====================

def monitor_system_state():
    """Background thread to monitor state and trigger alarms"""
    print("State monitor started")
    
    while True:
        try:
            # Check for door open too long
            door_id, duration = system_state.check_door_alarms()
            if door_id:
                system_state.trigger_alarm(f"{door_id} open for {duration:.0f}s (unlocked)")
            
            if system_state.timer_expired:
                send_command("PI2", "timer_expired", {})

            # Update timer
            system_state.get_timer_remaining()
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in monitor: {e}")
            time.sleep(5)


# ==================== API ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "influxdb": "connected" if influx_client else "disconnected",
        "mqtt": "connected" if mqtt_connected else "disconnected"
    }), 200


@app.route('/system/state', methods=['GET'])
def get_system_state():
    """Get complete system state"""
    return jsonify(system_state.get_full_state()), 200


@app.route('/devices', methods=['GET'])
def get_all_devices():
    """Get all devices"""
    devices = []
    device_info = {
        'PI1': {'device_name': 'Entrance Device', 'location': 'Main Door'},
        'PI2': {'device_name': 'Kitchen Device', 'location': 'Kitchen'}
    }
    
    for device_id, info in device_info.items():
        last_seen = device_last_seen.get(device_id)
        online = False
        
        if last_seen:
            diff = (datetime.now() - datetime.fromisoformat(last_seen)).total_seconds()
            online = diff < 30
        
        devices.append({
            'device_id': device_id,
            'device_name': info['device_name'],
            'location': info['location'],
            'online': online,
            'last_seen': last_seen or 'Never',
            'sensors': device_sensors.get(device_id, {})
        })
    
    return jsonify(devices), 200


@app.route('/security/arm', methods=['POST'])
def arm_security():
    """Arm security system"""
    data = request.get_json()
    pin = data.get('pin', '')
    
    if pin != SECURITY_PIN:
        return jsonify({"error": "Incorrect PIN"}), 401
    
    success = system_state.arm_security()
    if success:
        # Notify all RPIs
        send_command("all", "security_armed", {})
        return jsonify({"success": True, "message": "Arming in 10 seconds"}), 200
    else:
        return jsonify({"error": "Already arming"}), 400


@app.route('/security/disarm', methods=['POST'])
def disarm_security():
    """Disarm security system"""
    data = request.get_json()
    pin = data.get('pin', '')
    
    if pin != SECURITY_PIN:
        return jsonify({"error": "Incorrect PIN"}), 401
    
    system_state.disarm_security()
    send_command("all", "security_disarmed", {})
    
    return jsonify({"success": True}), 200


@app.route('/alarm/clear', methods=['POST'])
def clear_alarm():
    """Clear alarm"""
    data = request.get_json()
    pin = data.get('pin', '')
    
    if pin != SECURITY_PIN:
        return jsonify({"error": "Incorrect PIN"}), 401
    
    system_state.disarm_security()
    send_command("all", "alarm_cleared", {})
    
    return jsonify({"success": True}), 200


@app.route('/timer/set', methods=['POST'])
def set_timer():
    """Set timer"""
    data = request.get_json()
    seconds = data.get('seconds', 0)
    
    system_state.set_timer(seconds)
    send_command("PI2", "timer_set", {"seconds": seconds})
    
    return jsonify({"success": True}), 200


@app.route('/timer/start', methods=['POST'])
def start_timer():
    """Start timer"""
    system_state.start_timer()
    send_command("PI2", "timer_start", {})
    return jsonify({"success": True}), 200


@app.route('/timer/stop', methods=['POST'])
def stop_timer():
    """Stop timer"""
    system_state.stop_timer()
    send_command("PI2", "timer_stop", {})
    return jsonify({"success": True}), 200


@app.route('/timer/add', methods=['POST'])
def add_timer_seconds():
    """Add seconds to timer"""
    data = request.get_json()
    seconds = data.get('seconds', 10)
    
    system_state.add_timer_seconds(seconds)
    send_command("PI2", "timer_add", {"seconds": seconds})
    
    return jsonify({"success": True}), 200


@app.route('/stats', methods=['GET'])
def stats():
    """Get statistics"""
    if not influx_client:
        return jsonify({"error": "InfluxDB not available"}), 503
    
    try:
        query_api = influx_client.query_api()
        stats = {}
        
        for sensor_type in ['temperature', 'humidity', 'motion', 'distance', 'door', 'button']:
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
            
            if count > 0:
                stats[sensor_type] = count
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("="*60)
    print("🏠 IoT Flask Server with Centralized State")
    print("="*60)
    
    # Initialize InfluxDB
    init_influxdb()
    
    # Initialize command MQTT client
    init_command_mqtt_client()
    
    # Start data MQTT client in background
    mqtt_thread = threading.Thread(target=start_data_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    # Start state monitor
    monitor_thread = threading.Thread(target=monitor_system_state, daemon=True)
    monitor_thread.start()
    
    time.sleep(2)
    
    print("\n🚀 Server starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)