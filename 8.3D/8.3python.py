# task8_3d_capture_and_dash_refactored.py
# SIT225 8.3D — Smooth live Dash + 10s window saving with matched webcam image

from datetime import datetime, timedelta
from pathlib import Path
import threading, time, csv, re

# 3rd party libs
from arduino_iot_cloud import ArduinoCloudClient
from iot_secrets import DEVICE_ID, SECRET_KEY
from smoothdash import make_smooth_app
from dash import html, dcc, Output, Input, no_update
import plotly.graph_objects as go

# Webcam
try:
    import cv2
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

# ---------- User settings ----------
VAR_X, VAR_Y, VAR_Z = "accelerometer_x", "accelerometer_y", "accelerometer_z"
WINDOW_SEC, MIN_SAMPLES_PER_WINDOW = 10, 15
OUTPUT_PREFIX = ""
HOST, PORT = "127.0.0.1", 8050

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data 2"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ANNOT_PATH = DATA_DIR / "annotations.csv"

# ---------- Smooth Dash app ----------
WINDOW_POINTS, MAX_APPEND, POLL_MS = 800, 20, 120
app, state = make_smooth_app(["X", "Y", "Z"], window_points=WINDOW_POINTS, max_append=MAX_APPEND, poll_ms=POLL_MS)
push = state["push"]

# Serve files from ./data 2
from flask import send_from_directory
@app.server.route("/data2/<path:filename>")
def serve_file(filename): return send_from_directory(DATA_DIR, filename, as_attachment=False)

# Extend layout with controls
_controls = html.Div([
    html.Div([
        html.Button("Force Save Now", id="force-save", n_clicks=0, style={"marginRight": "12px"}),
        html.Span("Status: "), html.Span(id="save-status", children="Waiting for data…"),
        dcc.Interval(id="buf-peek", interval=3000, n_intervals=0)
    ], style={"padding":"8px 12px","borderTop":"1px solid #ddd","marginTop":"8px"}),
    html.Div([
        html.H4("Latest window image"),
        html.Img(id="latest-img", src="", style={"maxWidth":"100%","border":"1px solid #eee","borderRadius":"8px"})
    ], style={"padding":"8px 12px"})
])
app.layout = html.Div([*app.layout.children, _controls]) if hasattr(app.layout, "children") else html.Div([app.layout, _controls])

# ---------- Data buffers ----------
latest = {"x": None, "y": None, "z": None}
seen = {"x": False, "y": False, "z": False}
lock, buf_lock, cam_lock = threading.Lock(), threading.Lock(), threading.Lock()
buf_rows, buf_start_ts = [], None
_cam = None

# ---------- Helper functions ----------
def _open_cam():
    global _cam
    if _cam: return True
    if not OPENCV_OK: return False
    try:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
        ok, _ = cam.read()
        if not ok: cam.release(); return False
        _cam = cam; return True
    except: return False

def _close_cam():
    global _cam
    if _cam: _cam.release(); _cam = None

def _ts_stamp(fmt="%Y%m%d%H%M%S"): return datetime.now().strftime(fmt)
def _iso_ms_now(): return datetime.now().isoformat(timespec="milliseconds")

def _next_seq_number():
    pat = re.compile(r"^(\d{3})_\d{14}\.csv$")
    max_seq = 0
    for p in DATA_DIR.glob("*.csv"):
        m = pat.match(p.name)
        if m: max_seq = max(max_seq, int(m.group(1)))
    return max_seq + 1

def _emit_if_ready_unlocked():
    if all(seen.values()):
        x, y, z = latest["x"], latest["y"], latest["z"]
        ts_hms = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        push(ts_hms, x, y, z)
        with buf_lock:
            global buf_start_ts
            if buf_start_ts is None: buf_start_ts = datetime.now()
            buf_rows.append((_iso_ms_now(), x, y, z))
        for k in seen: seen[k] = False

# ---------- Cloud callbacks ----------
def on_x(_client, v): 
    with lock: latest["x"], seen["x"] = float(v) if v is not None else None, True; _emit_if_ready_unlocked()
def on_y(_client, v): 
    with lock: latest["y"], seen["y"] = float(v) if v is not None else None, True; _emit_if_ready_unlocked()
def on_z(_client, v): 
    with lock: latest["z"], seen["z"] = float(v) if v is not None else None, True; _emit_if_ready_unlocked()

