import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_TO = os.getenv("ALERT_EMAIL")

def send_email(signal):
    subject = f"[Swing Signal] {signal['Coin']} | {signal['Type']} | Confidence: {signal['Confidence']}%"

    tps = signal.get("TPs", [])
    tp_lines = "\n".join([f"TP{i+1}      : {tp}" for i, tp in enumerate(tps) if tp])

    body = f"""
🚀 New Swing Signal Detected!

Symbol     : {signal['Coin']}
Direction  : {signal['Type']}
Entry      : {signal['Entry']}
{tp_lines}
SL         : {signal['SL']}
Confidence : {signal['Confidence']}%
Signal Time: {signal['Signal Time']}

📊 Indicators:
- EMA Diff   : {signal.get('ema_diff', 'N/A')}
- RSI        : {signal.get('rsi', 'N/A')}
- MACD Hist  : {signal.get('macd_hist', 'N/A')}
- ADX        : {signal.get('adx', 'N/A')}
- ATR        : {signal.get('atr', 'N/A')}
- RVOL       : {signal.get('rvol', 'N/A')}

👉 Check your dashboard: Nihar's Dream Project
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
