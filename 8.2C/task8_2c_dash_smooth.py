# task8_2c_dash_smooth_rewrite.py
# SIT225 8.2C — Smooth Dash streaming for smartphone accelerometer (X, Y, Z)
# Uses smoothdash_rewrite.create_smooth_dash + Arduino Cloud callbacks
# Features: background autosave + "Force Save Now" UI button

from datetime import datetime
import threading
import time
from pathlib import Path
import csv

from arduino_iot_cloud import ArduinoCloudClient
from iot_secrets import DEVICE_ID, SECRET_KEY
from smoothdash_rewrite import create_smooth_dash

import plotly.graph_objects as go
from dash import html, dcc, Output, Input

# ---------------- User configuration ----------------
VAR_X, VAR_Y, VAR_Z = "accelerometer_x", "accelerometer_y", "accelerometer_z"

WINDOW_SIZE = 600
MAX_STEP    = 15
REFRESH_MS  = 150

SAVE_INTERVAL_SEC   = 5
MIN_POINTS_TO_SAVE  = 30
OUTPUT_PREFIX       = "accel"

DATA_DIR = Path(__file__).resolve().parent / "data_2"
DATA_DIR.mkdir(parents=True, exist_ok=True)
# ----------------------------------------------------

# --- Build smooth Dash app ---
app, state = create_smooth_dash(
    channels=["X", "Y", "Z"],
    window_size=WINDOW_SIZE,
    step_size=MAX_STEP,
    refresh_ms=REFRESH_MS,
)
push_sample = state["push"]

# --- Add Force Save button and status ---
def append_control_bar(app):
    base_children = list(app.layout.children) if hasattr(app.layout, "children") else []
    controls = html.Div([
        html.Button("Force Save Now", id="force-save-btn", n_clicks=0, style={"marginRight": "12px"}),
        html.Span("Status: ", style={"fontWeight": "600"}),
        html.Span(id="save-status", children="Waiting for data…"),
        dcc.Interval(id="save-log-interval", interval=3000, n_intervals=0),
    ], style={"padding": "8px 12px", "borderTop": "1px solid #ddd", "marginTop": "8px"})
    if hasattr(app.layout, "children"):
        app.layout.children = [*base_children, controls]
    else:
        app.layout = html.Div([*base_children, controls])

append_control_bar(app)

# --- Cloud data collection ---
latest = {"x": None, "y": None, "z": None}
seen   = {"x": False, "y": False, "z": False}
data_lock = threading.Lock()

log_lock = threading.Lock()
log_buffer = []  # tuples: (iso_ts, x, y, z)

def _current_stamp(): return datetime.now().strftime("%Y%m%d_%H%M%S")

def _emit_if_complete():
    if seen["x"] and seen["y"] and seen["z"]:
        x, y, z = latest["x"], latest["y"], latest["z"]
        ts_ui = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        push_sample(ts_ui, x, y, z)
        ts_iso = datetime.now().isoformat(timespec="milliseconds")
        with log_lock:
            log_buffer.append((ts_iso, x, y, z))
        for k in seen: seen[k] = False

def _on_x(_client, val):
    with data_lock:
        latest["x"] = float(val) if val is not None else None
        seen["x"] = True
        _emit_if_complete()

def _on_y(_client, val):
    with data_lock:
        latest["y"] = float(val) if val is not None else None
        seen["y"] = True
        _emit_if_complete()

def _on_z(_client, val):
    with data_lock:
        latest["z"] = float(val) if val is not None else None
        seen["z"] = True
        _emit_if_complete()

def start_cloud():
    client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY)
    client.register(VAR_X, value=None, on_write=_on_x)
    client.register(VAR_Y, value=None, on_write=_on_y)
    client.register(VAR_Z, value=None, on_write=_on_z)
    def run(): 
        print("[Cloud] Connecting… keep IoT app in foreground.")
        client.start()
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t

# --- File saving helpers ---
def _write_csv(rows, base_path: Path) -> Path:
    csv_file = base_path.with_suffix(".csv")
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","x","y","z"])
        writer.writerows(rows)
    return csv_file

def _write_plot(rows, base_path: Path):
    ts, xs, ys, zs = zip(*rows)
    fig = go.Figure()
    fig.add_scatter(x=ts, y=xs, mode="lines", name="X")
    fig.add_scatter(x=ts, y=ys, mode="lines", name="Y")
    fig.add_scatter(x=ts, y=zs, mode="lines", name="Z")
    fig.update_layout(
        title=f"Accelerometer window — {base_path.name}",
        xaxis_title="Time", yaxis_title="Acceleration",
        margin=dict(l=40,r=20,t=50,b=40),
        legend=dict(orientation="h", y=1.02, x=0),
        template="plotly_white"
    )
    png_path = base_path.with_suffix(".png")
    html_path = base_path.with_suffix(".html")
    try:
        fig.write_image(str(png_path), width=1200, height=500, scale=2)
        return "png", png_path
    except Exception:
        fig.write_html(str(html_path), include_plotlyjs="cdn")
        return "html", html_path

def _save_rows(rows):
    base = DATA_DIR / f"{OUTPUT_PREFIX}_{_current_stamp()}"
    csv_file = _write_csv(rows, base)
    kind, plot_file = _write_plot(rows, base)
    print(f"[Save] {len(rows)} samples | CSV -> {csv_file.name} | {kind.upper()} -> {plot_file.name}")
    return f"Saved {len(rows)} samples: {csv_file.name} + {plot_file.name}"

# --- Autosave background thread ---
def start_autosave():
    def run():
        while True:
            time.sleep(SAVE_INTERVAL_SEC)
            with log_lock:
                buffered = len(log_buffer)
                if buffered >= MIN_POINTS_TO_SAVE:
                    rows = log_buffer[:]
                    log_buffer.clear()
                else:
                    rows = []
            if rows: _save_rows(rows)
            else: print(f"[Save] Skipped: only {buffered} points (< {MIN_POINTS_TO_SAVE})")
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t

# --- Dash callbacks for manual save + buffer info ---
@app.callback(
    Output("save-status", "innerText"),
    Input("force-save-btn", "n_clicks"),
    prevent_initial_call=True
)
def manual_save(_):
    with log_lock:
        if not log_buffer: return "No data buffered yet — move phone with IoT app in foreground."
        rows = log_buffer[:]
        log_buffer.clear()
    return _save_rows(rows)

@app.callback(
    Output("save-status", "title"),
    Input("save-log-interval", "n_intervals")
)
def show_buffer(_):
    with log_lock: n = len(log_buffer)
    print(f"[Buffer] {n} samples buffered")
    return f"Buffered: {n} samples"

# --- Main ---
if __name__ == "__main__":
    start_cloud()
    start_autosave()
    print(f"Saving data to: {DATA_DIR}")
    print("Dash running at http://127.0.0.1:8050")
    app.run(debug=False, host="127.0.0.1", port=8050)
