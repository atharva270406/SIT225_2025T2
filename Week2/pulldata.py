import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "accel_log_20250807_151559.csv"
IMG_FILE = DATA_FILE.replace(".csv", "_plot.png")

try:
    data = pd.read_csv(DATA_FILE)
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data['timestamp'], data['x'], label='X-axis (g)', color='red', linewidth=1)
    ax.plot(data['timestamp'], data['y'], label='Y-axis (g)', color='green', linewidth=1)
    ax.plot(data['timestamp'], data['z'], label='Z-axis (g)', color='blue', linewidth=1)

    ax.set_title('Accelerometer Data Over Time')
    ax.set_xlabel('Time')
    ax.set_ylabel('Acceleration (g)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(IMG_FILE, dpi=300)
    print(f"[INFO] Saved graph to {IMG_FILE}")
    plt.show()

except FileNotFoundError:
    print(f"[ERROR] File not found: {DATA_FILE}")
except Exception as err:
    print(f"[ERROR] Could not process file: {err}")
