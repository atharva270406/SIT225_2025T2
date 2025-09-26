import csv
import time
import random


API_KEY = 'sk_test_9f8a1c2b7e4d4a1f9c3e2a7d'
THING_ID = 'thing_abc123xyz789'

CSV_FILENAME = 'crashdata.csv'
NUM_ENTRIES = 100

def generate_fake_entry():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    x = round(random.uniform(-2.0, 2.0), 2)
    y = round(random.uniform(-2.0, 2.0), 2)
    z = round(random.uniform(-2.0, 2.0), 2)
    linear = round((x**2 + y**2 + z**2)**0.5, 2)

    if linear > 20:
        status = "Crash Detected"
    elif linear > 10:
        status = "Sudden Movement"
    else:
        status = "Normal"

    return [timestamp, x, y, z, linear, status]

with open(CSV_FILENAME, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'X', 'Y', 'Z', 'Linear Acceleration', 'Crash Status'])

    for _ in range(NUM_ENTRIES):
        row = generate_fake_entry()
        writer.writerow(row)
        print("Logged:", row)
        time.sleep(0.1)  # Simulate delay between entries

print(f"\n✅ Fake cloud data saved to {CSV_FILENAME}")
