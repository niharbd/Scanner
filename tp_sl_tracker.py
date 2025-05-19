import json
import os
import pandas as pd
from datetime import datetime
import pytz
import requests

BST = pytz.timezone("Asia/Dhaka")
ACTIVE_FILE = "active_signals.json"
LOG_FILE = "signals_log.csv"

def fetch_current_price(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
        response = requests.get(url)
        return float(response.json()["price"])
    except:
        return None

def load_active_signals():
    if os.path.exists(ACTIVE_FILE):
        with open(ACTIVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_active_signals(signals):
    with open(ACTIVE_FILE, "w") as f:
        json.dump(signals, f, indent=2)

def append_to_log(entry, result, tp_hit=None):
    entry["result"] = result
    entry["tp_hit"] = tp_hit
    entry["exit_time"] = datetime.now(BST).strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        if not ((df["Coin"] == entry["Coin"]) & (df["Signal Time"] == entry["Signal Time"])).any():
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:
        df = pd.DataFrame([entry])
    df.to_csv(LOG_FILE, index=False)

def track():
    active = load_active_signals()
    updated = []
    for signal in active:
        symbol = signal["Coin"]
        current = fetch_current_price(symbol)
        if current is None:
            updated.append(signal)
            continue

        direction = signal["Type"].upper()
        is_long = direction == "LONG"
        tps = signal.get("TPs", [])
        sl = signal["SL"]
        entry = signal["Entry"]

        tp_hit = None
        result = None

        for i, tp in enumerate(tps):
            if tp is None:
                continue
            if (is_long and current >= tp) or (not is_long and current <= tp):
                tp_hit = f"TP{i+1}"
                result = 1
            else:
                break

        sl_hit = (current <= sl) if is_long else (current >= sl)
        if sl_hit:
            tp_hit = None
            result = 0

        if result is not None:
            print(f"✅ {symbol}: {tp_hit if result == 1 else 'SL'} hit.")
            append_to_log(signal, result, tp_hit)
        else:
            updated.append(signal)
            print(f"🔄 {symbol}: still running at {current}")

    save_active_signals(updated)

if __name__ == "__main__":
    print("📊 Checking open trades...")
    track()
    print("✅ Done.")
