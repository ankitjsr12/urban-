import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"tester.{uuid.uuid4().hex[:6]}@urbansense.local"
    client.post(
        '/api/v1/auth/register',
        json={'name': 'Telemetry Tester', 'email': email, 'password': 'Password123!', 'role': 'AUTHORITY'},
    )
    res = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Password123!'})
    token = res.json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_gps_location_ingestion_and_nearby_queries(auth_headers):
    # 1. Create a bus first
    bus_res = client.post(
        '/api/v1/buses',
        headers=auth_headers,
        json={'registration_number': f"GPS-BUS-{uuid.uuid4().hex[:4].upper()}"},
    )
    bus_id = bus_res.json()['data']['id']

    # 2. Ingest GPS point
    client_evt_id = f"evt-{uuid.uuid4().hex}"
    loc_payload = {
        'bus_id': bus_id,
        'latitude': 37.7749,
        'longitude': -122.4194,
        'speed': 28.5,
        'heading': 90.0,
        'accuracy': 2.0,
        'source': 'GPS_TEST',
        'client_event_id': client_evt_id,
    }
    loc_res = client.post('/api/v1/locations', headers=auth_headers, json=loc_payload)
    assert loc_res.status_code == 200
    assert loc_res.json()['data']['bus_id'] == bus_id

    # 3. Duplicate event submission returns duplicate acknowledgement
    dup_res = client.post('/api/v1/locations', headers=auth_headers, json=loc_payload)
    assert dup_res.status_code == 200
    assert dup_res.json()['data']['duplicate'] is True

    # 4. Ingest second point for history
    loc_payload_2 = {
        'bus_id': bus_id,
        'latitude': 37.7760,
        'longitude': -122.4180,
        'speed': 32.0,
    }
    client.post('/api/v1/locations', headers=auth_headers, json=loc_payload_2)

    # 5. Query latest location
    latest_res = client.get(f'/api/v1/buses/{bus_id}/location', headers=auth_headers)
    assert latest_res.status_code == 200
    assert latest_res.json()['data']['bus_id'] == bus_id

    # 6. Query location history
    history_res = client.get(f'/api/v1/buses/{bus_id}/location-history', headers=auth_headers)
    assert history_res.status_code == 200
    assert history_res.json()['data']['total'] >= 2

    # 7. Query nearby buses
    nearby_res = client.get(
        '/api/v1/buses/nearby?latitude=37.7750&longitude=-122.4190&radius_km=10.0',
        headers=auth_headers,
    )
    assert nearby_res.status_code == 200
    nearby_items = nearby_res.json()['data']['items']
    assert len(nearby_items) >= 1
    assert any(item['bus_id'] == bus_id for item in nearby_items)


def test_offline_sync_idempotency(auth_headers):
    # Prepare batch offline events
    bus_res = client.post(
        '/api/v1/buses',
        headers=auth_headers,
        json={'registration_number': f"SYNC-BUS-{uuid.uuid4().hex[:4].upper()}"},
    )
    bus_id = bus_res.json()['data']['id']

    evt_1 = f"sync-evt-{uuid.uuid4().hex}"
    evt_2 = f"sync-evt-{uuid.uuid4().hex}"

    batch = [
        {
            'client_event_id': evt_1,
            'event_type': 'location',
            'payload': {'bus_id': bus_id, 'latitude': 37.7800, 'longitude': -122.4100, 'speed': 25.0},
        },
        {
            'client_event_id': evt_2,
            'event_type': 'driver_log',
            'payload': {'status': 'SHIFT_START'},
        },
    ]

    # First sync submission
    res1 = client.post('/api/v1/sync', headers=auth_headers, json=batch)
    assert res1.status_code == 200
    results1 = res1.json()['data']['results']
    assert len(results1) == 2
    assert all(r['accepted'] is True and r['duplicate'] is False for r in results1)

    # Replay sync submission with identical client_event_ids
    res2 = client.post('/api/v1/sync', headers=auth_headers, json=batch)
    assert res2.status_code == 200
    results2 = res2.json()['data']['results']
    assert len(results2) == 2
    assert all(r['accepted'] is True and r['duplicate'] is True for r in results2)
