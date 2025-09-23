# gyro_dashboard.py
# SIT225 — Real-time Gyroscope Dashboard with Bokeh
# Run:
#   pip install bokeh pandas numpy
#   bokeh serve --show gyro_dashboard.py --args ./data
# Or provide a single CSV file path instead of a folder.

import sys
from pathlib import Path
import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, MultiSelect, TextInput, Button, Div, DataTable, TableColumn
from bokeh.plotting import figure

# ---------- Utility functions ----------
def csv_files_in_folder(folder: Path):
    if not folder.exists():
        return []
    return sorted(folder.glob("*.csv"), key=lambda f: f.stat().st_mtime)

def newest_csv(folder: Path):
    files = csv_files_in_folder(folder)
    return files[-1] if files else None

def read_csv_file(path: Path):
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        if "sample" not in df.columns:
            df["sample"] = np.arange(len(df))
        return df, f"Loaded: {path.name} ({len(df)} rows)"
    except Exception as e:
        return pd.DataFrame(), f"Failed to read {path}: {e}"

def numeric_columns(df: pd.DataFrame):
    preferred = [c for c in ["gyro_x", "gyro_y", "gyro_z"] if c in df.columns]
    if preferred:
        return preferred
    return [c for c in df.select_dtypes(include=[np.number]).columns if c != "sample"]

def clamp_value(value, low, high):
    return max(low, min(int(value), high))

# ---------- App Initialization ----------
args = sys.argv[1:]
folder_watch = None
csv_file = None

if args:
    p = Path(args[0])
    if p.is_dir():
        folder_watch = p
    else:
        csv_file = p
if not folder_watch and not csv_file:
    folder_watch = Path("./data")

# Load initial data
data_df = pd.DataFrame()
status_info = "No data loaded."

if csv_file:
    data_df, status_info = read_csv_file(csv_file)
else:
    newest = newest_csv(folder_watch)
    if newest:
        data_df, status_info = read_csv_file(newest)

if data_df.empty:
    data_df = pd.DataFrame({"sample": [], "gyro_x": [], "gyro_y": [], "gyro_z": []})

default_axes = numeric_columns(data_df)
start_index = 0
default_window = min(200, len(data_df) or 200)

# ---------- Widgets ----------
title_div = Div(text="<h2>Gyroscope Dashboard</h2>")
data_label = Div(text=f"<b>Data source:</b> {status_info}")

chart_type_select = Select(title="Chart type", value="Line", options=["Line", "Scatter", "Histogram"])
axes_select = MultiSelect(title="Axes", value=default_axes, options=default_axes, size=4)
sample_input = TextInput(title="Number of samples", value=str(default_window))

btn_prev = Button(label="Previous")
btn_next = Button(label="Next")

summary_source = ColumnDataSource(dict(axis=[], mean=[], std=[], min=[], max=[]))
summary_table = DataTable(
    source=summary_source,
    columns=[TableColumn(field=f, title=f) for f in ["axis", "mean", "std", "min", "max"]],
    width=600,
    height=200,
    index_position=None
)

plot = figure(height=350, sizing_mode="stretch_width", x_axis_label="Sample", y_axis_label="Reading")
active_renderers = []

# ---------- Logic ----------
def get_window_size():
    try:
        return max(10, int(sample_input.value))
    except Exception:
        return 200

def get_window_indices():
    global start_index
    n = get_window_size()
    L = len(data_df)
    start = clamp_value(start_index, 0, max(0, L - 1))
    end = clamp_value(start + n, 1, L)
    return start, end

def refresh_axes_options():
    options = numeric_columns(data_df)
    axes_select.options = options
    if not axes_select.value or any(a not in options for a in axes_select.value):
        axes_select.value = options

def update_summary_table(window_df: pd.DataFrame, axes: list[str]):
    if window_df.empty or not axes:
        summary_source.data = dict(axis=[], mean=[], std=[], min=[], max=[])
        return
    stats = window_df[axes].agg(["mean", "std", "min", "max"]).T.reset_index().rename(columns={"index": "axis"})
    for col in ["mean", "std", "min", "max"]:
        stats[col] = stats[col].round(4)
    summary_source.data = stats.to_dict(orient="list")

def clear_renderers():
    for r in list(active_renderers):
        try:
            plot.renderers.remove(r)
        except Exception:
            pass
        active_renderers.remove(r)

def draw_chart():
    clear_renderers()
    axes = list(axes_select.value)
    start, end = get_window_indices()
    window_df = data_df.iloc[start:end].copy()

    if chart_type_select.value in ("Line", "Scatter"):
        for axis in axes:
            src = ColumnDataSource(dict(sample=window_df["sample"], value=window_df[axis]))
            if chart_type_select.value == "Line":
                r = plot.line(x="sample", y="value", source=src, legend_label=axis)
            else:
                r = plot.circle(x="sample", y="value", source=src, legend_label=axis, size=5)
            active_renderers.append(r)
        plot.xaxis.axis_label = "Sample"
        plot.yaxis.axis_label = "Reading"
    else:  # Histogram
        for axis in axes:
            vals = window_df[axis].dropna().values
            if len(vals) == 0:
                continue
            hist, edges = np.histogram(vals, bins=30)
            src = ColumnDataSource(dict(top=hist, left=edges[:-1], right=edges[1:]))
            r = plot.quad(top="top", bottom=0, left="left", right="right", alpha=0.5, source=src, legend_label=axis)
            active_renderers.append(r)
        plot.xaxis.axis_label = "Reading bins"
        plot.yaxis.axis_label = "Count"

    plot.legend.visible = True
    update_summary_table(window_df, axes)

def prev_window():
    global start_index
    start_index = max(0, start_index - get_window_size())
    draw_chart()

def next_window():
    global start_index
    n = get_window_size()
    L = len(data_df)
    start_index = min(max(0, L - n), start_index + n)
    draw_chart()

btn_prev.on_click(prev_window)
btn_next.on_click(next_window)

def controls_updated(attr, old, new):
    draw_chart()

chart_type_select.on_change("value", controls_updated)
axes_select.on_change("value", controls_updated)
sample_input.on_change("value", controls_updated)

def check_for_new_data():
    global data_df, status_info, start_index
    if csv_file:
        return
    latest = newest_csv(folder_watch)
    if not latest:
        return
    last_name = getattr(curdoc(), "_last_file", None)
    last_mtime = getattr(curdoc(), "_last_mtime", 0.0)
    if latest.name != last_name or latest.stat().st_mtime > last_mtime:
        new_df, info = read_csv_file(latest)
        if not new_df.empty:
            data_df = new_df
            status_info = info
            curdoc()._last_file = latest.name
            curdoc()._last_mtime = latest.stat().st_mtime
            refresh_axes_options()
            start_index = max(0, len(data_df) - get_window_size())
            data_label.text = f"<b>Data source:</b> {status_info}"
            draw_chart()

# ---------- Initial Rendering ----------
refresh_axes_options()
draw_chart()

controls_layout = column(chart_type_select, axes_select, sample_input, row(btn_prev, btn_next), width=350)
main_layout = row(controls_layout, column(data_label, plot, Div(text="<b>Summary (current window)</b>"), summary_table),
                  sizing_mode="stretch_width")
curdoc().add_root(column(title_div, main_layout))

curdoc().add_periodic_callback(check_for_new_data, 10_000)
