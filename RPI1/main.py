import threading

from components.dms import run_dms_console
from sensors.db import Buzzer
from settings.settings import load_settings
from components.ds1 import run_ds1
from components.dpir1 import run_dpir1
from components.dus1 import run_dus1
from components.dl import create_led_bulb
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
        led_bulb = None
        if 'DL1' in settings:
            led_bulb = create_led_bulb(settings['DL1'])
        led_bulb.on()
        led_bulb.off()
        ds1_settings = settings['DS1']
        run_ds1(ds1_settings, threads, stop_event)
        dpir1_settings = settings['DPIR1']
        run_dpir1(dpir1_settings, threads, stop_event)
        dus1_settings = settings['DUS1']
        run_dus1(dus1_settings, threads, stop_event)


        buzzer = Buzzer(settings['DB']['pin']) if 'DB' in settings else None
        if 'DMS1' in settings:
            dms_thread = threading.Thread(
                target=run_dms_console,
                args=(settings['DMS1'], stop_event, led_bulb, buzzer)
            )
            dms_thread.daemon = True
            dms_thread.start()
            threads.append(dms_thread)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            if t != dms_thread:
                stop_event.set()
