import RPi.GPIO as GPIO
import time

class DMS(object):
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.keypad_map = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['*', '0', '#']
        ]
        # Postavljanje pinova
        for r in self.rows:
            GPIO.setup(r, GPIO.OUT)
            GPIO.output(r, GPIO.LOW)
        for c in self.cols:
            GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def get_key(self):
        for i, row_pin in enumerate(self.rows):
            GPIO.output(row_pin, GPIO.HIGH)
            for j, col_pin in enumerate(self.cols):
                if GPIO.input(col_pin) == GPIO.HIGH:
                    while GPIO.input(col_pin) == GPIO.HIGH: # Debounce
                        time.sleep(0.05)
                    GPIO.output(row_pin, GPIO.LOW)
                    return self.keypad_map[i][j]
            GPIO.output(row_pin, GPIO.LOW)
        return None

def run_dms_loop(dms, callback, stop_event):
    while not stop_event.is_set():
        key = dms.get_key()
        if key:
            callback(key)
        time.sleep(0.1)