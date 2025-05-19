
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime
import pytz
import os
import requests
import json
from email_alerts import send_email
from signal_logger import log_signal
from binance.client import Client

TIMEZONE = pytz.timezone("Asia/Dhaka")
CONFIDENCE_THRESHOLD = 0.97
MODEL_PATH = "model.pkl"
ACTIVE_SIGNALS_FILE = "active_signals.json"
SIGNAL_JSON = "signals.json"

logging.basicConfig(filename="scanner.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = Client(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))

def load_model():
    try:
        model = joblib.load(MODEL_PATH)
        logging.info("✅ Model loaded.")
        return model
    except Exception as e:
        logging.error(f"❌ Model load failed: {e}")
        return None

def fetch_klines(symbol, interval="1h", limit=100):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        raw = requests.get(url).json()
        cols = ["time", "open", "high", "low", "close", "volume", "close_time",
                "quote_asset_vol", "num_trades", "taker_buy_base", "taker_buy_quote", "ignore"]
        df = pd.DataFrame(raw, columns=cols)
        df = df.astype(float)
        return df
    except:
        return None

def calculate_features(df):
    df["ema_50"] = df["close"].ewm(span=50).mean()
    df["ema_200"] = df["close"].ewm(span=200).mean()
    df["ema_diff"] = df["ema_50"] - df["ema_200"]
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    macd_fast = df["close"].ewm(span=12).mean()
    macd_slow = df["close"].ewm(span=26).mean()
    df["macd_hist"] = macd_fast - macd_slow - (macd_fast - macd_slow).ewm(span=9).mean()
    tr = df[["high", "low", "close"]].apply(lambda x: max(x["high"] - x["low"], abs(x["high"] - x["close"]), abs(x["low"] - x["close"])), axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["atr_ratio"] = df["atr"] / df["close"]
    df["rvol"] = df["volume"] / df["volume"].rolling(20).mean()
    df["adx"] = 30  # Static placeholder
    return df

def load_active_signals():
    if os.path.exists(ACTIVE_SIGNALS_FILE):
        with open(ACTIVE_SIGNALS_FILE, "r") as f:
            return json.load(f)
    return []

def save_active_signals(signals):
    with open(ACTIVE_SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

def scan():
    model = load_model()
    active = load_active_signals()
    info = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()
    symbols = [s["symbol"] for s in info["symbols"] if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"]
    results = []

    for symbol in symbols:
        if symbol in [s["Coin"] for s in active]:
            continue
        df1h = fetch_klines(symbol, "1h")
        df4h = fetch_klines(symbol, "4h")
        if df1h is None or df4h is None:
            continue
        df1h = calculate_features(df1h)
        df4h = calculate_features(df4h)
        l1 = df1h.iloc[-1]
        l4 = df4h.iloc[-1]
        long_trend = l1["ema_diff"] > 0 and l4["ema_diff"] > 0
        short_trend = l1["ema_diff"] < 0 and l4["ema_diff"] < 0
        if not (long_trend or short_trend): continue
        if l1["rvol"] < 2 or l1["atr_ratio"] < 0.01: continue
        if long_trend and not (55 <= l1["rsi"] <= 80): continue
        if short_trend and not (20 <= l1["rsi"] <= 45): continue
        direction = "LONG" if long_trend else "SHORT"
        entry = l1["close"]
        sl = round(entry * 0.985, 4) if direction == "LONG" else round(entry * 1.015, 4)
        tp1 = round(entry + 1.5 * l1["atr"], 4) if direction == "LONG" else round(entry - 1.5 * l1["atr"], 4)
        tp2 = round(entry + 2.5 * l1["atr"], 4) if direction == "LONG" else round(entry - 2.5 * l1["atr"], 4)
        tp3 = round(entry + 4.0 * l1["atr"], 4) if direction == "LONG" else round(entry - 4.0 * l1["atr"], 4)
        tp4 = round(entry + 5.0 * l1["atr"], 4) if direction == "LONG" else round(entry - 5.0 * l1["atr"], 4)
        features = [[l1["ema_diff"], l1["rsi"], l1["macd_hist"], l1["adx"], l1["atr"], l1["atr_ratio"], l1["rvol"]]]
        confidence = model.predict_proba(features)[0][1] if model else 0.9
        if confidence < CONFIDENCE_THRESHOLD: continue
        now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        signal = {
            "Coin": symbol,
            "Type": direction,
            "Entry": round(entry, 4),
            "TPs": [tp1, tp2, tp3, tp4],
            "SL": sl,
            "Confidence": round(confidence * 100, 2),
            "Signal Time": now,
            "ema_diff": l1["ema_diff"], "rsi": l1["rsi"], "macd_hist": l1["macd_hist"],
            "adx": l1["adx"], "atr": l1["atr"], "atr_ratio": l1["atr_ratio"], "rvol": l1["rvol"]
        }
        log_signal(signal)
        try: send_email(signal)
        except: pass
        results.append(signal)

    with open(SIGNAL_JSON, "w") as f:
        json.dump({"signals": results, "meta": {
            "timestamp": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
            "total_scanned": len(symbols),
            "generated": len(results),
            "avg_confidence": round(np.mean([s["Confidence"] for s in results]), 2) if results else 0
        }}, f, indent=2)

    save_active_signals(results)
    return results

if __name__ == "__main__":
    scan()
