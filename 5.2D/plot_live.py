#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import paho.mqtt.client as mqtt
import config   # your MQTT_* settings stored here

# ------------------- CONFIG -------------------
BUFFER_LIMIT = 1200          # how many points to keep in memory
TIME_WINDOW = 30             # seconds shown on x-axis
REFRESH_RATE = 200           # milliseconds between redraws
CSV_FILE = None              # set to "data.csv" if you want to log values
# ------------------------------------------------

# circular buffers for time and sensor values
time_vals = deque(maxlen=BUFFER_LIMIT)
gx_vals = deque(maxlen=BUFFER_LIMIT)
gy_vals = deque(maxlen=BUFFER_LIMIT)
gz_vals = deque(maxlen=BUFFER_LIMIT)

start_time = None

def current_iso():
    """Return current UTC time as ISO string with milliseconds."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

# ----------------- Matplotlib Setup -----------------
plt.rcParams["figure.autolayout"] = True
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
ax_gx, ax_gy, ax_gz, ax_all = axes.ravel()

line_gx, = ax_gx.plot([], [], label="X")
line_gy, = ax_gy.plot([], [], label="Y")
line_gz, = ax_gz.plot([], [], label="Z")
line_allx, = ax_all.plot([], [], label="X")
line_ally, = ax_all.plot([], [], label="Y")
line_allz, = ax_all.plot([], [], label="Z")

titles = [
    "Gyroscope X", 
    "Gyroscope Y", 
    "Gyroscope Z", 
    "Gyroscope X,Y,Z Combined"
]

for ax, title in zip((ax_gx, ax_gy, ax_gz, ax_all), titles):
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.grid(True)

ax_all.legend(loc="upper right")

def save_snapshot(event):
    """Press 's' key to save snapshot."""
    if event.key == "s":
        filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(filename, dpi=150)
        print(f"📸 Plot saved: {filename}")

fig.canvas.mpl_connect("key_press_event", save_snapshot)

def refresh_plot(_):
    """Update all plots with latest data."""
    if not time_vals:
        return

    xmax = time_vals[-1]
    xmin = max(0, xmax - TIME_WINDOW)

    for ax in (ax_gx, ax_gy, ax_gz, ax_all):
        ax.set_xlim(xmin, max(TIME_WINDOW, xmax))

    # update each subplot
    line_gx.set_data(time_vals, gx_vals); ax_gx.relim(); ax_gx.autoscale_view()
    line_gy.set_data(time_vals, gy_vals); ax_gy.relim(); ax_gy.autoscale_view()
    line_gz.set_data(time_vals, gz_vals); ax_gz.relim(); ax_gz.autoscale_view()

    line_allx.set_data(time_vals, gx_vals)
    line_ally.set_data(time_vals, gy_vals)
    line_allz.set_data(time_vals, gz_vals)
    ax_all.relim(); ax_all.autoscale_view()

# ----------------- MQTT Functions -----------------
def mqtt_connected(client, userdata, flags, rc, props=None):
    if rc == 0:
        print("✅ Connected to HiveMQ broker")
        client.subscribe(config.MQTT_TOPIC, qos=1)
        print(f"📡 Subscribed to topic: {config.MQTT_TOPIC}")
    else:
        print(f"❌ Connection failed with code {rc}")

def mqtt_message(client, userdata, msg):
    global start_time
    try:
        message = msg.payload.decode("utf-8").strip()
        values = json.loads(message)   # expecting {"x":..,"y":..,"z":..}

        gx, gy, gz = float(values["x"]), float(values["y"]), float(values["z"])
        now = datetime.now(timezone.utc)

        if start_time is None:
            start_time = now
        elapsed = (now - start_time).total_seconds()

        # push into buffers
        time_vals.append(elapsed)
        gx_vals.append(gx)
        gy_vals.append(gy)
        gz_vals.append(gz)

        if CSV_FILE:
            with open(CSV_FILE, "a", encoding="utf-8") as f:
                f.write(f"{current_iso()},{gx},{gy},{gz}\n")

    except Exception as e:
        print(f"⚠️ Error parsing message: {e} | raw={msg.payload[:100]}")

def mqtt_disconnected(client, userdata, rc, props=None):
    print(f"🔌 Disconnected from broker (code={rc})")

# ----------------- MQTT Client Setup -----------------
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
client.tls_set()   # TLS required by HiveMQ Cloud
client.on_connect = mqtt_connected
client.on_message = mqtt_message
client.on_disconnect = mqtt_disconnected

print("🚀 Connecting to MQTT broker…")
client.connect(config.MQTT_BROKER, int(config.MQTT_PORT), keepalive=60)
client.loop_start()

ani = animation.FuncAnimation(fig, refresh_plot, interval=REFRESH_RATE)

try:
    plt.show()
finally:
    client.loop_stop()
    client.disconnect()
