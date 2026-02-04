import time
import threading
from typing import Callable, Optional, Tuple

try:
    import smbus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    print("Warning: smbus library not available")


class GSG:
    
    # MPU6050 I2C address
    MPU6050_ADDR = 0x68
    
    # Register addresses
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43
    
    def __init__(self, i2c_bus=1):
        self.bus_num = i2c_bus
        self.lock = threading.Lock()
        
        if not SMBUS_AVAILABLE:
            raise ImportError("smbus library is required for MPU6050")
        
        self.bus = smbus.SMBus(self.bus_num)
        
        # Wake up the MPU6050
        self.bus.write_byte_data(self.MPU6050_ADDR, self.PWR_MGMT_1, 0)
        time.sleep(0.1)
        
        print(f"GSG: MPU6050 initialized on I2C bus {self.bus_num}")

    def read_raw_data(self, addr):
        high = self.bus.read_byte_data(self.MPU6050_ADDR, addr)
        low = self.bus.read_byte_data(self.MPU6050_ADDR, addr + 1)
        
        value = (high << 8) | low
        
        # Convert to signed value
        if value > 32768:
            value = value - 65536
        
        return value

    def read(self) -> Optional[Tuple[float, float, float, float, float, float]]:

        with self.lock:
            try:
                # Read accelerometer data
                acc_x = self.read_raw_data(self.ACCEL_XOUT_H)
                acc_y = self.read_raw_data(self.ACCEL_XOUT_H + 2)
                acc_z = self.read_raw_data(self.ACCEL_XOUT_H + 4)
                
                # Read gyroscope data
                gyro_x = self.read_raw_data(self.GYRO_XOUT_H)
                gyro_y = self.read_raw_data(self.GYRO_XOUT_H + 2)
                gyro_z = self.read_raw_data(self.GYRO_XOUT_H + 4)
                
                # Convert to g and °/s
                accel_scale = 16384.0  # For ±2g range
                gyro_scale = 131.0     # For ±250°/s range
                
                return (
                    round(acc_x / accel_scale, 3),
                    round(acc_y / accel_scale, 3),
                    round(acc_z / accel_scale, 3),
                    round(gyro_x / gyro_scale, 3),
                    round(gyro_y / gyro_scale, 3),
                    round(gyro_z / gyro_scale, 3)
                )
                
            except Exception as e:
                print(f"GSG: Error reading sensor: {e}")
                return None

    def cleanup(self):
        try:
            self.bus.write_byte_data(self.MPU6050_ADDR, self.PWR_MGMT_1, 0x40)
        except:
            pass


def run_gsg_loop(gsg: GSG, interval: float, callback: Callable, stop_event):

    print(f"GSG: Starting measurement loop (interval={interval}s)")
    
    try:
        while not stop_event.is_set():
            reading = gsg.read()
            timestamp = time.time()

            if reading is not None:
                try:
                    callback(*reading, timestamp)
                except Exception as e:
                    print(f"GSG: Error in callback: {e}")
            else:
                print("GSG: Failed to read sensor")

            time.sleep(interval)
            
    except Exception as e:
        print(f"GSG: Error in measurement loop: {e}")
    finally:
        print("GSG: Cleaning up...")
        gsg.cleanup()
        print("GSG: Cleanup complete")