# capture_dash.py
"""
SIT225 Task 8.3D — Real-time Dash stream with 10s segmented saving + webcam snapshot.

Features:
- Streams accelerometer data from Arduino IoT Cloud into a smooth Plotly Dash graph.
- Buffers values into 10-second windows; saves each window as CSV + chart + webcam photo.
- Maintains an annotations.csv for labeling later.
"""

import csv
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from dash import Dash, dcc, html, Output, Input, no_update
import plotly.graph_objects as go
from smoothdash import make_smooth_app
from arduino_iot_cloud import ArduinoCloudClient
from iot_secrets import DEVICE_ID, SECRET_KEY

# Webcam support (optional)
try:
    import cv2
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False


# ---------- Config ----------
VAR_X, VAR_Y, VAR_Z = "accelerometer_x", "accelerometer_y", "accelerometer_z"
WINDOW_DURATION = 10           # seconds per saved chunk
MIN_ROWS = 15                  # ensure enough samples before saving
HOST, PORT = "127.0.0.1", 8050

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data2"
DATA_DIR.mkdir(exist_ok=True)
ANNOT_FILE = DATA_DIR / "annotations.csv"

# ---------- Smooth Dash base ----------
app, state = make_smooth_app(
    ["X", "Y", "Z"],
    window_points=700,
    max_append=25,
    poll_ms=150,
)
append_point = state["push"]

from flask import send_from_directory

@app.server.route("/data2/<path:fname>")
def serve_files(fname):
    return send_from_directory(DATA_DIR, fname, as_attachment=False)

# ---------- Extend layout ----------
extra_ui = html.Div([
    html.Div([
        html.Button("Save window now", id="save-btn", n_clicks=0, style={"marginRight":"8px"}),
        html.Span("Status: "),
        html.Span(id="save-status", children="Idle"),
        dcc.Interval(id="buf-check", interval=3000, n_intervals=0)
    ], style={"padding":"8px 10px", "borderTop":"1px solid #ccc", "marginTop":"8px"}),
    html.Div([
        html.H4("Latest saved snapshot"),
        html.Img(id="preview-img", src="", style={"maxWidth":"100%", "border":"1px solid #ccc", "borderRadius":"6px"})
    ], style={"padding":"8px 10px"})
])

app.layout.children = [*app.layout.children, extra_ui]

# ---------- Data buffers ----------
latest_vals = {"x": None, "y": None, "z": None}
got_flag = {"x": False, "y": False, "z": False}
lock = threading.Lock()

buf = []
buf_lock = threading.Lock()
buf_start = None


# ---------- Camera helper ----------
class Camera:
    def __init__(self):
        self.cam = None
        self.lock = threading.Lock()

    def open(self):
        if not OPENCV_OK:
            return False
        if self.cam:
            return True
        try:
            cam = cv2.VideoCapture(0)
            ok, _ = cam.read()
            if not ok:
                cam.release()
                return False
            self.cam = cam
            return True
        except Exception:
            return False

    def snap(self, out: Path):
        if not self.open():
            return None
        with self.lock:
            ok, frame = self.cam.read()
            if not ok:
                return None
            path = out.with_suffix(".jpg")
            cv2.imwrite(str(path), frame)
            return path

    def close(self):
        if self.cam:
            self.cam.release()
            self.cam = None


camera = Camera()

# ---------- Helpers ----------
def _iso_now():
    return datetime.now().isoformat(timespec="milliseconds")

