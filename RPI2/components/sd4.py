import threading
import time
import json
import paho.mqtt.client as mqtt


class SD4Controller:
    def __init__(self, settings, stop_event):
        self.settings = settings
        self.stop_event = stop_event

        self.seconds = 0
        self.running = False
        self.blinking = False

        self.blink_state = True
        self.last_blink = time.time()
        self.blink_interval = 0.5

        self.mqtt_client = None

        if not settings['simulated']:
            from RPI2.sensors.sd4 import SD4
            self.display = SD4(settings['clk_pin'], settings['dio_pin'])
        else:
            self.display = None

    def start_mqtt(self):
        self.mqtt_client = mqtt.Client(client_id="PI2_SD4")
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.subscribe("commands/PI2/#")
        self.mqtt_client.loop_start()

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic.endswith("timer_set"):
            self.seconds = payload.get("seconds", 0)
            self.blinking = False

        elif topic.endswith("timer_start"):
            self.running = True

        elif topic.endswith("timer_stop"):
            self.running = False
            self.blinking = False

        elif topic.endswith("timer_add"):
            self.seconds += payload.get("seconds", 0)

        elif topic.endswith("timer_expired"):
            self.blinking = True
            self.running = False
            self.seconds = 0

    def run(self):
        print("SD4: Running MQTT-controlled display")
        self.start_mqtt()

        while not self.stop_event.is_set():

            if self.blinking:
                self.handle_blink()
            else:
                self.show_time()

            time.sleep(0.1)

        if self.display:
            self.display.cleanup()

    def show_time(self):
        minutes = self.seconds // 60
        seconds = self.seconds % 60
        value = minutes * 100 + seconds

        if self.display:
            self.display.show_number(value, colon=True)
        else:
            print(f"SD4 Display: {minutes:02d}:{seconds:02d}")

    def handle_blink(self):
        current = time.time()

        if current - self.last_blink >= self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink = current

        if self.blink_state:
            if self.display:
                self.display.show_number(0, colon=True)
            else:
                print("SD4 Display: 00:00 (BLINK)")
        else:
            if self.display:
                self.display.clear()
            else:
                print("SD4 Display: [OFF]")


    def button_pressed(self):
        """
        Called when physical BTN pressed.
        Only send event to server.
        """
        if self.mqtt_client:
            self.mqtt_client.publish(
                "events/PI2/button_pressed",
                json.dumps({})
            )