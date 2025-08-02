import sys
import traceback
from arduino_iot_cloud import ArduinoCloudClient
from datetime import datetime
import csv

# Device credentials
DEVICE_ID = "7f21a336-73ad-49b1-821e-e2bfe40e6912"
SECRET_KEY = "YsOfTIi1m8DCwAEVKSjVkUAAP"

# Dictionary to store latest accelerometer readings
accel_data = {"accelx": None, "accely": None, "accelz": None}

def write_to_csv(writer):
    """Write a row to CSV when all values are available."""
    if all(value is not None for value in accel_data.values()):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([
            timestamp,
            accel_data["accelx"],
            accel_data["accely"],
            accel_data["accelz"]
        ])
        print(f"{timestamp} | X: {accel_data['accelx']}, Y: {accel_data['accely']}, Z: {accel_data['accelz']}")
        # Reset values
        for key in accel_data:
            accel_data[key] = None

def create_callback(axis, writer):
    """Generate a callback function for a given axis."""
    def callback(client, value):
        accel_data[axis] = value
        write_to_csv(writer)
    return callback

def main():
    print("Starting accelerometer data collection...")

    with open("accelerometer_data.csv", mode="a", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["timestamp", "accelx", "accely", "accelz"])

        client = ArduinoCloudClient(
            device_id=DEVICE_ID,
            username=DEVICE_ID,
            password=SECRET_KEY
        )

        # Register variables with callbacks
        client.register("accelx", value=None, on_write=create_callback("accelx", writer))
        client.register("accely", value=None, on_write=create_callback("accely", writer))
        client.register("accelz", value=None, on_write=create_callback("accelz", writer))

        # Start listening
        client.start()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("An error occurred:")
        traceback.print_exc()
