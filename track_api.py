# track_api.py — Open & Click Tracking Server with Stats Endpoint

from flask import Flask, request, send_file, redirect, jsonify
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


# 📊 API to return tracking stats
@app.route("/stats")
def tracking_stats():
    campaign = request.args.get("campaign")
    if not campaign:
        return jsonify({"error": "campaign query param required"}), 400

    def load_event(event_type):
        path = os.path.join(TRACK_LOG_DIR, f"{campaign}_{event_type}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return []

    opens = load_event("open")
    clicks = load_event("click")

    return jsonify({
        "campaign": campaign,
        "opens": len(opens),
        "clicks": len(clicks),
        "open_details": opens,
        "click_details": clicks
    })


# Run locally (dev only)
if __name__ == "__main__":
    app.run(debug=True, port=8080)
