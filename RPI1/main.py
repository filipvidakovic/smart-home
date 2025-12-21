import threading
from settings.settings import load_settings
from components.ds1 import run_ds1
from components.dpir1 import run_dpir1
from components.dus1 import run_dus1
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        ds1_settings = settings['DS1']
        run_ds1(ds1_settings, threads, stop_event)
        dpir1_settings = settings['DPIR1']
        run_dpir1(dpir1_settings, threads, stop_event)
        dus1_settings = settings['DUS1']
        run_dus1(dus1_settings, threads, stop_event)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()
