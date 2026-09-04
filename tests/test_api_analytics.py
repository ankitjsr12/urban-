import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"analytics.tester.{uuid.uuid4().hex[:6]}@urbansense.local"
    client.post(
        '/api/v1/auth/register',
        json={'name': 'Analytics Tester', 'email': email, 'password': 'Password123!', 'role': 'AUTHORITY'},
    )
    res = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Password123!'})
    token = res.json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_analytics_endpoints(auth_headers):
    # 1. Overview
    overview_res = client.get('/api/v1/analytics/overview', headers=auth_headers)
    assert overview_res.status_code == 200
    ov_data = overview_res.json()['data']
    assert 'total_buses' in ov_data
    assert 'total_road_defects' in ov_data
    assert 'total_incidents' in ov_data
    assert 'total_traffic_events' in ov_data

    # 2. Traffic Analytics
    traffic_res = client.get('/api/v1/analytics/traffic', headers=auth_headers)
    assert traffic_res.status_code == 200
    tr_data = traffic_res.json()['data']
    assert 'vehicle_totals' in tr_data
    assert 'system_average_speed_kmh' in tr_data

    # 3. Road Defects Analytics
    defects_res = client.get('/api/v1/analytics/road-defects', headers=auth_headers)
    assert defects_res.status_code == 200
    def_data = defects_res.json()['data']
    assert 'by_type' in def_data
    assert 'by_severity' in def_data
    assert 'resolution_rate_percent' in def_data

    # 4. Incidents Analytics
    incidents_res = client.get('/api/v1/analytics/incidents', headers=auth_headers)
    assert incidents_res.status_code == 200
    inc_data = incidents_res.json()['data']
    assert 'by_type' in inc_data
    assert 'by_severity' in inc_data

    # 5. Routes Analytics
    routes_res = client.get('/api/v1/analytics/routes', headers=auth_headers)
    assert routes_res.status_code == 200
    assert 'routes' in routes_res.json()['data']

    # 6. Heatmap GeoJSON FeatureCollection
    heatmap_res = client.get('/api/v1/analytics/heatmap?kind=incidents', headers=auth_headers)
    assert heatmap_res.status_code == 200
    hm_data = heatmap_res.json()['data']
    assert hm_data['type'] == 'FeatureCollection'
    assert 'features' in hm_data
    assert isinstance(hm_data['features'], list)
