import os
import json
import time
import joblib
import pandas as pd
import requests
from datetime import datetime
import pytz
from random import uniform, choice

from utils import fetch_klines
from signal_logger import log_signal

CONFIDENCE_THRESHOLD = 0.80
BST = pytz.timezone("Asia/Dhaka")

print("📡 Starting swing scanner with detailed logging...")

def load_model():
    path = "model.pkl"
    if os.path.exists(path):
        try:
            model = joblib.load(path)
            print("✅ Model loaded successfully.")
            return model
        except Exception as e:
            print(f"❌ Model load error: {e}")
    return None

def get_all_usdt_futures_symbols():
    try:
        info = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()
        return [s["symbol"] for s in info["symbols"] if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"]
    except:
        return []

def scan():
    model = load_model()
    symbols = get_all_usdt_futures_symbols()
    results = []
    scan_log = []

    for symbol in symbols:
        print(f"🔍 Scanning {symbol}...")
        try:
            df_15m = fetch_klines(symbol, interval="15m", limit=100)
            df_1h = fetch_klines(symbol, interval="1h", limit=100)
            if df_15m is None or df_1h is None or df_15m.empty or df_1h.empty:
                print(f"⚠️  {symbol} skipped due to missing data.")
                continue

            for df in [df_15m, df_1h]:
                df["EMA20"] = df["Close"].ewm(span=20).mean()
                df["EMA50"] = df["Close"].ewm(span=50).mean()
                df["RSI"] = 100 - (100 / (1 + df["Close"].diff().clip(lower=0).rolling(14).mean() / df["Close"].diff().clip(upper=0).abs().rolling(14).mean()))
                macd = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
                signal = macd.ewm(span=9).mean()
                df["MACD"] = macd
                df["MACD_Signal"] = signal
                df["RVOL"] = df["Volume"] / df["Volume"].rolling(window=20).mean()
                df["ADX"] = abs(df["High"].diff() - df["Low"].diff()).rolling(14).mean()

            l15 = df_15m.iloc[-1]
            l1h = df_1h.iloc[-1]

            if l15["ADX"] < 25 or l1h["ADX"] < 25:
                print(f"❌ {symbol} rejected: ADX too low")
                scan_log.append({"symbol": symbol, "status": "rejected", "reason": "ADX < 25"})
                continue
            if not (55 <= l15["RSI"] <= 85 and 55 <= l1h["RSI"] <= 85):
                print(f"❌ {symbol} rejected: RSI = {l15['RSI']:.1f} / {l1h['RSI']:.1f}")
                scan_log.append({"symbol": symbol, "status": "rejected", "reason": "RSI out of range"})
                continue
            if l15["RVOL"] < 1.5:
                print(f"❌ {symbol} rejected: RVOL = {l15['RVOL']:.2f}")
                scan_log.append({"symbol": symbol, "status": "rejected", "reason": "RVOL < 1.5"})
                continue
            macd_cross = df_15m["MACD"].iloc[-2] < df_15m["MACD_Signal"].iloc[-2] and l15["MACD"] > l15["MACD_Signal"]
            if not macd_cross:
                print(f"❌ {symbol} rejected: No MACD crossover")
                scan_log.append({"symbol": symbol, "status": "rejected", "reason": "No MACD crossover"})
                continue

            breakout = l15["Close"] > l15["EMA20"] > l15["EMA50"] and l1h["Close"] > l1h["EMA20"] > l1h["EMA50"]
            breakdown = l15["Close"] < l15["EMA20"] < l15["EMA50"] and l1h["Close"] < l1h["EMA20"] < l1h["EMA50"]

            if breakout or breakdown:
                entry = l15["Close"]
                atr = df_15m["High"].sub(df_15m["Low"]).rolling(14).mean().iloc[-1]
                tps = [
                    round(entry * (1.04 if breakout else 0.96), 4),
                    round(entry * (1.06 if breakout else 0.94), 4),
                    round(entry * (1.08 if breakout else 0.92), 4),
                    round(entry * (1.10 if breakout else 0.90), 4),
                ]
                sl = round(entry * (0.97 if breakout else 1.03), 4)
                now = datetime.now(BST).strftime("%Y-%m-%d %H:%M:%S")

                if model:
                    features = [[
                        l15["EMA20"] - l15["EMA50"],
                        l15["RSI"],
                        l15["MACD"] - l15["MACD_Signal"],
                        l15["ADX"],
                        atr,
                        atr / entry,
                        l15["RVOL"]
                    ]]
                    confidence = round(model.predict_proba(features)[0][1] * 100, 2)
                else:
                    confidence = 90.0

                if confidence >= CONFIDENCE_THRESHOLD:
                    print(f"✅ {symbol} | Confidence: {confidence}%")
                    row = {
                        "Coin": symbol,
                        "Type": "LONG" if breakout else "SHORT",
                        "Confidence": confidence,
                        "Entry": round(entry, 4),
                        "TPs": tps,
                        "SL": sl,
                        "Why Detected": "Trend+Volume+ML",
                        "Signal Time": now
                    }
                    log_signal(row)
                    results.append(row)
                    scan_log.append({"symbol": symbol, "status": "✅ passed", "confidence": confidence})
                else:
                    print(f"⚠️  {symbol} skipped — Confidence too low ({confidence}%)")
                    scan_log.append({"symbol": symbol, "status": "rejected", "reason": f"Low confidence ({confidence}%)"})
        except Exception as e:
            print(f"❌ Error with {symbol}: {str(e)}")
            scan_log.append({"symbol": symbol, "status": "error", "reason": str(e)})
            continue

    print(f"\n✅ Scan complete: {len(results)} signal(s) found out of {len(symbols)} coins")

    with open("scan_debug.json", "w") as f:
        json.dump(scan_log, f, indent=2)

    return results

if __name__ == "__main__":
    scan()
