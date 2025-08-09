import serial
import time
from datetime import datetime

PORT_NAME = 'COM14'
BAUD = 9600
LOG_FILE = f"acc_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def open_serial_connection(port, baud_rate):
    return serial.Serial(port, baud_rate, timeout=1)

def log_data(port_name, baud_rate, output_file):
    try:
        arduino = open_serial_connection(port_name, baud_rate)
        print(f"[INFO] Connected to {port_name} at {baud_rate} baud.")
        print(f"[INFO] Writing data to: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as log:
            log.write("time_stamp,acc_x,acc_y,acc_z\n")

            while True:
                try:
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if line and line.count(',') == 2:
                        ax, ay, az = (item.strip() for item in line.split(','))
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        log.write(f"{now},{ax},{ay},{az}\n")
                        log.flush()
                        print(f"[DATA] {now} -> X:{ax}  Y:{ay}  Z:{az}")
                except KeyboardInterrupt:
                    print("\n[INFO] Logging stopped manually.")
                    break
                except Exception as err:
                    print(f"[WARN] Failed to read/process line: {err}")
    except serial.SerialException as serr:
        print(f"[ERROR] Could not open serial port: {serr}")
    except Exception as e:
        print(f"[ERROR] Unexpected issue: {e}")
    finally:
        if 'arduino' in locals() and arduino.is_open:
            arduino.close()
            print("[INFO] Serial connection closed.")

if __name__ == "__main__":
    log_data(PORT_NAME, BAUD, LOG_FILE)
