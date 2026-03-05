import os
import json
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from src.core.rag import RAGPipeline
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "db.json")
SS_DIR = os.path.join(BASE_DIR, "data", "screenshots")

pipeline = RAGPipeline()

db = {}
if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

for filename in sorted(os.listdir(SS_DIR)):
    if not filename.endswith(".jpg"):
        continue

    name = filename.replace("screen_", "").replace(".jpg", "")
    dt = datetime.strptime(name, "%Y%m%d-%H%M%S")
    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    timestamp = int(dt.timestamp())
    entry_id = f"entry_{timestamp_str.replace(' ', '_').replace(':', '-')}"

    if entry_id in db:
        continue

    img_path = os.path.join("data", "screenshots", filename)
    print(f"Analyzing: {timestamp_str}")
    analysis = pipeline.analyze(img_path)

    time.sleep(2)

    db[entry_id] = {
        "text": f"TIME: {timestamp_str}\nSCREEN ANALYSIS: {analysis}",
        "metadata": {
            "timestamp": timestamp,
            "timestamp_str": timestamp_str,
            "screenshot_path": img_path
        }
    }

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Added: {timestamp_str}")

print("Done.")