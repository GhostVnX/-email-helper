# track_api.py — Open & Click Tracking Server

from flask import Flask, request, send_file, redirect
import os
import json
from datetime import datetime

app = Flask(__name__)
TRACK_LOG_DIR = "logs/tracking"
os.makedirs(TRACK_LOG_DIR, exist_ok=True)

PIXEL_PATH = "static/pixel.png"

# Utility: write tracking data

def log_event(event_type, tracking_id):
    campaign = tracking_id.split(":")[0] if ":" in tracking_id else "unknown"
    log_path = os.path.join(TRACK_LOG_DIR, f"{campaign}_{event_type}.json")

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "id": tracking_id
    }

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(log_path, "w") as f:
        json.dump(data, f, indent=2)


# 📬 Open Tracking
@app.route("/track")
def track_open():
    tid = request.args.get("tid")
    if tid:
        log_event("open", tid)
    return send_file(PIXEL_PATH, mimetype="image/png")


# 🔗 Click Tracking
@app.route("/redirect")
def track_click():
    tid = request.args.get("tid")
    url = request.args.get("url")
    if tid and url:
        log_event("click", tid)
        return redirect(url)
    return "Invalid request.", 400


# Run locally (dev only)
if __name__ == "__main__":
    app.run(debug=True, port=8080)
