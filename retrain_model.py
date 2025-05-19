import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
from datetime import datetime

# Load and clean data
df = pd.read_csv("signals_log.csv")
df.dropna(inplace=True)
df = df[df["result"].isin([0, 1])]  # Ensure binary labels

# Feature columns
features = [
    "ema_diff", "rsi", "macd_hist", "adx",
    "atr", "atr_ratio", "rvol"
]
X = df[features]
y = df["result"]

print(f"📊 Training on {len(df)} samples")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = "model.pkl"
backup_path = f"model_{timestamp}.pkl"
joblib.dump(model, model_path)
joblib.dump(model, backup_path)

print(f"✅ Model retrained and saved as {model_path} and backup {backup_path}")
