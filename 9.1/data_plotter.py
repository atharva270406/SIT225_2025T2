import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import numpy as np

# 1. DATA INPUT
# The provided data is stored as a multi-line string.
data = """Timestamp,Linear Acceleration,Crash Status
2025-09-26 16:57:56,8.67,Normal
2025-09-26 16:57:57,8.23,Normal
2025-09-26 16:57:58,9.31,Normal
2025-09-26 16:57:59,5.62,Normal
2025-09-26 16:58:00,5.81,Normal
2025-09-26 16:58:01,5.38,Normal
2025-09-26 16:58:02,7.16,Normal
2025-09-26 16:58:03,5.45,Normal
2025-09-26 16:58:04,7.28,Normal
2025-09-26 16:58:05,6.41,Normal
2025-09-26 16:58:06,9.42,Normal
2025-09-26 16:58:07,7.8,Normal
2025-09-26 16:58:08,6.91,Normal
2025-09-26 16:58:09,9.94,Normal
2025-09-26 16:58:10,6.71,Normal
2025-09-26 16:58:11,5.59,Normal
2025-09-26 16:58:12,14.59,Sudden Movement
2025-09-26 16:58:13,5.94,Normal
2025-09-26 16:58:14,5.52,Normal
2025-09-26 16:58:15,5.14,Normal
2025-09-26 16:58:16,8.18,Normal
2025-09-26 16:58:17,5.2,Normal
2025-09-26 16:58:18,6.44,Normal
2025-09-26 16:58:19,24.02,Crash Detected
2025-09-26 16:58:20,6.96,Normal
2025-09-26 16:58:21,13.83,Sudden Movement
2025-09-26 16:58:22,9.84,Normal
2025-09-26 16:58:23,6.65,Normal
2025-09-26 16:58:24,5.43,Normal
2025-09-26 16:58:25,6.79,Normal
2025-09-26 16:58:26,6.28,Normal
2025-09-26 16:58:27,9.42,Normal
2025-09-26 16:58:28,9.21,Normal
2025-09-26 16:58:29,9.11,Normal
2025-09-26 16:58:30,7.13,Normal
2025-09-26 16:58:31,8.2,Normal
2025-09-26 16:58:32,7.49,Normal
2025-09-26 16:58:33,5.4,Normal
2025-09-26 16:58:34,6.49,Normal
2025-09-26 16:58:35,9.81,Normal
2025-09-26 16:58:36,18.27,Sudden Movement
2025-09-26 16:58:37,8.86,Normal
2025-09-26 16:58:38,6.2,Normal
2025-09-26 16:58:39,9.24,Normal
2025-09-26 16:58:40,21.81,Crash Detected
2025-09-26 16:58:41,27.86,Crash Detected
2025-09-26 16:58:42,8.92,Normal
2025-09-26 16:58:43,5.47,Normal
2025-09-26 16:58:44,8.05,Normal
2025-09-26 16:58:45,8.44,Normal
2025-09-26 16:58:46,6.63,Normal
2025-09-26 16:58:47,7.84,Normal
2025-09-26 16:58:48,7.13,Normal
2025-09-26 16:58:49,8.18,Normal
2025-09-26 16:58:50,6.98,Normal
2025-09-26 16:58:51,5.8,Normal
2025-09-26 16:58:52,6.09,Normal
2025-09-26 16:58:53,8.86,Normal
2025-09-26 16:58:54,6.34,Normal
2025-09-26 16:58:55,8.86,Normal
"""

# Read the data into a DataFrame and parse the Timestamp column
df = pd.read_csv(StringIO(data), parse_dates=['Timestamp'])

# 2. PLOTTING SETUP
plt.figure(figsize=(16, 7))

# Define colors and markers for the different 'Crash Status' categories
# This allows for distinct visual representation of the events.
colors = {
    'Normal': 'tab:blue',
    'Sudden Movement': 'tab:orange',
    'Crash Detected': 'tab:red'
}
markers = {
    'Normal': 'o',
    'Sudden Movement': '^',
    'Crash Detected': 's'
}

# 3. PLOT GENERATION

# Plot the linear acceleration as a simple line for the overall trend
plt.plot(df['Timestamp'], df['Linear Acceleration'], color='lightgray', linestyle='-', linewidth=1, zorder=1)

# Plot the scatter points, colored by 'Crash Status'
for status, color in colors.items():
    subset = df[df['Crash Status'] == status]
    plt.scatter(
        subset['Timestamp'],
        subset['Linear Acceleration'],
        label=status,
        color=color,
        marker=markers.get(status, 'x'), # Fallback marker is 'x'
        s=100, # Marker size
        zorder=3 # Ensures the points are drawn on top of the line
    )

# 4. CUSTOMIZATION
plt.title('Linear Acceleration Over Time, Categorized by Event Status', fontsize=18, pad=20)
plt.xlabel('Timestamp (Time)', fontsize=14)
plt.ylabel('Linear Acceleration ($\mathrm{m/s^2}$)', fontsize=14)

# Add a horizontal line to indicate a potential "high acceleration" threshold (e.g., 10 m/s^2)
plt.axhline(y=10.0, color='green', linestyle='--', linewidth=1, label='10 $\mathrm{m/s^2}$ Threshold')

plt.legend(title='Event Status', loc='upper right')
plt.grid(True, which='major', linestyle=':', linewidth=0.5)

# Format the x-axis for better readability of datetimes (rotating labels)
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.show()
