import serial
import time
import random

# Set up the serial connection (change 'COM9' if needed)
ser = serial.Serial('COM9', 4800, timeout=10)
time.sleep(2)  # Give Arduino time to reset

while True:
    blink_count = random.randint(1, 5)

    current_time = time.strftime("%H:%M:%S")
    print("[" + current_time + "] Sending:", blink_count)
    ser.write((str(blink_count) + "\n").encode())
    ser.flush()

    response = ser.readline().decode().strip()

    if response.isdigit():
        delay_time = int(response)
        print("[" + time.strftime("%H:%M:%S") + "] Received:", delay_time, "- sleeping...")
        time.sleep(delay_time)
        print("[" + time.strftime("%H:%M:%S") + "] Woke up\n")
    else:
        print("[" + time.strftime("%H:%M:%S") + "] No valid data received.\n")
