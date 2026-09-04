import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"intel.tester.{uuid.uuid4().hex[:6]}@urbansense.local"
    client.post(
        '/api/v1/auth/register',
        json={'name': 'Intel Officer', 'email': email, 'password': 'Password123!', 'role': 'AUTHORITY'},
    )
    res = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Password123!'})
    token = res.json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_road_defect_and_incident_lifecycle(auth_headers):
    # 1. Create Road Defect
    defect_res = client.post(
        '/api/v1/road-defects',
        headers=auth_headers,
        json={
            'defect_type': 'POTHOLE',
            'severity': 'HIGH',
            'status': 'OPEN',
            'description': 'Severe pothole in center lane',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'confidence': 0.95,
        },
    )
    assert defect_res.status_code == 201
    defect_id = defect_res.json()['data']['id']

    # 2. Get Defect by ID
    get_def_res = client.get(f'/api/v1/road-defects/{defect_id}', headers=auth_headers)
    assert get_def_res.status_code == 200

    # 3. Update Defect Status to RESOLVED
    up_def_res = client.patch(
        f'/api/v1/road-defects/{defect_id}/status',
        headers=auth_headers,
        json={'status': 'RESOLVED'},
    )
    assert up_def_res.status_code == 200
    assert up_def_res.json()['data']['status'] == 'RESOLVED'

    # 4. Create Incident
    inc_res = client.post(
        '/api/v1/incidents',
        headers=auth_headers,
        json={
            'incident_type': 'ROAD_HAZARD',
            'priority': 'HIGH',
            'status': 'OPEN',
            'title': 'Fallen tree on highway',
            'description': 'Blocking two lanes',
            'latitude': 37.7755,
            'longitude': -122.4185,
            'confidence': 0.89,
        },
    )
    assert inc_res.status_code == 201
    inc_id = inc_res.json()['data']['id']

    # 5. Upload Evidence for Incident
    fake_img = io.BytesIO(b'fake-image-binary-data')
    upload_res = client.post(
        '/api/v1/evidence/upload',
        headers=auth_headers,
        data={'incident_id': inc_id},
        files={'file': ('scene.jpg', fake_img, 'image/jpeg')},
    )
    assert upload_res.status_code == 200
    assert 'file_url' in upload_res.json()['data']
    assert 'checksum' in upload_res.json()['data']

    # 6. Update Incident Status
    inc_stat_res = client.patch(
        f'/api/v1/incidents/{inc_id}/status',
        headers=auth_headers,
        json={'status': 'ACKNOWLEDGED'},
    )
    assert inc_stat_res.status_code == 200
    assert inc_stat_res.json()['data']['status'] == 'ACKNOWLEDGED'

    # 7. Query nearby incidents
    nearby_inc_res = client.get(
        '/api/v1/incidents/nearby?latitude=37.7750&longitude=-122.4190&radius_km=5.0',
        headers=auth_headers,
    )
    assert nearby_inc_res.status_code == 200
    assert nearby_inc_res.json()['data']['total'] >= 1


def test_citizen_reports_and_notifications(auth_headers):
    # 1. Submit Citizen Report
    rep_res = client.post(
        '/api/v1/reports',
        headers=auth_headers,
        json={
            'report_type': 'WATERLOGGING',
            'title': 'Flooded bus stop',
            'description': 'Water accumulation near curb',
            'latitude': 37.7760,
            'longitude': -122.4170,
            'priority': 'MEDIUM',
        },
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()['data']['id']

    # 2. Get My Reports
    my_rep_res = client.get('/api/v1/reports/my', headers=auth_headers)
    assert my_rep_res.status_code == 200
    assert my_rep_res.json()['data']['total'] >= 1

    # 3. Create Notification
    me_res = client.get('/api/v1/auth/me', headers=auth_headers)
    user_id = me_res.json()['data']['id']

    notif_res = client.post(
        '/api/v1/notifications',
        headers=auth_headers,
        json={
            'user_id': user_id,
            'notification_type': 'ALERT',
            'title': 'Route Detour Active',
            'message': 'Buses on Route 1 rerouted due to road work',
        },
    )
    assert notif_res.status_code == 201
    notif_id = notif_res.json()['data']['id']

    # 4. Mark Notification as Read
    read_res = client.patch(f'/api/v1/notifications/{notif_id}/read', headers=auth_headers)
    assert read_res.status_code == 200
    assert read_res.json()['data']['is_read'] is True
