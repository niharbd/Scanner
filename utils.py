import requests
import pandas as pd
import time

def fetch_klines(symbol, interval="15m", limit=100):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    retries = 3

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data, columns=[
                    "Open Time", "Open", "High", "Low", "Close", "Volume",
                    "Close Time", "Quote Asset Volume", "Number of Trades",
                    "Taker Buy Base", "Taker Buy Quote", "Ignore"
                ])
                df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms")
                df["Close Time"] = pd.to_datetime(df["Close Time"], unit="ms")
                df = df.astype({
                    "Open": "float", "High": "float", "Low": "float",
                    "Close": "float", "Volume": "float"
                })
                return df
            else:
                print(f"⚠️ Error fetching {symbol} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Fetch error for {symbol} ({interval}): {e}")
            time.sleep(1)

    return None
