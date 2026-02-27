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
device_last_seen = {'PI1': None, 'PI2': None, 'PI3': None}
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
    },
    'PI3': {
        'temperature_bedroom': {'type': 'temperature', 'last_value': None, 'last_reading': None},
        'humidity_bedroom': {'type': 'humidity', 'last_value': None, 'last_reading': None},
        'temperature_master': {'type': 'temperature', 'last_value': None, 'last_reading': None},
        'humidity_master': {'type': 'humidity', 'last_value': None, 'last_reading': None},
        'motion': {'type': 'motion', 'last_value': None, 'last_reading': None}
    }
}

# LCD Display state - stores current LCD display data
lcd_display_state = {
    'PI3': {
        'line1': 'Smart Home LCD',
        'line2': 'DHT Sensor',
        'current_sensor': 'dht1',
        'dht1': {'temperature': None, 'humidity': None, 'location': 'Bedroom'},
        'dht2': {'temperature': None, 'humidity': None, 'location': 'Master Bedroom'},
        'last_updated': None
    },
    'PI2': {
        'line1': 'Kitchen DHT',
        'line2': 'Temperature',
        'dht3': {'temperature': None, 'humidity': None, 'location': 'Kitchen'},
        'last_updated': None
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
            print(f"📥 MQTT: {topic} → {payload.get('readings', [{}])[0].get('sensor_type', 'unknown')} reading")
            handle_sensor_data(payload)
        
        # ========== RPI EVENTS ==========
        elif topic.startswith("events/"):
            print(f"📥 MQTT: {topic}")
            handle_rpi_event(topic, payload)
            
    except Exception as e:
        print(f"❌ Error processing message: {e}")
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
        
        if sensor_type == 'motion':
            print(f"🔍 Processing motion: device={device_id}, value={value} (type: {type(value)})")
        
        # Update device tracking
        if device_id in device_last_seen:
            device_last_seen[device_id] = datetime.now().isoformat()
        
        if device_id in device_sensors and sensor_type in device_sensors[device_id]:
            device_sensors[device_id][sensor_type]['last_value'] = value
            device_sensors[device_id][sensor_type]['last_reading'] = reading.get('timestamp')
        
        # Update LCD display state for PI3 (Bedrooms)
        if device_id == 'PI3' and sensor_type == 'temperature':
            if 'dht1' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI3']['dht1']['temperature'] = value
                lcd_display_state['PI3']['last_updated'] = datetime.now().isoformat()
            elif 'dht2' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI3']['dht2']['temperature'] = value
                lcd_display_state['PI3']['last_updated'] = datetime.now().isoformat()
        elif device_id == 'PI3' and sensor_type == 'humidity':
            if 'dht1' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI3']['dht1']['humidity'] = value
                lcd_display_state['PI3']['last_updated'] = datetime.now().isoformat()
            elif 'dht2' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI3']['dht2']['humidity'] = value
                lcd_display_state['PI3']['last_updated'] = datetime.now().isoformat()
        
        # Update LCD display state for PI2 (Kitchen)
        if device_id == 'PI2' and sensor_type == 'temperature':
            if 'dht3' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI2']['dht3']['temperature'] = value
                lcd_display_state['PI2']['last_updated'] = datetime.now().isoformat()
        elif device_id == 'PI2' and sensor_type == 'humidity':
            if 'dht3' in reading.get('sensor_id', '').lower():
                lcd_display_state['PI2']['dht3']['humidity'] = value
                lcd_display_state['PI2']['last_updated'] = datetime.now().isoformat()
        
        # ===== UPDATE SERVER STATE BASED ON SENSOR TYPE =====
        
        # Distance readings for motion tracking
        if sensor_type == 'distance':
            system_state.add_distance_reading(device_id, value)
        
        # Motion detection for people counting
        elif sensor_type == 'motion' and value == 1:  # 1 = motion detected
            distance_history = system_state.distance_history.get(device_id, [])
            print(f"🔍 Motion detected on {device_id}, checking {len(distance_history)} distance readings...")
            
            # SECURITY: If building is empty (0 people), ANY motion triggers alarm
            if system_state.people_count == 0:
                system_state.trigger_alarm(f"🚨 INTRUSION DETECTED: Motion detected in empty building ({device_id})")
                print(f"🚨 ALARM: Motion detected with empty building ({device_id})")
            
            direction = system_state.detect_motion_direction(device_id)
            print(f"🔍 Motion detected on {device_id}, direction: {direction}")
            
            if direction == 'entering':
                system_state.update_people_count(+1)
                print(f"➡️  Person ENTERING via {device_id}")
            elif direction == 'exiting':
                system_state.update_people_count(-1)
                print(f"⬅️  Person EXITING via {device_id}")
            else:
                # No clear direction - wait for more distance data
                print(f"⏳ Unclear direction - accumulating distance history ({len(distance_history)} readings so far)")
        
        # Door state updates
        elif sensor_type == 'door':
            door_id = 'DS1' if device_id == 'PI1' else 'DS2'
            system_state.update_door_state(door_id, value == 1)
        
        # GSG (Gyroscope/Accelerometer) - detect dangerous movement
        elif sensor_type in ['accel_x', 'accel_y', 'accel_z'] and device_id == 'PI2':
            # Threshold: acceleration > 1.5g indicates dangerous shaking/movement
            if abs(value) > 1.5:
                system_state.trigger_alarm(f"⚠️ Saint George is in dangerous - High acceleration detected ({sensor_type}={value:.2f}g)")
                print(f"⚠️ ALARM: GSG detected dangerous movement on {device_id}: {sensor_type}={value:.2f}g")
        
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
        'PI2': {'device_name': 'Kitchen Device', 'location': 'Kitchen'},
        'PI3': {'device_name': 'Bedrooms Device', 'location': 'Bedrooms'}
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


@app.route('/lamp/control', methods=['POST'])
def control_lamp():
    """Control RGB lamp on PI3"""
    data = request.get_json()
    command = data.get('command', '')  # 'on', 'off', 'set_color'
    color = data.get('color', 'white')  # Color name
    
    if command not in ['on', 'off', 'set_color']:
        return jsonify({"error": "Invalid command. Use 'on', 'off', or 'set_color'"}), 400
    
    # Send command to PI3
    payload = {
        'command': command,
        'color': color
    }
    send_command("PI3", "lamp_control", payload)
    
    return jsonify({
        "success": True, 
        "message": f"Lamp command '{command}' sent",
        "color": color if command in ['on', 'set_color'] else None
    }), 200


@app.route('/ir/control', methods=['POST'])
def control_ir():
    """Send IR command from PI3 IR remote to BRGB lamp"""
    data = request.get_json()
    command = data.get('command', '')  # 'power', 'color_next', 'color_prev'
    device = data.get('device', 'brgb')  # Only BRGB supported
    
    if device != 'brgb':
        return jsonify({"error": "Only BRGB device is supported"}), 400
    
    # Map 'power' to 'power_toggle' for internal processing
    if command == 'power':
        command = 'power_toggle'
    
    valid_commands = ['power_toggle', 'color_next', 'color_prev']
    if command not in valid_commands:
        return jsonify({"error": f"Invalid command. Use one of: power, color_next, color_prev"}), 400
    
    # Send IR command to PI3 for BRGB control
    payload = {
        'command': command,
        'device': device
    }
    send_command("PI3", "ir_command", payload)
    
    return jsonify({
        "success": True,
        "message": f"IR command '{command}' sent to {device}",
        "device": device
    }), 200


@app.route('/ir/devices', methods=['GET'])
def get_ir_devices():
    """Get available IR devices and their supported commands"""
    devices = {
        'brgb': {
            'name': 'RGB Lamp',
            'emoji': '💡',
            'commands': ['power', 'color_next', 'color_prev']
        }
    }
    
    return jsonify({
        "devices": devices,
        "message": "Available IR-controlled device: BRGB lamp"
    }), 200


@app.route('/lcd/display', methods=['GET'])
def get_lcd_display():
    """Get LCD display data from PI3 (Bedrooms) and PI2 (Kitchen)"""
    pi3_lcd = lcd_display_state.get('PI3', {})
    pi2_lcd = lcd_display_state.get('PI2', {})
    return jsonify({
        'PI3': {
            'device_id': 'PI3',
            'location': 'Bedrooms',
            'dht1': pi3_lcd.get('dht1', {}),
            'dht2': pi3_lcd.get('dht2', {}),
            'last_updated': pi3_lcd.get('last_updated')
        },
        'PI2': {
            'device_id': 'PI2',
            'location': 'Kitchen',
            'dht3': pi2_lcd.get('dht3', {}),
            'last_updated': pi2_lcd.get('last_updated')
        }
    }), 200


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
    
    # Clear the alarm
    system_state.clear_alarm()
    system_state.disarm_security()
    send_command("all", "alarm_cleared", {})
    
    return jsonify({"success": True, "message": "Alarm deactivated"}), 200


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


@app.route('/timer/button-seconds', methods=['GET'])
def get_timer_button_seconds():
    """Get configured seconds to add on button press"""
    return jsonify({"seconds": system_state.timer_button_add_seconds}), 200


@app.route('/timer/button-seconds', methods=['POST'])
def set_timer_button_seconds():
    """Set configured seconds to add on button press"""
    data = request.get_json()
    try:
        seconds = int(data.get('seconds', 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Seconds must be an integer"}), 400
    if seconds < 1:
        return jsonify({"error": "Seconds must be >= 1"}), 400
    system_state.timer_button_add_seconds = seconds
    return jsonify({"success": True, "seconds": system_state.timer_button_add_seconds}), 200


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