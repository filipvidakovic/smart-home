import time
import random

def run_dms_simulator(delay, callback, stop_event):
    buttons = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']
    while not stop_event.is_set():
        time.sleep(delay)  # Simuliran razmak između pritisaka tastera
        pressed_key = random.choice(buttons)
        callback(pressed_key)