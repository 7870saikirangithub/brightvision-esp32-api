
import urllib.request
import json

url = "http://127.0.0.1:5000/api/data"

data = {
    "device": "ESP32-BrightVision",
    "temperature": 30.5,
    "humidity": 65
}

body = json.dumps(data).encode("utf-8")

req = urllib.request.Request(
    url,
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode("utf-8"))
except Exception as e:
    print("Error:", e)
