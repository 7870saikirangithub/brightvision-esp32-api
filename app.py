
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
from threading import Lock
import math

app = Flask(__name__)

# Enable CORS for the monitoring dashboard.
# For production, restrict this to your dashboard's domain.
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/health": {"origins": "*"}
})

lock = Lock()

latest_data = {
    "device": "ESP32",
    "temperature": None,
    "humidity": None,
    "device_status": "Waiting for ESP32",
    "updated_at": None
}


# ================= HOME =================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "BrightVision ESP32 API is running",
        "endpoints": [
            "/health",
            "/api/data",
            "/api/latest"
        ]
    })


# ================= HEALTH CHECK =================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "BrightVision ESP32 API"
    })


# ================= RECEIVE ESP32 DATA =================
@app.route("/api/data", methods=["POST", "OPTIONS"])
def receive_data():

    # Handle browser CORS preflight requests.
    if request.method == "OPTIONS":
        return "", 204

    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type must be application/json"
        }), 400

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({
            "success": False,
            "error": "Invalid JSON object"
        }), 400

    try:
        temperature = float(payload["temperature"])
        humidity = float(payload["humidity"])

        if not math.isfinite(temperature):
            raise ValueError("Temperature must be finite")

        if not math.isfinite(humidity):
            raise ValueError("Humidity must be finite")

        if not -50 <= temperature <= 150:
            raise ValueError("Temperature out of range")

        if not 0 <= humidity <= 100:
            raise ValueError("Humidity out of range")

    except (KeyError, TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Provide valid temperature and humidity numbers"
        }), 400

    now = datetime.now(timezone.utc).isoformat()

    with lock:
        latest_data.update({
            "device": str(
                payload.get("device", "ESP32")
            )[:50],
            "temperature": temperature,
            "humidity": humidity,
            "device_status": "Online",
            "updated_at": now
        })

    return jsonify({
        "success": True,
        "message": "Data received successfully",
        "updated_at": now
    }), 201


# ================= GET LATEST DATA =================
@app.route("/api/latest", methods=["GET", "OPTIONS"])
def get_latest():

    if request.method == "OPTIONS":
        return "", 204

    with lock:
        data = dict(latest_data)

    if data["updated_at"] is not None:
        try:
            updated = datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            )

            age = (
                datetime.now(timezone.utc) - updated
            ).total_seconds()

            data["device_status"] = (
                "Online" if age <= 45 else "Offline"
            )

        except (ValueError, TypeError):
            data["device_status"] = "Unknown"

    return jsonify(data)


# ================= START SERVER =================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
