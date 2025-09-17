# smoothdash_rewrite.py
"""
SIT225 8.2C — Smooth live streaming helper for Plotly Dash

Purpose:
Normally, Dash redraws the entire figure each update, causing visible jumps.
This module uses Graph.extendData to append small batches of points, keeping
a sliding window for each channel, producing smooth real-time updates.

Usage:
    app, state = create_smooth_dash(
        channels=["X","Y","Z"],
        window_size=600,   # visible points per series
        step_size=20,      # max points appended per interval
        refresh_ms=200     # update period in ms
    )
    state["push"](timestamp, *values)  # thread-safe insertion
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import List

import plotly.graph_objects as go
from dash import Dash, dcc, html, Output, Input, no_update


@dataclass
class _StreamBuffer:
    queue: deque       # tuples of (timestamp, val1, val2, ...)
    lock: Lock
    num_channels: int


def create_smooth_dash(
    channels: List[str],
    window_size: int = 600,
    step_size: int = 20,
    refresh_ms: int = 200,
):
    """
    Builds a Dash app configured for smooth streaming using extendData.
    Returns (app, state) where state["push"] appends a sample to the internal queue.
    """
    num_ch = len(channels)
    buf = _StreamBuffer(deque(), Lock(), num_ch)

    # --- Initialize figure ---
    fig = go.Figure()
    for ch in channels:
        fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name=ch))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title="Time",
        yaxis_title="Value",
        legend=dict(orientation="h", x=1, y=1.02, xanchor="right", yanchor="bottom"),
        uirevision=True,  # maintain zoom/axis while updating
        title="Live Stream (Smooth)",
    )

    # --- Dash layout ---
    app = Dash(__name__)
    app.layout = html.Div(
        style={"fontFamily": "system-ui, Segoe UI, Roboto, Arial", "padding": "12px"},
        children=[
            html.H2("Smooth Live Stream"),
            html.Div(id="info", style={"marginBottom": "8px"}),
            dcc.Graph(id="graph", figure=fig),
            dcc.Interval(id="interval", interval=refresh_ms, n_intervals=0),
        ],
    )

    # --- Callback for updating graph ---
    @app.callback(
        Output("graph", "extendData"),
        Output("info", "children"),
        Input("interval", "n_intervals"),
        prevent_initial_call=False,
    )
    def _update(_):
        with buf.lock:
            if not buf.queue:
                return no_update, "Waiting… inbox=0"
            batch = [buf.queue.popleft() for _ in range(min(len(buf.queue), step_size))]

        timestamps = [row[0] for row in batch]
        per_channel = [[] for _ in range(buf.num_channels)]
        for _, *vals in batch:
            for idx, val in enumerate(vals):
                per_channel[idx].append(val)

        extend_data = {"x": [timestamps]*buf.num_channels, "y": per_channel}
        trace_ids = list(range(buf.num_channels))
        return (extend_data, trace_ids, window_size), f"Appended {len(timestamps)} | inbox={len(buf.queue)}"

    # --- Thread-safe push method ---
    def _push(timestamp, *vals):
        if len(vals) != num_ch:
            raise ValueError(f"Expected {num_ch} values, got {len(vals)}")
        with buf.lock:
            buf.queue.append((timestamp, *vals))

    state = {
        "push": _push,
        "channels": channels,
        "window_size": window_size,
        "step_size": step_size,
        "refresh_ms": refresh_ms,
    }
    return app, state
