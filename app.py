
from flask import Flask, request, jsonify
from datetime import datetime, timezone
from threading import Lock

app = Flask(__name__)
lock = Lock()

latest_data = {
    "device": "ESP32",
    "temperature": None,
    "humidity": None,
    "device_status": "Waiting for ESP32",
    "updated_at": None
}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "BrightVision ESP32 API is running",
        "endpoints": ["/health", "/api/data", "/api/latest"]
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/data", methods=["POST"])
def receive_data():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        temperature = float(payload["temperature"])
        humidity = float(payload["humidity"])

        if not (-50 <= temperature <= 150):
            raise ValueError()

        if not (0 <= humidity <= 100):
            raise ValueError()

    except (KeyError, TypeError, ValueError):
        return jsonify({
            "error": "Valid temperature and humidity are required"
        }), 400

    with lock:
        latest_data.update({
            "device": str(payload.get("device", "ESP32"))[:50],
            "temperature": temperature,
            "humidity": humidity,
            "device_status": "Online",
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    return jsonify({
        "success": True,
        "message": "Data received successfully"
    }), 201


@app.route("/api/latest", methods=["GET"])
def get_latest():
    with lock:
        data = dict(latest_data)

    if data["updated_at"]:
        updated = datetime.fromisoformat(data["updated_at"])
        age = (datetime.now(timezone.utc) - updated).total_seconds()
        data["device_status"] = "Online" if age <= 45 else "Offline"

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
