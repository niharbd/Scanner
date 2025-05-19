import streamlit as st
import pandas as pd
import json
import os
import subprocess
from datetime import datetime

st.set_page_config(page_title="Nihar's Dream Project", layout="wide")

# Title block
st.title("📊 Nihar's Dream Project")

# Spinner animation shared for all scan modes
spinner_html = """
<div style='display: flex; gap: 3px; justify-content: flex-start; margin-top: 1em;'>
  <div style='width: 5px; height: 20px; background: #e74c3c; animation: flicker 1s infinite;'></div>
  <div style='width: 5px; height: 20px; background: #2ecc71; animation: flicker 1s infinite 0.2s;'></div>
  <div style='width: 5px; height: 20px; background: #e74c3c; animation: flicker 1s infinite 0.4s;'></div>
</div>
<style>
@keyframes flicker {
  0% { opacity: 0.3; transform: scaleY(0.9); }
  50% { opacity: 1; transform: scaleY(1.2); }
  100% { opacity: 0.3; transform: scaleY(0.9); }
}
</style>
"""

# Session state
if "scan_ran" not in st.session_state:
    st.session_state.scan_ran = False
if "scanning" not in st.session_state:
    st.session_state.scanning = False
if "initial_scan_done" not in st.session_state:
    st.session_state.initial_scan_done = False

# Auto scan on first load
if not st.session_state.initial_scan_done:
    st.session_state.scanning = True
    st.session_state.initial_scan_done = True
    placeholder = st.empty()
    placeholder.markdown(spinner_html, unsafe_allow_html=True)
    try:
        subprocess.call(["python", "scanner_writer.py"])
        st.session_state.scan_ran = True
    except Exception as e:
        st.error(f"❌ Auto scan failed: {e}")
    st.session_state.scanning = False
    placeholder.empty()

# Manual scan trigger
if st.button("🔄 Run Scanner Now"):
    st.session_state.scanning = True
    placeholder = st.empty()
    placeholder.markdown(spinner_html, unsafe_allow_html=True)
    try:
        subprocess.call(["python", "scanner_writer.py"])
        st.session_state.scan_ran = True
    except Exception as e:
        st.error(f"❌ Scanner failed: {e}")
    st.session_state.scanning = False
    placeholder.empty()

# Load signal data and meta
live_signals = []
meta = {}
if os.path.exists("signals.json") and st.session_state.scan_ran:
    with open("signals.json", "r") as f:
        content = json.load(f)
        if isinstance(content, dict):
            live_signals = content.get("signals", [])
            meta = content.get("meta", {})

# Load history
history_df = pd.read_csv("signals_log.csv") if os.path.exists("signals_log.csv") else pd.DataFrame()

# Scan metrics
if st.session_state.scan_ran and meta:
    scan_time = meta.get("timestamp", "")
    total_signals = meta.get("generated", 0)
    total_scanned = meta.get("total_scanned", 0)
    total_rejected = total_scanned - total_signals
    avg_confidence = meta.get("avg_confidence", 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🕒 Last Scan (BST)", scan_time)
    col2.metric("📈 Signals", f"{total_signals} / {total_scanned}")
    col3.metric("❌ Rejected", total_rejected)
    col4.metric("🤖 Avg. Confidence", f"{avg_confidence:.2f}%")

# Tab layout
tabs = st.tabs(["📡 Live Signals", "📜 Signal History", "📈 Performance Report"])

# Tab 1: Live Signals
with tabs[0]:
    if live_signals:
        st.dataframe(pd.DataFrame(live_signals))
    else:
        st.info("No current signals. Awaiting next scan...")

# Tab 2: Signal History
with tabs[1]:
    if not history_df.empty:
        cols = ["Signal Time", "Coin", "Type", "Entry", "TPs", "SL", "Confidence", "result", "tp_hit"]
        if all(c in history_df.columns for c in cols):
            history_df = history_df[cols]
        if "Signal Time" in history_df.columns:
            history_df = history_df.sort_values("Signal Time", ascending=False)
        elif "signal_time" in history_df.columns:
            history_df = history_df.sort_values("signal_time", ascending=False)
        st.dataframe(history_df.reset_index(drop=True))
    else:
        st.info("No signal history yet.")

# Tab 3: Performance
with tabs[2]:
    if not history_df.empty:
        total = len(history_df)
        wins = len(history_df[history_df["result"] == 1])
        losses = len(history_df[history_df["result"] == 0])
        win_rate = (wins / total) * 100 if total else 0

        tp_counts = history_df["tp_hit"].value_counts().to_dict() if "tp_hit" in history_df.columns else {}

        st.metric("📌 Total Signals", total)
        st.metric("✅ TP Hit (Wins)", wins)
        st.metric("❌ SL Hit (Losses)", losses)
        st.metric("🎯 Win Rate", f"{win_rate:.2f}%")

        st.subheader("📊 TP Hit Breakdown")
        if tp_counts:
            for level in ["TP1", "TP2", "TP3", "TP4"]:
                st.write(f"{level}: {tp_counts.get(level, 0)}")
        else:
            st.info("No TP hits recorded yet.")
    else:
        st.info("No performance data yet.")
