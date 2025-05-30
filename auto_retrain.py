import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    df = pd.read_csv("signals_log.csv")
    df = df[df["result"].isin([0, 1])].dropna()

    features = ["ema_diff", "rsi", "macd_hist", "adx", "atr", "atr_ratio", "rvol"]
    X = df[features]
    y = df["result"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    joblib.dump(model, "model.pkl")
    joblib.dump(model, f"model_{timestamp}.pkl")

    logging.info("✅ Auto-retrain complete. Model updated and backup saved.")

except Exception as e:
    logging.error(f"❌ Auto-retrain failed: {e}")
