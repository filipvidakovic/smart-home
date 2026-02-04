import time
import threading
from typing import Optional

try:
    import tm1637
    TM1637_AVAILABLE = True
except ImportError:
    TM1637_AVAILABLE = False
    print("Warning: tm1637 library not available")


class SD4:
    
    def __init__(self, clk_pin, dio_pin):
        self.clk_pin = clk_pin
        self.dio_pin = dio_pin
        self.lock = threading.Lock()
        
        if not TM1637_AVAILABLE:
            raise ImportError("tm1637 library is required for 7-segment display")
        
        self.display = tm1637.TM1637(clk=self.clk_pin, dio=self.dio_pin)
        self.display.brightness(7)  # Max brightness (0-7)
        
        print(f"SD4: Initialized (CLK={self.clk_pin}, DIO={self.dio_pin})")

    def show_number(self, number: int, colon: bool = False):

        with self.lock:
            if 0 <= number <= 9999:
                self.display.number(number)
                if colon:
                    self.display.show(':', 2)  # Show colon at position 2
            else:
                print(f"SD4: Number {number} out of range (0-9999)")

    def show_time(self, hours: int, minutes: int):

        with self.lock:
            time_value = hours * 100 + minutes
            self.display.numbers(hours, minutes, colon=True)

    def show_text(self, text: str):
        with self.lock:
            self.display.write(text)

    def clear(self):
        with self.lock:
            self.display.write([0, 0, 0, 0])

    def cleanup(self):
        self.clear()


def run_sd4_timer(sd4: SD4, stop_event):

    print("SD4: Starting timer display")
    
    try:
        seconds = 0
        while not stop_event.is_set():
            minutes = seconds // 60
            secs = seconds % 60
            
            # Display MM:SS format
            display_value = minutes * 100 + secs
            sd4.show_number(display_value, colon=True)
            
            time.sleep(1)
            seconds += 1
            
            # Reset after 99:59
            if seconds >= 6000:
                seconds = 0
                
    except Exception as e:
        print(f"SD4: Error in timer loop: {e}")
    finally:
        print("SD4: Cleaning up...")
        sd4.cleanup()
        print("SD4: Cleanup complete")