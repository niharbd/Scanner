import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from scanner_writer import run_scanner
from tp_sl_tracker import track
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="📊 Nihar's Dream Project", layout="wide")
st.title("📊 Nihar's Dream Project")

# 🔄 Auto-refresh every 10 minutes
st_autorefresh(interval=600000, limit=None, key="refresh")

# Run scan on first page load
if "auto_scanned" not in st.session_state:
    st.session_state["auto_scanned"] = True
    with st.spinner("🔍 Auto scanning market..."):
        run_scanner()

st.sidebar.success("Use sidebar to navigate tabs")
TAB_OPTIONS = ["Live Signals", "Signal History", "Performance Report", "Scan Log"]
selected_tab = st.sidebar.radio("View Mode", TAB_OPTIONS)

SIGNAL_FILE = "signals.json"
LOG_FILE = "signals_log.csv"
ACTIVE_FILE = "active_signals.json"

def load_signals():
    if os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, "r") as f:
            return json.load(f)
    return {"signals": [], "meta": {}}

def load_history():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame()

signals_data = load_signals()
signal_df = pd.DataFrame(signals_data.get("signals", []))
history_df = load_history()

if selected_tab == "Live Signals":
    st.subheader("📡 Live Market Signals")
    meta = signals_data.get("meta", {})
    st.markdown(f"✅ Last Scan Time (BST): `{meta.get('timestamp', 'N/A')}`")
    st.markdown(f"📈 Valid Signals Detected: `{meta.get('generated', 0)} / {meta.get('total_scanned', 0)}`")
    st.markdown(f"🤖 Average Model Confidence: `{meta.get('avg_confidence', 0)}%`")

    if not signal_df.empty:
        st.dataframe(signal_df)
    else:
        st.info("No signals found. Please wait for next auto-scan.")

elif selected_tab == "Signal History":
    st.subheader("📜 Signal History Log")
    if not history_df.empty:
        st.dataframe(history_df.sort_values("Signal Time", ascending=False).reset_index(drop=True))
    else:
        st.info("No signal history available.")

elif selected_tab == "Performance Report":
    st.subheader("📈 Performance Tracker")
    if not history_df.empty:
        tp_counts = history_df["tp_hit"].value_counts().to_dict()
        result_counts = history_df["result"].value_counts().to_dict()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Signals", len(history_df))
            st.metric("TP Hits", result_counts.get(1, 0))
            st.metric("SL Hits", result_counts.get(0, 0))
        with col2:
            for i in range(1, 5):
                st.metric(f"TP{i} Hits", tp_counts.get(f"TP{i}", 0))
    else:
        st.info("No performance data available.")

elif selected_tab == "Scan Log":
    st.subheader("🔍 Coin Scan Log")
    if os.path.exists("scan_debug.json"):
        with open("scan_debug.json", "r") as f:
            debug_log = json.load(f)
        df_log = pd.DataFrame(debug_log)
        st.dataframe(df_log)
    else:
        st.info("Scan log not found. Run the scanner at least once.")
