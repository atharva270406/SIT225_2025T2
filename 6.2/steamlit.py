# streamlit_gyro_dashboard.py
# Streamlit-based Gyroscope Dashboard with robust folder/file watch
from pathlib import Path
import time
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Gyroscope Dashboard", layout="wide")
st.write("✅ Dashboard initialized")

# ---------- Utility Functions ----------
def get_csv_files(folder: Path):
    try:
        return sorted(folder.glob("*.csv"), key=lambda f: f.stat().st_mtime)
    except Exception:
        return []

def newest_csv(folder: Path):
    files = get_csv_files(folder)
    return files[-1] if files else None

def read_csv(path):
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        if "sample" not in df.columns:
            df["sample"] = np.arange(len(df))
        return df
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        return pd.DataFrame()

def numeric_columns(df: pd.DataFrame):
    preferred = [c for c in ["gyro_x", "gyro_y", "gyro_z"] if c in df.columns]
    if preferred:
        return preferred
    return [c for c in df.select_dtypes(include=[np.number]).columns if c != "sample"]

def clamp_value(val, lo, hi):
    return max(lo, min(int(val), hi))

# ---------- Sidebar Controls ----------
st.sidebar.title("Controls")
source_mode = st.sidebar.radio("Data source", ["Upload CSV file", "Watch folder"], index=1)

uploaded_df = pd.DataFrame()
watched_df = pd.DataFrame()
file_info_text = ""

# --- Upload CSV mode ---
if source_mode == "Upload CSV file":
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        uploaded_df = read_csv(uploaded_file)
        file_info_text = f"Uploaded: {uploaded_file.name}"

# --- Watch folder mode ---
else:
    default_path = str((Path.cwd() / "data").resolve())
    folder_input = st.sidebar.text_input("Folder to monitor", value=default_path)
    folder_path = Path(folder_input.strip().strip('"').strip("'"))
    st.sidebar.caption(f"Monitoring: {folder_path}")
    st.write({
        "folder_exists": folder_path.exists(),
        "csv_count": len(list(folder_path.glob("*.csv")))
    })

    if not folder_path.exists():
        st.warning("Folder not found. Check path above.")
    latest_file = newest_csv(folder_path)
    if latest_file:
        file_info_text = f"Watching: {folder_path} • Latest: {latest_file.name}"
        watched_df = read_csv(latest_file)
    else:
        st.warning("No CSV files detected yet.")
        watched_df = pd.DataFrame()

# Determine which dataframe to use
df = uploaded_df if source_mode == "Upload CSV file" else watched_df

# Preview / Debug section
with st.expander("Data preview / status", expanded=True):
    st.write("File info:", file_info_text or "(none)")
    st.write("Data shape:", df.shape)
    if not df.empty:
        st.dataframe(df.head(10))
    else:
        st.info("No data available. Upload or provide a folder containing CSVs.")

if df.empty:
    st.stop()

# ---------- Plotting Controls ----------
chart_choice = st.sidebar.selectbox("Chart type", ["Line", "Scatter", "Histogram"], index=0)

axes_list = numeric_columns(df)
if not axes_list:
    st.error("No numeric columns found for plotting.")
    st.stop()

selected_axes = st.sidebar.multiselect("Axes to display", axes_list, default=axes_list)
if not selected_axes:
    st.warning("Select at least one axis.")
    st.stop()

# ---------- Windowing ----------
if "start_index" not in st.session_state:
    st.session_state.start_index = 0
if "window_size" not in st.session_state:
    st.session_state.window_size = min(200, len(df))

win_size = st.sidebar.number_input(
    "Number of samples (N)",
    min_value=10,
    max_value=int(len(df)),
    value=min(200, len(df)),
    step=10
)
st.session_state.window_size = int(win_size)

col_prev, col_next = st.sidebar.columns(2)
if col_prev.button("Previous"):
    st.session_state.start_index = max(0, st.session_state.start_index - st.session_state.window_size)
if col_next.button("Next"):
    st.session_state.start_index = min(max(0, len(df) - st.session_state.window_size),
                                       st.session_state.start_index + st.session_state.window_size)

start_idx = clamp_value(st.session_state.start_index, 0, max(0, len(df) - 1))
end_idx = clamp_value(start_idx + st.session_state.window_size, 1, len(df))
window_df = df.iloc[start_idx:end_idx].copy()

# ---------- Layout ----------
st.title("Gyroscope Dashboard — Streamlit")
st.caption("Navigate through N-sample windows or watch a folder for new CSV files.")

col_metrics = st.columns(3)
col_metrics[0].metric("Total rows", len(df))
col_metrics[1].metric("Window size", st.session_state.window_size)
col_metrics[2].metric("Window range", f"{start_idx}–{end_idx-1}")

if file_info_text:
    st.markdown(f"**Data source:** {file_info_text}")

# Prepare data for Altair (long format)
plot_df = window_df.reset_index(drop=True).reset_index().rename(columns={"index": "sample_idx"})
plot_df = plot_df.melt(id_vars=["sample_idx"], value_vars=selected_axes, var_name="axis", value_name="value")

# ---------- Plot ----------
if chart_choice == "Line":
    chart = alt.Chart(plot_df).mark_line().encode(
        x="sample_idx:Q",
        y="value:Q",
        color="axis:N",
        tooltip=["axis:N", "sample_idx:Q", "value:Q"]
    ).properties(height=350)
elif chart_choice == "Scatter":
    chart = alt.Chart(plot_df).mark_circle(size=30).encode(
        x="sample_idx:Q",
        y="value:Q",
        color="axis:N",
        tooltip=["axis:N", "sample_idx:Q", "value:Q"]
    ).properties(height=350)
else:  # Histogram
    chart = alt.Chart(plot_df).mark_bar(opacity=0.7).encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=40), title="Reading bins"),
        y=alt.Y("count():Q", title="Count"),
        color="axis:N",
        tooltip=["axis:N", "count():Q"]
    ).properties(height=350)

st.altair_chart(chart, use_container_width=True)

# ---------- Summary Table ----------
st.subheader("Summary for current window")
summary_df = window_df[selected_axes].agg(["count", "mean", "std", "min", "max"]).T.reset_index().rename(columns={"index": "axis"})
summary_df["mean"] = summary_df["mean"].round(4)
summary_df["std"] = summary_df["std"].round(4)
st.dataframe(summary_df, hide_index=True)

# ---------- Auto-refresh (watch folder mode) ----------
if source_mode == "Watch folder" and st.sidebar.checkbox("Auto-refresh every 10s", value=True):
    st.sidebar.caption("Auto-refresh enabled")
    time.sleep(10)
    st.experimental_rerun()
