import serial
import time
from datetime import datetime


SERIAL_PORT = 'COM14'  
BAUD_RATE = 9600  
FILENAME = f"accel_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

try:
    # Open serial connection
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
    print(f"Saving data to: {FILENAME}")

    # Open the output CSV file
    with open(FILENAME, 'w') as file:
        # Write CSV header
        file.write("timestamp,x,y,z\n")

        while True:
            try:
                # Read line from serial port
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

                if raw_line.count(',') == 2:
                    x, y, z = raw_line.split(',')

                    # Get current timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                    # Write to CSV
                    csv_line = f"{timestamp},{x.strip()},{y.strip()},{z.strip()}\n"
                    file.write(csv_line)
                    file.flush()  # Ensure it's written to disk immediately

                    print(f"Logged: {csv_line.strip()}")

            except KeyboardInterrupt:
                print("\nLogging stopped by user.")
                break
            except Exception as e:
                print(f"Error reading line: {e}")
                continue

except serial.SerialException as e:
    print(f"Serial error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
