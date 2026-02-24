import threading
import time
from typing import Callable


def gsg_callback(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, timestamp, 
                 mqtt_publisher=None, settings=None):
    t = time.localtime(timestamp)
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Accel: X={acc_x:6.3f}g Y={acc_y:6.3f}g Z={acc_z:6.3f}g")
    print(f"Gyro:  X={gyro_x:6.2f}° Y={gyro_y:6.2f}° Z={gyro_z:6.2f}°")
    
    #Update system state
    
    if mqtt_publisher and settings:
        for axis, value in [('accel_x', acc_x), ('accel_y', acc_y), ('accel_z', acc_z),
                            ('gyro_x', gyro_x), ('gyro_y', gyro_y), ('gyro_z', gyro_z)]:
            mqtt_publisher.add_reading(
                sensor_type=axis,
                value=value,
                simulated=settings.get('simulated', False)
            )


def run_gsg(settings, threads, stop_event, mqtt_publisher=None):
    def callback_wrapper(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, timestamp):
        gsg_callback(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, timestamp, 
                     mqtt_publisher, settings)
    
    if settings['simulated']:
        from RPI2.simulators.gsg import run_gsg_simulator
        print("Starting GSG simulator")
        gsg_thread = threading.Thread(
            target=run_gsg_simulator,
            args=(callback_wrapper, stop_event),
            daemon=True
        )
        gsg_thread.start()
        threads.append(gsg_thread)
        print("GSG simulator started")
    else:
        from RPI2.sensors.gsg import run_gsg_loop, GSG
        print("Starting GSG loop")
        gsg = GSG(i2c_bus=settings.get('i2c_bus', 1))
        interval = settings.get('read_interval', 0.5)
        
        gsg_thread = threading.Thread(
            target=run_gsg_loop,
            args=(gsg, interval, callback_wrapper, stop_event),
            daemon=True
        )
        gsg_thread.start()
        threads.append(gsg_thread)
        print("GSG loop started")