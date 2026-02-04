import threading


def run_sd4(settings, threads, stop_event):
    
    if settings['simulated']:
        from RPI2.simulators.sd4 import run_sd4_simulator
        print("Starting SD4 simulator")
        sd4_thread = threading.Thread(
            target=run_sd4_simulator,
            args=(stop_event,),
            daemon=True
        )
        sd4_thread.start()
        threads.append(sd4_thread)
        print("SD4 simulator started")
    else:
        from RPI2.sensors.sd4 import run_sd4_timer, SD4
        print("Starting SD4 timer")
        sd4 = SD4(settings['clk_pin'], settings['dio_pin'])
        sd4_thread = threading.Thread(
            target=run_sd4_timer,
            args=(sd4, stop_event),
            daemon=True
        )
        sd4_thread.start()
        threads.append(sd4_thread)
        print("SD4 timer started")