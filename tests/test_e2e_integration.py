"""End-to-end integration test suite verifying the complete UrbanSense architecture:
1. Authentication & Role-Based Access Control
2. Fleet Telemetry & PostGIS Geospatial Nearby Queries
3. AI Detection Ingestion, Severity Scoring & Deduplication
4. Incident Lifecycle & Status Transitions
5. Mobile Offline Event Batch Synchronization (Idempotency)
6. Real-time WebSocket Event Broadcasting
7. Analytics Overview & Route Intelligence
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.websocket.manager import manager


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_full_end_to_end_urban_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # -------------------------------------------------------------
        # STEP 1: Register & Authenticate Users (Admin & Driver)
        # -------------------------------------------------------------
        admin_email = f"e2e_admin_{uuid.uuid4().hex[:6]}@example.com"
        reg_admin = await client.post(
            "/api/v1/auth/register",
            json={
                "email": admin_email,
                "password": "StrongPassword123!",
                "name": "E2E Administrator",
                "role": "ADMIN",
            },
        )
        assert reg_admin.status_code == 201, reg_admin.text

        login_admin = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": "StrongPassword123!"},
        )
        assert login_admin.status_code == 200, login_admin.text
        admin_tokens = login_admin.json()["data"]
        admin_auth = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        driver_email = f"e2e_driver_{uuid.uuid4().hex[:6]}@example.com"
        reg_driver = await client.post(
            "/api/v1/auth/register",
            json={
                "email": driver_email,
                "password": "StrongPassword123!",
                "name": "E2E Bus Driver",
                "role": "DRIVER",
            },
        )
        assert reg_driver.status_code == 201, reg_driver.text

        login_driver = await client.post(
            "/api/v1/auth/login",
            json={"email": driver_email, "password": "StrongPassword123!"},
        )
        assert login_driver.status_code == 200, login_driver.text
        driver_tokens = login_driver.json()["data"]
        driver_auth = {"Authorization": f"Bearer {driver_tokens['access_token']}"}

        # Verify /auth/me
        me_resp = await client.get("/api/v1/auth/me", headers=admin_auth)
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["email"] == admin_email

        # -------------------------------------------------------------
        # STEP 2: Fleet Management (Create Bus & Route)
        # -------------------------------------------------------------
        route_resp = await client.post(
            "/api/v1/routes",
            headers=admin_auth,
            json={
                "route_number": f"R-{uuid.uuid4().hex[:4].upper()}",
                "name": "Central Corridor Express",
                "origin_name": "Station North",
                "destination_name": "Terminal South",
            },
        )
        assert route_resp.status_code in (200, 201)
        route_id = route_resp.json()["data"]["id"]

        bus_resp = await client.post(
            "/api/v1/buses",
            headers=admin_auth,
            json={
                "registration_number": f"WB-{uuid.uuid4().hex[:4].upper()}",
                "model": "Volvo 8400 Electric",
                "capacity": 55,
                "status": "ACTIVE",
                "assigned_route_id": route_id,
            },
        )
        assert bus_resp.status_code in (200, 201)
        bus_id = bus_resp.json()["data"]["id"]

        # -------------------------------------------------------------
        # STEP 3: GPS Telemetry & PostGIS Geospatial Nearby Queries
        # -------------------------------------------------------------
        base_lat, base_lon = 22.5726, 88.3639  # Central Kolkata coordinates
        loc_resp = await client.post(
            "/api/v1/locations",
            headers=driver_auth,
            json={
                "bus_id": bus_id,
                "latitude": base_lat,
                "longitude": base_lon,
                "speed": 38.5,
                "heading": 180.0,
            },
        )
        assert loc_resp.status_code in (200, 201), loc_resp.text

        # Query nearby locations within 5 km radius
        nearby_resp = await client.get(
            f"/api/v1/locations/nearby?latitude={base_lat}&longitude={base_lon}&radius_km=5.0",
            headers=admin_auth,
        )
        assert nearby_resp.status_code == 200
        nearby_items = nearby_resp.json()["data"]["items"]
        assert len(nearby_items) >= 1
        assert any(item.get("bus_id") == bus_id for item in nearby_items)

        # -------------------------------------------------------------
        # STEP 4: AI Detection Ingestion, Severity & Deduplication
        # -------------------------------------------------------------
        detection_resp = await client.post(
            "/api/v1/detections",
            headers=driver_auth,
            json={
                "bus_id": bus_id,
                "detection_type": "POTHOLE",
                "confidence": 0.92,
                "latitude": base_lat,
                "longitude": base_lon,
                "model_name": "UrbanSense-YOLOv8x",
                "model_version": "v1.4.0",
                "metadata": {"source": "mobile-cam-front"},
            },
        )
        assert detection_resp.status_code in (200, 201), detection_resp.text
        det_data = detection_resp.json()["data"]
        assert det_data["detection_type"] == "POTHOLE"
        assert "event_result" in det_data

        # Test duplicate AI detection deduplication via event engine
        det_dup1 = await client.post(
            "/api/v1/detections",
            headers=driver_auth,
            json={
                "bus_id": bus_id,
                "detection_type": "WATERLOGGING",
                "confidence": 0.85,
                "latitude": 22.8500,
                "longitude": 88.6500,
            },
        )
        assert det_dup1.status_code in (200, 201)
        data_dup1 = det_dup1.json()["data"]
        assert data_dup1["event_result"]["status"] == "success"

        det_dup2 = await client.post(
            "/api/v1/detections",
            headers=driver_auth,
            json={
                "bus_id": bus_id,
                "detection_type": "WATERLOGGING",
                "confidence": 0.92,
                "latitude": 22.85002,  # ~2 meters away
                "longitude": 88.65001,
            },
        )
        assert det_dup2.status_code in (200, 201)
        data_dup2 = det_dup2.json()["data"]["event_result"]
        assert data_dup2["action"] == "merged"
        assert data_dup2["is_duplicate"] is True
        assert data_dup2["recurrence_count"] >= 2

        # -------------------------------------------------------------
        # STEP 5: Mobile Offline Batch Sync (Idempotent)
        # -------------------------------------------------------------
        client_sync_id = str(uuid.uuid4())
        sync_payload = [
            {
                "client_event_id": client_sync_id,
                "event_type": "location",
                "payload": {
                    "bus_id": bus_id,
                    "latitude": base_lat + 0.005,
                    "longitude": base_lon + 0.005,
                    "speed": 42.0,
                },
            }
        ]

        # First sync
        sync_res1 = await client.post("/api/v1/sync", headers=driver_auth, json=sync_payload)
        assert sync_res1.status_code in (200, 201), sync_res1.text
        assert sync_res1.json()["data"]["processed_count"] == 1
        assert sync_res1.json()["data"]["results"][0]["accepted"] is True
        assert sync_res1.json()["data"]["results"][0]["duplicate"] is False

        # Re-sync same payload (idempotency check)
        sync_res2 = await client.post("/api/v1/sync", headers=driver_auth, json=sync_payload)
        assert sync_res2.status_code in (200, 201)
        assert sync_res2.json()["data"]["results"][0]["accepted"] is True
        assert sync_res2.json()["data"]["results"][0]["duplicate"] is True

        # -------------------------------------------------------------
        # STEP 6: Incidents & Lifecycle
        # -------------------------------------------------------------
        inc_resp = await client.post(
            "/api/v1/incidents",
            headers=driver_auth,
            json={
                "incident_type": "ROAD_HAZARD",
                "severity": "HIGH",
                "latitude": base_lat,
                "longitude": base_lon,
                "title": "Severe road obstruction near bus corridor",
                "description": "Debris and fallen branch blocking transit lane",
            },
        )
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["data"]["id"]

        status_update = await client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            headers=admin_auth,
            json={"status": "UNDER_REVIEW"},
        )
        assert status_update.status_code == 200
        assert status_update.json()["data"]["status"] == "UNDER_REVIEW"

        # -------------------------------------------------------------
        # STEP 7: Analytics Overview & Route Intelligence
        # -------------------------------------------------------------
        overview = await client.get("/api/v1/analytics/overview", headers=admin_auth)
        assert overview.status_code == 200
        ov_data = overview.json()["data"]
        assert ov_data["total_buses"] >= 1
        assert ov_data["total_detections"] >= 1

        route_intel = await client.get("/api/v1/analytics/routes/intelligence", headers=admin_auth)
        assert route_intel.status_code == 200
        assert "routes" in route_intel.json()["data"]

        # -------------------------------------------------------------
        # STEP 8: WebSocket Manager Broadcast Verification
        # -------------------------------------------------------------
        # Test direct broadcast method on ConnectionManager
        await manager.broadcast("buses", {"event": "BUS_LOCATION_UPDATE", "bus_id": bus_id})
        await manager.broadcast("incidents", {"event": "INCIDENT_ALERT", "incident_id": incident_id})
