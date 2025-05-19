import json
import logging
from datetime import datetime
from scanner_swing_improved import scan

SIGNAL_JSON = "signals.json"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_scanner():
    logging.info("Running swing signal scanner...")
    try:
        result = scan()
        if isinstance(result, dict) and "signals" in result:
            with open(SIGNAL_JSON, "w") as f:
                json.dump(result, f, indent=2, default=str)
            logging.info(f"✅ {len(result['signals'])} signal(s) saved to {SIGNAL_JSON}")
            logging.info(f"📊 Avg Confidence: {result['meta'].get('avg_confidence', 'N/A')}%, Coins Scanned: {result['meta'].get('total_scanned', 'N/A')}")
        else:
            logging.info("No valid swing signals found.")
    except Exception as e:
        logging.error(f"❌ Scanner run failed: {e}")

if __name__ == "__main__":
    run_scanner()
