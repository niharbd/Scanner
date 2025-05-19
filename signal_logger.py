import pandas as pd
import os

def log_signal(row, filename="signals_log.csv"):
    fields = [
        "symbol", "type", "entry", "tp1", "tp2", "tp3", "tp4", "sl",
        "ema_diff", "rsi", "macd_hist", "adx",
        "atr", "atr_ratio", "rvol", "confidence",
        "signal_time", "result"
    ]

    tps = row.get("TPs", [None, None, None, None])
    log_row = {
        "symbol": row["Coin"],
        "type": row["Type"],
        "entry": row["Entry"],
        "tp1": tps[0],
        "tp2": tps[1],
        "tp3": tps[2],
        "tp4": tps[3],
        "sl": row["SL"],
        "ema_diff": row.get("ema_diff", 0),
        "rsi": row.get("rsi", 0),
        "macd_hist": row.get("macd_hist", 0),
        "adx": row.get("adx", 0),
        "atr": row.get("atr", 0),
        "atr_ratio": row.get("atr_ratio", 0),
        "rvol": row.get("rvol", 0),
        "confidence": row["Confidence"],
        "signal_time": row["Signal Time"],
        "result": ""  # to be filled later (1 = TP hit, 0 = SL hit)
    }

    df_log = pd.DataFrame([log_row])
    if not os.path.exists(filename):
        df_log.to_csv(filename, index=False)
    else:
        df_log.to_csv(filename, mode="a", header=False, index=False)
