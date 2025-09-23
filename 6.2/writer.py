# arduino_gyro_logger.py
# Real-time Gyroscope Data Logger to CSV
# Run:
#   pip install pandas pyserial

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import serial

# ---------- Configuration ----------
SERIAL_PORT = r"\\.\COM14"       # Change for your Arduino
BAUD_RATE = 115200
OUTPUT_DIR = "./data"
ROWS_PER_CSV = 500
FILE_PREFIX = "gyro"
PRINT_INTERVAL = 50
# -----------------------------------

output_path = Path(OUTPUT_DIR)
output_path.mkdir(parents=True, exist_ok=True)

axis_cols = {
    "x": f"{FILE_PREFIX}_x",
    "y": f"{FILE_PREFIX}_y",
    "z": f"{FILE_PREFIX}_z"
}

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # allow Arduino to reset
except Exception as e:
    print(f"ERROR: Unable to open serial port {SERIAL_PORT}: {e}", file=sys.stderr)
    sys.exit(1)

print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
print(f"CSV output directory: {output_path.resolve()}")
print(f"Each file will contain {ROWS_PER_CSV} samples.")

sample_counter = 0
buffered_rows = []

def write_csv_chunk():
    """Save buffered samples to a timestamped CSV file and clear buffer."""
    global buffered_rows
    if not buffered_rows:
        return
    df = pd.DataFrame(buffered_rows, columns=["sample", "timestamp", axis_cols["x"], axis_cols["y"], axis_cols["z"]])
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{FILE_PREFIX}_data_{timestamp_str}.csv"
    file_path = output_path / file_name
    df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Saved {file_path} ({len(df)} rows).")
    buffered_rows = []

try:
    arduino.reset_input_buffer()
    while True:
        raw_line = arduino.readline().decode("utf-8", errors="ignore").strip()
        if not raw_line:
            continue

        values = raw_line.split(",")
        if len(values) != 3:
            continue

        try:
            x_val, y_val, z_val = map(float, map(str.strip, values))
        except ValueError:
            continue

        timestamp = datetime.now().isoformat(timespec="milliseconds")
        buffered_rows.append([sample_counter, timestamp, x_val, y_val, z_val])
        sample_counter += 1

        if sample_counter % PRINT_INTERVAL == 0:
            print(f"Collected {sample_counter} samples...")

        if len(buffered_rows) >= ROWS_PER_CSV:
            write_csv_chunk()

except KeyboardInterrupt:
    print("\nKeyboard interrupt detected. Saving remaining samples...")
    write_csv_chunk()
except Exception as e:
    print(f"\nERROR: {e}", file=sys.stderr)
    write_csv_chunk()
finally:
    arduino.close()
