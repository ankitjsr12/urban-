import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.road_defect import DefectSeverity, RoadDefectType
from app.models.incident import IncidentSeverity, IncidentType
from app.services.duplicate_detector import haversine_distance_meters
from app.services.severity_engine import SeverityEngine
from ai_service.ocr.anpr_verifier import MultiFrameANPRVerifier

client = TestClient(app)


def get_admin_headers():
    """Register and login an admin user for authenticated endpoint tests."""
    uid_str = uuid.uuid4().hex[:8]
    email = f"admin.{uid_str}@urbansense.local"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin Tester",
            "email": email,
            "password": "AdminPassword123!",
            "role": "ADMIN",
        },
    )
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "AdminPassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_detailed_health_check():
    res = client.get("/health/detailed")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in ("healthy", "degraded")
    assert "components" in body
    assert "database" in body["components"]
    assert "redis" in body["components"]
    assert "ai_service" in body["components"]


def test_severity_engine_calculations():
    # Pothole calculation
    sev, score, factors = SeverityEngine.calculate_defect_severity(
        defect_type=RoadDefectType.POTHOLE,
        confidence=0.92,
        speed_kmh=55.0,
        recurrence_count=3,
    )
    assert sev in (DefectSeverity.HIGH, DefectSeverity.CRITICAL)
    assert score > 45.0
    assert factors["confidence"] == 0.92
    assert factors["recurrence_level"] == "repeat"

    # Incident calculation
    i_sev, i_score, _ = SeverityEngine.calculate_incident_severity(
        incident_type=IncidentType.ACCIDENT,
        confidence=0.95,
        speed_kmh=80.0,
        traffic_density="HIGH",
    )
    assert i_sev in (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL)
    assert i_score >= 75.0


def test_anpr_multi_frame_verifier():
    verifier = MultiFrameANPRVerifier(min_frames=3, min_confidence=0.60)
    
    # Simulate jittery/noisy frame OCR observations of plate "MH12AB1234"
    observations = [
        ("MH12AB1234", 0.91),
        ("MH12AB1234", 0.88),
        ("MH12AB1234", 0.95),
        ("MH12AB123", 0.45),   # truncated glitch
    ]
    res = verifier.verify_observations(observations)
    assert res["is_verified"] is True
    assert res["verified_plate"] == "MH12AB1234"
    assert res["frame_count"] == 4
    assert res["matching_frames"] == 3
    assert res["confidence"] > 0.80


def test_haversine_distance():
    # Times Square (40.7580, -73.9855) to Empire State (40.7484, -73.9857) ~ 1.07 km
    dist = haversine_distance_meters(40.7580, -73.9855, 40.7484, -73.9857)
    assert 1000 <= dist <= 1200


def test_user_management_api():
    headers = get_admin_headers()

    # List users
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "items" in data
    assert data["total"] >= 1

    # Create target user to update
    uid_str = uuid.uuid4().hex[:8]
    email = f"user.{uid_str}@urbansense.local"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Target User",
            "email": email,
            "password": "Password123!",
            "role": "CITIZEN",
        },
    )
    user_id = reg.json()["data"]["id"]

    # Get single user
    detail_res = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["email"] == email

    # Patch user
    patch_res = client.patch(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"name": "Updated Name", "is_verified": True},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["name"] == "Updated Name"
    assert patch_res.json()["data"]["is_verified"] is True

    # Deactivate user
    del_res = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["is_active"] is False


def test_fleet_health_endpoint():
    headers = get_admin_headers()
    res = client.get("/api/v1/fleet/health", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "summary" in data
    assert "vehicles" in data
    assert "total_buses" in data["summary"]
    assert "fleet_health_avg" in data["summary"]


def test_route_intelligence_endpoint():
    headers = get_admin_headers()
    res = client.get("/api/v1/analytics/routes/intelligence", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "summary" in data
    assert "routes" in data
    assert "monitored_routes" in data["summary"]


def test_reports_generation_json_and_csv():
    headers = get_admin_headers()

    # JSON report
    res_json = client.get("/api/v1/reports/generate?report_type=road_defects&format=json", headers=headers)
    assert res_json.status_code == 200
    assert res_json.json()["success"] is True
    assert "records" in res_json.json()["data"]

    # CSV report
    res_csv = client.get("/api/v1/reports/generate?report_type=road_defects&format=csv", headers=headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "defect_type,severity,status" in res_csv.text

    # Summary report
    res_sum = client.get("/api/v1/reports/generate?report_type=summary&format=csv", headers=headers)
    assert res_sum.status_code == 200
    assert "metric,value" in res_sum.text


def test_system_monitoring_endpoint():
    headers = get_admin_headers()
    res = client.get("/api/v1/system/monitoring", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "services" in data
    assert "database" in data["services"]
    assert "websocket" in data
    assert "runtime" in data


def test_detection_ai_event_engine_deduplication():
    headers = get_admin_headers()

    # Post first detection (POTHOLE)
    det1 = {
        "detection_type": "POTHOLE",
        "class_name": "POTHOLE",
        "confidence": 0.88,
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    res1 = client.post("/api/v1/detections", headers=headers, json=det1)
    assert res1.status_code == 201
    data1 = res1.json()["data"]
    assert "event_result" in data1
    assert data1["event_result"]["status"] == "success"

    # Post duplicate detection within 50m of same pothole
    det2 = {
        "detection_type": "POTHOLE",
        "class_name": "POTHOLE",
        "confidence": 0.94,
        "latitude": 37.77492,  # ~2 meters away
        "longitude": -122.41941,
    }
    res2 = client.post("/api/v1/detections", headers=headers, json=det2)
    assert res2.status_code == 201
    data2 = res2.json()["data"]
    assert "event_result" in data2
    # Verify deduplication triggered
    assert data2["event_result"]["action"] == "merged"
    assert data2["event_result"]["is_duplicate"] is True
    assert data2["event_result"]["recurrence_count"] >= 2
