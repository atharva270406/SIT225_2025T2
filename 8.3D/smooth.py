# streamdash.py
"""
Smooth real-time streaming in Plotly Dash (SIT225 Task 8.2C)

This helper creates a Dash app that updates line graphs smoothly.
Instead of redrawing entire figures, it appends new points in small chunks
to mimic a "video frame" effect.
"""

from collections import deque
from threading import Lock
from typing import List, Tuple

import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, no_update


class SharedBuffer:
    """Thread-safe buffer to store incoming sensor samples."""
    def __init__(self, n_channels: int):
        self._queue: deque[Tuple] = deque()
        self._lock = Lock()
        self.n_channels = n_channels

    def put(self, row: Tuple):
        with self._lock:
            self._queue.append(row)

    def get_batch(self, max_items: int):
        """Retrieve up to max_items from the buffer."""
        with self._lock:
            items = []
            for _ in range(min(len(self._queue), max_items)):
                items.append(self._queue.popleft())
            return items, len(self._queue)


def create_stream_app(
    channels: List[str],
    window_size: int = 500,
    batch_limit: int = 15,
    refresh_ms: int = 250,
):
    """
    Build and return a Dash app for smooth live plotting.
    Returns (app, state) where state["add_sample"](t, *values) can be used
    to push new points into the graph.
    """
    buffer = SharedBuffer(len(channels))

    # Initial blank figure
    fig = go.Figure()
    for ch in channels:
        fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name=ch))

    fig.update_layout(
        template="plotly_white",
        title="Streaming Dashboard",
        xaxis_title="Time",
        yaxis_title="Reading",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right"),
        uirevision="fixed",  # prevent reset on zoom/pan
    )

    app = Dash(__name__)
    app.layout = html.Div(
        style={"fontFamily": "Segoe UI, Roboto, Arial", "padding": "10px"},
        children=[
            html.H3("Live Data Stream (Smooth Updates)"),
            html.Div(id="status"),
            dcc.Graph(id="live-plot", figure=fig),
            dcc.Interval(id="timer", interval=refresh_ms, n_intervals=0),
        ],
    )

    @app.callback(
        Output("live-plot", "extendData"),
        Output("status", "children"),
        Input("timer", "n_intervals"),
        prevent_initial_call=False,
    )
    def update(_):
        rows, remaining = buffer.get_batch(batch_limit)
        if not rows:
            return no_update, f"Waiting for data... (buffer empty)"

        # Split timestamps and channel values
        times = [r[0] for r in rows]
        per_channel = [[] for _ in range(buffer.n_channels)]
        for _, *vals in rows:
            for i, v in enumerate(vals):
                per_channel[i].append(v)

        extend_dict = {"x": [times] * buffer.n_channels, "y": per_channel}
        indices = list(range(buffer.n_channels))

        return (extend_dict, indices, window_size), f"Added {len(times)} samples | buffer={remaining}"

    # External API for producers
    def add_sample(t, *values):
        if len(values) != buffer.n_channels:
            raise ValueError(f"Expected {buffer.n_channels} values, got {len(values)}")
        buffer.put((t, *values))

    state = {
        "add_sample": add_sample,
        "channels": channels,
        "window_size": window_size,
        "batch_limit": batch_limit,
        "refresh_ms": refresh_ms,
    }
    return app, state
