# task5_dash_live_alt.py
# SIT225 8.1P — Live accelerometer viewer with Plotly Dash
#
# Usage:
#   1) pip install arduino-iot-cloud dash plotly pandas kaleido
#   2) Create iot_secrets.py with DEVICE_ID + SECRET_KEY
#   3) Ensure Thing variables: accelerometer_x, accelerometer_y, accelerometer_z
#   4) Run: python task5_dash_live_alt.py → open http://127.0.0.1:8050

from pathlib import Path
from datetime import datetime
import threading
from collections import deque

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Output, Input

from arduino_iot_cloud import ArduinoCloudClient
from iot_secrets import DEVICE_ID, SECRET_KEY

# ------------------ Settings ------------------
VAR_X, VAR_Y, VAR_Z = "accelerometer_x", "accelerometer_y", "accelerometer_z"
WINDOW_SIZE = 5            # number of samples per saved window
UI_REFRESH_MS = 1000       # poll frequency (ms)

BASE_DIR = Path(__file__).resolve().parent
SAVE_DIR = BASE_DIR / "plots"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ Buffers -------------------
data_queue = deque()        # holds (timestamp, x, y, z)
queue_lock = threading.Lock()

latest_vals = {"x": None, "y": None, "z": None}
received    = {"x": False, "y": False, "z": False}
val_lock    = threading.Lock()

last_window = []
last_saved_file = None

# ------------------ Cloud Logic ----------------
def _push_if_ready():
    """Append one complete XYZ sample to queue if all 3 arrived."""
    if all(received.values()):
        row = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            latest_vals["x"],
            latest_vals["y"],
            latest_vals["z"],
        )
        with queue_lock:
            data_queue.append(row)
        for k in received:
            received[k] = False

def _on_var(axis):
    def handler(_client, value):
        with val_lock:
            latest_vals[axis] = float(value) if value is not None else None
            received[axis] = True
            _push_if_ready()
    return handler

def start_cloud():
    """Start Arduino IoT Cloud client in background thread."""
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,
        password=SECRET_KEY,
    )
    client.register(VAR_X, value=None, on_write=_on_var("x"))
    client.register(VAR_Y, value=None, on_write=_on_var("y"))
    client.register(VAR_Z, value=None, on_write=_on_var("z"))

    def runner():
        try:
            print("[Cloud] Connecting... keep phone app active.")
            client.start()
        except Exception as exc:
            print("[Cloud] Error:", exc)

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    return t

# ------------------ Plotting -------------------
def make_figure(batch):
    """Return a Plotly figure for given batch of samples."""
    fig = go.Figure()
    if not batch:
        fig.update_layout(
            template="plotly_white",
            title="Waiting for data...",
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis_title="Time",
            yaxis_title="Acceleration (g)",
        )
        return fig

    ts, xs, ys, zs = zip(*batch)
    fig.add_trace(go.Scatter(x=list(ts), y=list(xs), mode="lines", name="X"))
    fig.add_trace(go.Scatter(x=list(ts), y=list(ys), mode="lines", name="Y"))
    fig.add_trace(go.Scatter(x=list(ts), y=list(zs), mode="lines", name="Z"))

    fig.update_layout(
        template="plotly_white",
        title=f"Latest window (N={len(batch)})",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title="Time",
        yaxis_title="Acceleration (g)",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )
    return fig

def save_window(batch, fig):
    """Save current batch to CSV + PNG (or HTML fallback)."""
    global last_saved_file
    if not batch:
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"accel_{stamp}"

    df = pd.DataFrame(batch, columns=["timestamp", "x", "y", "z"])
    csv_path = SAVE_DIR / f"{base}.csv"
    df.to_csv(csv_path, index=False)

    try:
        png_path = SAVE_DIR / f"{base}.png"
        fig.write_image(str(png_path), width=1200, height=500, scale=2)
        last_saved_file = png_path.name
    except Exception:
        html_path = SAVE_DIR / f"{base}.html"
        fig.write_html(str(html_path), include_plotlyjs="cdn")
        last_saved_file = html_path.name
    return last_saved_file

# ------------------ Dash App ------------------
app = Dash(__name__)
app.layout = html.Div(
    style={"fontFamily": "system-ui, Segoe UI, Roboto, Arial", "padding": "12px"},
    children=[
        html.H2("SIT225 8.1P — Live Accelerometer (X/Y/Z)"),
        html.Div(id="status", style={"marginBottom": "8px"}),
        dcc.Graph(id="graph"),
        dcc.Interval(id="timer", interval=UI_REFRESH_MS, n_intervals=0),
        html.Div(
            "If PNG export fails, install 'kaleido' (pip install kaleido).",
            style={"fontSize": "12px", "opacity": 0.7},
        ),
    ],
)

@app.callback(
    Output("graph", "figure"),
    Output("status", "children"),
    Input("timer", "n_intervals"),
    prevent_initial_call=False,
)
def update(_tick):
    global last_window
    with queue_lock:
        if len(data_queue) >= WINDOW_SIZE:
            window = [data_queue.popleft() for _ in range(WINDOW_SIZE)]
        else:
            window = None

    if window is None:
        fig = make_figure(last_window)
        return fig, f"Waiting... queue={len(data_queue)}, last_save={last_saved_file or '—'}"

    last_window = window
    fig = make_figure(window)
    saved_file = save_window(window, fig)
    return fig, f"Saved: {saved_file} | queue now {len(data_queue)}"

# ------------------ Main ----------------------
def main():
    start_cloud()
    print("Dash running at http://127.0.0.1:8050")
    app.run(debug=False, host="127.0.0.1", port=8050)

if __name__ == "__main__":
    main()
