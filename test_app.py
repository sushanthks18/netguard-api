import json
import pytest
from app import app, endpoints, incidents, NEXT_ID


@pytest.fixture
def client():
    app.config["TESTING"] = True
    endpoints.clear()
    incidents.clear()
    NEXT_ID["value"] = 1
    with app.test_client() as client:
        yield client


def register(client, name="Core-GW-01", url="https://core-gw-01.local"):
    payload = json.dumps({"name": name, "url": url})
    resp = client.post(
        "/endpoints", data=payload, content_type="application/json"
    )
    return resp.get_json()["id"]


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_endpoint(client):
    payload = json.dumps({"name": "IMS-Node-1", "url": "https://ims1.local"})
    resp = client.post(
        "/endpoints", data=payload, content_type="application/json"
    )
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "IMS-Node-1"


def test_register_missing_fields(client):
    payload = json.dumps({"name": "IncompleteNode"})
    resp = client.post(
        "/endpoints", data=payload, content_type="application/json"
    )
    assert resp.status_code == 400


def test_report_healthy_check_no_incident(client):
    eid = register(client)
    payload = json.dumps({"latency_ms": 80, "up": True})
    resp = client.post(
        f"/endpoints/{eid}/report",
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == 201
    assert len(incidents) == 0


def test_report_down_triggers_critical_incident(client):
    eid = register(client)
    payload = json.dumps({"latency_ms": 0, "up": False})
    client.post(
        f"/endpoints/{eid}/report",
        data=payload,
        content_type="application/json",
    )
    resp = client.get("/incidents")
    body = resp.get_json()
    assert body["incident_count"] == 1
    assert body["incidents"][0]["severity"] == "critical"


def test_report_high_latency_triggers_warning(client):
    eid = register(client)
    payload = json.dumps({"latency_ms": 500, "up": True})
    client.post(
        f"/endpoints/{eid}/report",
        data=payload,
        content_type="application/json",
    )
    resp = client.get("/incidents")
    body = resp.get_json()
    assert body["incident_count"] == 1
    assert body["incidents"][0]["severity"] == "warning"


def test_endpoint_status_returns_history(client):
    eid = register(client)
    payload = json.dumps({"latency_ms": 90, "up": True})
    client.post(
        f"/endpoints/{eid}/report",
        data=payload,
        content_type="application/json",
    )
    resp = client.get(f"/endpoints/{eid}/status")
    body = resp.get_json()
    assert body["latest_status"]["latency_ms"] == 90
    assert len(body["check_history"]) == 1
