import serial
import csv
import time

PORT = 'COM16'
BAUD = 9600
filename = f"gyro_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"

def read_gyro_data():
    try:
        connection = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Serial connection established on {PORT} at {BAUD} baud.")
    except serial.SerialException as err:
        print(f"Failed to open serial port: {err}")
        return

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp_ms', 'gyro_x', 'gyro_y', 'gyro_z'])
        print("Receiving data... Press Ctrl+C to exit.")

        try:
            while True:
                raw_line = connection.readline().decode('utf-8').strip()
                if not raw_line:
                    continue

                data_parts = raw_line.split(',')
                if len(data_parts) == 4:
                    timestamp, gx, gy, gz = data_parts
                    print(f"{timestamp},{gx},{gy},{gz}")
                    writer.writerow([timestamp, gx, gy, gz])
                else:
                    print(f"Invalid data format: {raw_line}")

        except KeyboardInterrupt:
            print("\nData collection stopped by user.")
        finally:
            connection.close()
            print(f"Data successfully saved to {filename}")

if __name__ == "__main__":
    read_gyro_data()
