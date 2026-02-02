import time
import random

def run_dms_simulator(delay, callback, stop_event):
    print("DMS Simulator: Starting keypad event generation")
    buttons = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']
    while not stop_event.is_set():
        time.sleep(delay)
        pressed_key = random.choice(buttons)
        timestamp = time.time()
        callback(pressed_key, timestamp)