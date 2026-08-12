"""
NetGuard - Network Endpoint Health Monitor
--------------------------------------------
A lightweight Flask service that tracks the health of network
endpoints/services (simulating core network function monitoring),
records latency & uptime metrics, and raises incident alerts when
services degrade or go down.

Endpoints:
  GET  /health                    -> service liveness check
  POST /endpoints                 -> register a network endpoint to monitor
  POST /endpoints/<id>/report     -> report a health-check result (ping)
  GET  /endpoints                 -> list all monitored endpoints
  GET  /endpoints/<id>/status     -> current status + latency history
  GET  /incidents                 -> active/triggered incidents
"""

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory stores (swap for a real DB in production)
endpoints = {}       # id -> {name, url, checks: [...]}
incidents = []        # list of incident dicts

LATENCY_THRESHOLD_MS = 300   # above this -> degraded
NEXT_ID = {"value": 1}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200


@app.route("/endpoints", methods=["POST"])
def register_endpoint():
    data = request.get_json(silent=True)
    if not data or "name" not in data or "url" not in data:
        return jsonify({"error": "name and url are required"}), 400

    endpoint_id = NEXT_ID["value"]
    NEXT_ID["value"] += 1
    endpoints[endpoint_id] = {"id": endpoint_id, "name": data["name"],
                               "url": data["url"], "checks": []}
    return jsonify(endpoints[endpoint_id]), 201


@app.route("/endpoints", methods=["GET"])
def list_endpoints():
    return jsonify(list(endpoints.values())), 200


@app.route("/endpoints/<int:endpoint_id>/report", methods=["POST"])
def report_check(endpoint_id):
    if endpoint_id not in endpoints:
        return jsonify({"error": "endpoint not found"}), 404

    data = request.get_json(silent=True)
    if not data or "latency_ms" not in data or "up" not in data:
        return jsonify({"error": "latency_ms and up are required"}), 400

    check = {
        "latency_ms": data["latency_ms"],
        "up": data["up"],
        "timestamp": datetime.utcnow().isoformat(),
    }
    endpoints[endpoint_id]["checks"].append(check)

    # incident detection -> mirrors "monitoring and incident response"
    if not data["up"]:
        incidents.append({
            "endpoint_id": endpoint_id,
            "endpoint_name": endpoints[endpoint_id]["name"],
            "severity": "critical",
            "reason": "endpoint down",
            "timestamp": check["timestamp"],
        })
    elif data["latency_ms"] > LATENCY_THRESHOLD_MS:
        incidents.append({
            "endpoint_id": endpoint_id,
            "endpoint_name": endpoints[endpoint_id]["name"],
            "severity": "warning",
            "reason": f"high latency ({data['latency_ms']}ms)",
            "timestamp": check["timestamp"],
        })

    return jsonify({"message": "check recorded", "check": check}), 201


@app.route("/endpoints/<int:endpoint_id>/status", methods=["GET"])
def endpoint_status(endpoint_id):
    if endpoint_id not in endpoints:
        return jsonify({"error": "endpoint not found"}), 404

    checks = endpoints[endpoint_id]["checks"]
    latest = checks[-1] if checks else None
    return jsonify({
        "endpoint": endpoints[endpoint_id]["name"],
        "latest_status": latest,
        "check_history": checks[-10:],
    }), 200


@app.route("/incidents", methods=["GET"])
def list_incidents():
    return jsonify({"incident_count": len(incidents), "incidents": incidents}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