def _seq_number():
    pat = re.compile(r"^(\d{3})_\d{14}\.csv$")
    highest = 0
    for f in DATA_DIR.glob("*.csv"):
        m = pat.match(f.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return highest + 1

def _emit_if_ready():
    with lock:
        if got_flag["x"] and got_flag["y"] and got_flag["z"]:
            x, y, z = latest_vals["x"], latest_vals["y"], latest_vals["z"]
            append_point(datetime.now().strftime("%H:%M:%S.%f")[:-3], x, y, z)
            row = (_iso_now(), x, y, z)
            global buf_start
            with buf_lock:
                if buf_start is None:
                    buf_start = datetime.now()
                buf.append(row)
            got_flag.update({"x": False, "y": False, "z": False})

def _append_annotation(stem: str, label=""):
    first_write = not ANNOT_FILE.exists()
    with ANNOT_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if first_write:
            w.writerow(["filename", "label"])
        w.writerow([stem, label])

def save_window(reason="auto"):
    with buf_lock:
        n = len(buf)
        if n < MIN_ROWS:
            return f"[{reason}] skipped: only {n} samples", None
        rows = buf[:]
        buf.clear()
        global buf_start
        buf_start = None

    seq = _seq_number()
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stem = f"{seq:03d}_{stamp}"
    base = DATA_DIR / stem

    # CSV
    csv_path = base.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "x", "y", "z"])
        w.writerows(rows)

    # Plot
    fig = go.Figure()
    ts, xs, ys, zs = zip(*rows)
    fig.add_scatter(x=ts, y=xs, mode="lines", name="X")
    fig.add_scatter(x=ts, y=ys, mode="lines", name="Y")
    fig.add_scatter(x=ts, y=zs, mode="lines", name="Z")
    fig.update_layout(template="plotly_white", title=stem, margin=dict(l=40,r=20,t=40,b=40))
    try:
        png = base.with_suffix(".png")
        fig.write_image(str(png))
        art_path = png
    except Exception:
        html_path = base.with_suffix(".html")
        fig.write_html(str(html_path))
        art_path = html_path

    # Webcam
    img = camera.snap(base)

    # Annotation row
    _append_annotation(stem)

    msg = f"[{reason}] {len(rows)} rows saved as {csv_path.name}, chart={art_path.name}, img={'yes' if img else 'no'}"
    print(msg)
    return msg, img

# ---------- Cloud bindings ----------
def on_x(_c, v):
    with lock:
        latest_vals["x"] = float(v) if v else None
        got_flag["x"] = True
        _emit_if_ready()

def on_y(_c, v):
    with lock:
        latest_vals["y"] = float(v) if v else None
        got_flag["y"] = True
        _emit_if_ready()

def on_z(_c, v):
    with lock:
        latest_vals["z"] = float(v) if v else None
        got_flag["z"] = True
        _emit_if_ready()

def start_cloud():
    client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY)
    client.register(VAR_X, value=None, on_write=on_x)
    client.register(VAR_Y, value=None, on_write=on_y)
    client.register(VAR_Z, value=None, on_write=on_z)
    th = threading.Thread(target=client.start, daemon=True)
    th.start()

# ---------- Autosave thread ----------
def start_autosave():
    def run():
        while True:
            time.sleep(1)
            with buf_lock:
                start, n = buf_start, len(buf)
            if start and n > 0 and datetime.now() - start >= timedelta(seconds=WINDOW_DURATION):
                save_window("timer")
    th = threading.Thread(target=run, daemon=True)
    th.start()

# ---------- Dash callbacks ----------
@app.callback(
    Output("save-status", "children"),
    Input("save-btn", "n_clicks"),
    prevent_initial_call=True
)
def cb_manual_save(_):
    msg, _ = save_window("manual")
    return msg

@app.callback(
    Output("save-status", "title"),
    Output("preview-img", "src"),
    Input("buf-check", "n_intervals")
)
def cb_peek(_i):
    with buf_lock:
        n, start = len(buf), buf_start
    if start:
        elapsed = (datetime.now() - start).total_seconds()
        status = f"{n} rows buffered | {elapsed:.1f}s elapsed"
    else:
        status = f"{n} rows buffered"

    # newest jpg
    try:
        latest_img = max(DATA_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, default=None)
    except Exception:
        latest_img = None
    if latest_img:
        v = int(latest_img.stat().st_mtime)
        src = f"/data2/{latest_img.name}?v={v}"
    else:
        src = no_update
    return status, src

# ---------- Main ----------
if __name__ == "__main__":
    print(f"[Init] Saving in {DATA_DIR}")
    if not OPENCV_OK:
        print("[Note] OpenCV missing → webcam capture disabled")
    start_cloud()
    start_autosave()
    app.run(host=HOST, port=PORT, debug=False)
