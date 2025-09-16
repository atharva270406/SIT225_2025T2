# smoothdash_alt.py
"""
SIT225 8.2C — Smooth streaming Dash helper

Dash figures normally redraw completely at each update → can appear jumpy.
This wrapper instead uses Graph.extendData, appending only small slices of new
points (like animation frames). A sliding window keeps recent history visible.

Usage:
    app, state = build_smooth_dash(
        channels=["X", "Y", "Z"],
        window_len=600,   # points retained per series
        max_step=20,      # max appended points per frame
        refresh_ms=200    # UI update rate in ms
    )
    state["push"](timestamp_str, *values)   # thread-safe insert
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import List

import plotly.graph_objects as go
from dash import Dash, dcc, html, Output, Input, no_update


@dataclass
class _Buffer:
    q: deque            # stores tuples: (t, v1, v2, ...)
    lock: Lock
    n_series: int


def build_smooth_dash(
    channels: List[str],
    window_len: int = 600,
    max_step: int = 20,
    refresh_ms: int = 200,
):
    """
    Construct a Dash app configured for smooth streaming.
    Returns (app, state), where state["push"] is the producer entrypoint.
    """
    n = len(channels)
    buf = _Buffer(deque(), Lock(), n)

    # --- Initial empty figure scaffold ---
    base_fig = go.Figure()
    for ch in channels:
        base_fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name=ch))
    base_fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title="Time",
        yaxis_title="Value",
        title="Live Stream (smooth)",
        uirevision=True,
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )

    # --- Dash app layout ---
    app = Dash(__name__)
    app.layout = html.Div(
        style={"fontFamily": "system-ui, Segoe UI, Roboto, Arial", "padding": "12px"},
        children=[
            html.H2("Smooth Live Stream"),
            html.Div(id="info", style={"marginBottom": "8px"}),
            dcc.Graph(id="plot", figure=base_fig),
            dcc.Interval(id="timer", interval=refresh_ms, n_intervals=0),
        ],
    )

    # --- Periodic update ---
    @app.callback(
        Output("plot", "extendData"),
        Output("info", "children"),
        Input("timer", "n_intervals"),
        prevent_initial_call=False,
    )
    def _tick(_n):
        # Pull up to max_step samples
        with buf.lock:
            if not buf.q:
                return no_update, "Waiting... inbox=0"
            items = [buf.q.popleft() for _ in range(min(len(buf.q), max_step))]

        times = [r[0] for r in items]
        per_series = [[] for _ in range(buf.n_series)]
        for _, *vals in items:
            for i, v in enumerate(vals):
                per_series[i].append(v)

        extend_obj = {"x": [times] * buf.n_series, "y": per_series}
        traces = list(range(buf.n_series))
        return (extend_obj, traces, window_len), f"Appended {len(times)} | inbox={len(buf.q)}"

    # --- Producer method ---
    def _push(t, *vals):
        if len(vals) != n:
            raise ValueError(f"Expected {n} values, got {len(vals)}")
        with buf.lock:
            buf.q.append((t, *vals))

    state = {
        "push": _push,
        "channels": channels,
        "window_len": window_len,
        "max_step": max_step,
        "refresh_ms": refresh_ms,
    }
    return app, state
