# Step 1: Import necessary libraries
import pandas as pd
import matplotlib.pyplot as plt

# Step 2: Upload the CSV file
from google.colab import files
uploaded = files.upload()

# Step 3: Load the data into a DataFrame
df = pd.read_csv('accelerometerdata.csv', parse_dates=['timestamp'])

# Step 4: Plot the accelerometer data
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['accelx'], label='Accel X', color='red')
plt.plot(df['timestamp'], df['accely'], label='Accel Y', color='green')
plt.plot(df['timestamp'], df['accelz'], label='Accel Z', color='blue')

# Step 5: Customize the plot
plt.title('Accelerometer Data Over Time')
plt.xlabel('Timestamp')
plt.ylabel('Acceleration (g)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

# Step 6: Show the plot
plt.show()
