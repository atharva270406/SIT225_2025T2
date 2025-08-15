import pandas as pd
import matplotlib.pyplot as plt
from google.colab import files

uploaded = files.upload()

df = pd.read_csv('gyroscope_data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['x'], label='X-axis', marker='o', markersize=3)
plt.plot(df['timestamp'], df['y'], label='Y-axis', marker='o', markersize=3)
plt.plot(df['timestamp'], df['z'], label='Z-axis', marker='o', markersize=3)

plt.title('Gyroscope Data Over Time')
plt.xlabel('Timestamp')
plt.ylabel('Gyroscope Reading')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