def start_cloud_thread():
    client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY)
    for var, cb in zip([VAR_X, VAR_Y, VAR_Z], [on_x, on_y, on_z]): client.register(var, value=None, on_write=cb)
    th = threading.Thread(target=lambda: (print("[Cloud] Connecting…"), client.start()), daemon=True)
    th.start()
    return th

# ---------- Saving ----------
def _save_csv(rows, base_path: Path):
    path = base_path.with_suffix(".csv")
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["timestamp","x","y","z"]] + rows)
    return path

def _save_plot(rows, base_path: Path):
    fig = go.Figure()
    ts, xs, ys, zs = zip(*rows)
    for val, name in zip([xs, ys, zs], ["X","Y","Z"]): fig.add_scatter(x=ts, y=val, mode="lines", name=name)
    fig.update_layout(title=f"Accelerometer window — {base_path.stem}", xaxis_title="time", yaxis_title="accel",
                      margin=dict(l=40,r=20,t=50,b=40), legend=dict(orientation="h", y=1.02, x=0), template="plotly_white")
    try: 
        path = base_path.with_suffix(".png"); fig.write_image(str(path), width=1200, height=500, scale=2); return "png", path
    except: 
        path = base_path.with_suffix(".html"); fig.write_html(str(path), include_plotlyjs="cdn"); return "html", path

def _save_image(base_path: Path):
    if not OPENCV_OK: return None
    with cam_lock:
        if not _open_cam(): return None
        ok, frame = _cam.read()
        if not ok or frame is None: return None
        path = base_path.with_suffix(".jpg"); cv2.imwrite(str(path), frame); return path

def _append_annotation_row(filename_stem: str, label: str=""):
    write_header = not ANNOT_PATH.exists()
    with ANNOT_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header: w.writerow(["filename","label"])
        w.writerow([filename_stem, label])

def _flush_window(save_reason="auto"):
    global buf_start_ts
    with buf_lock:
        if len(buf_rows) < MIN_SAMPLES_PER_WINDOW: return f"[Save:{save_reason}] Skipped: only {len(buf_rows)} samples", None
        rows, buf_rows[:] = buf_rows[:], []
        buf_start_ts = None
    seq, ts = _next_seq_number(), _ts_stamp()
    stem, base = f"{seq:03d}_{ts}", DATA_DIR / (OUTPUT_PREFIX + f"{seq:03d}_{ts}")
    csv_path = _save_csv(rows, base)
    kind, art_path = _save_plot(rows, base)
    img_path = _save_image(base)
    _append_annotation_row(stem)
    msg = f"[Save:{save_reason}] {len(rows)} samples | CSV -> {csv_path.name} | {kind.upper()} -> {art_path.name}"
    msg += f" | IMG -> {img_path.name}" if img_path else " | IMG -> (skipped)"
    print(msg)
    return msg, img_path

def start_autosave_thread():
    def run():
        while True:
            time.sleep(1)
            with buf_lock:
                n, start_ts = len(buf_rows), buf_start_ts
            if start_ts and n > 0 and datetime.now() - start_ts >= timedelta(seconds=WINDOW_SEC): _flush_window("time")
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th

# ---------- Dash callbacks ----------
@app.callback(Output("save-status", "children"), Input("force-save", "n_clicks"), prevent_initial_call=True)
def cb_force_save(_): return _flush_window("manual")[0]

@app.callback(Output("save-status", "title"), Output("latest-img", "src"), Input("buf-peek", "n_intervals"))
def cb_peek(_):
    with buf_lock:
        n, start_ts = len(buf_rows), buf_start_ts
    status = f"Buffered: {n} rows | {((datetime.now()-start_ts).total_seconds() if start_ts else 0):.1f}s" if start_ts else f"Buffered: {n} rows"
    newest = max(DATA_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, default=None)
    img_src = f"/data2/{newest.name}?v={int(newest.stat().st_mtime)}" if newest else no_update
    return status, img_src

# ---------- Main ----------
if __name__ == "__main__":
    try:
        print(f"[Init] Output dir: {DATA_DIR}")
        if not OPENCV_OK: print("[Warn] OpenCV not installed. Install with: pip install opencv-python")
        start_cloud_thread()
        start_autosave_thread()
        print(f"[Run] Dash at http://{HOST}:{PORT}")
        app.run(debug=False, host=HOST, port=PORT)
    finally:
        _close_cam()
