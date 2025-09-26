import serial
import csv
import time

SERIAL_PORT = 'COM3'       
BAUD_RATE = 9600
CSV_FILENAME = 'crash_xyz_log.csv'

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

with open(CSV_FILENAME, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'X', 'Y', 'Z', 'Crash Status'])

    print("Logging started...")

    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("Timestamp:"):
                try:
                    parts = line.split(", ")
                    timestamp = parts[0].split(": ")[1]
                    x = parts[1].split(": ")[1]
                    y = parts[2].split(": ")[1]
                    z = parts[3].split(": ")[1]
                    status = parts[4].split(": ")[1]

                    writer.writerow([timestamp, x, y, z, status])
                    print(f"{timestamp} | {x} | {y} | {z} | {status}")
                except IndexError:
                    continue
    except KeyboardInterrupt:
        print("\nLogging stopped.")
        ser.close()
