import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def admin_token():
    email = f"admin.{uuid.uuid4().hex[:6]}@urbansense.local"
    client.post(
        '/api/v1/auth/register',
        json={'name': 'Admin User', 'email': email, 'password': 'AdminPassword123!', 'role': 'ADMIN'},
    )
    res = client.post('/api/v1/auth/login', json={'email': email, 'password': 'AdminPassword123!'})
    return res.json()['data']['access_token']


def test_bus_lifecycle(admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    reg_num = f"WB-{uuid.uuid4().hex[:4].upper()}-9999"

    # 1. Create Bus
    payload = {
        'registration_number': reg_num,
        'fleet_number': f"BUS-{uuid.uuid4().hex[:4].upper()}",
        'operator_name': 'Green Line Transit',
        'capacity': 70,
        'status': 'ACTIVE',
    }
    create_res = client.post('/api/v1/buses', headers=headers, json=payload)
    assert create_res.status_code == 201
    bus_data = create_res.json()['data']
    bus_id = bus_data['id']
    assert bus_data['registration_number'] == reg_num

    # 2. Get Bus by ID
    get_res = client.get(f'/api/v1/buses/{bus_id}', headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()['data']['id'] == bus_id

    # 3. Update Bus
    update_res = client.patch(f'/api/v1/buses/{bus_id}', headers=headers, json={'status': 'MAINTENANCE', 'capacity': 75})
    assert update_res.status_code == 200
    assert update_res.json()['data']['status'] == 'MAINTENANCE'
    assert update_res.json()['data']['capacity'] == 75

    # 4. Bus status endpoint
    status_res = client.get(f'/api/v1/buses/{bus_id}/status', headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()['data']['status'] == 'MAINTENANCE'

    # 5. List Buses
    list_res = client.get('/api/v1/buses?status=MAINTENANCE', headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()['data']['total'] >= 1


def test_driver_and_route_management(admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}

    # 1. Create Route
    r_num = f"R-{uuid.uuid4().hex[:4].upper()}"
    route_res = client.post(
        '/api/v1/routes',
        headers=headers,
        json={
            'route_number': r_num,
            'name': 'North Cross Rapid Line',
            'origin': 'North Hub',
            'destination': 'South Hub',
            'geometry_wkt': 'LINESTRING(-122.4194 37.7749, -122.4200 37.7800)',
        },
    )
    assert route_res.status_code == 201
    route_id = route_res.json()['data']['id']

    # 2. Register Driver User & Driver Profile
    drv_email = f"driver.{uuid.uuid4().hex[:6]}@urbansense.local"
    reg_res = client.post(
        '/api/v1/auth/register',
        json={'name': 'Fleet Driver 1', 'email': drv_email, 'password': 'DriverPassword123!', 'role': 'DRIVER'},
    )
    drv_user_id = reg_res.json()['data']['id']

    emp_id = f"EMP-{uuid.uuid4().hex[:4].upper()}"
    lic_num = f"DL-{uuid.uuid4().hex[:6].upper()}"
    driver_res = client.post(
        '/api/v1/drivers',
        headers=headers,
        json={'user_id': drv_user_id, 'employee_id': emp_id, 'license_number': lic_num, 'status': 'ACTIVE'},
    )
    assert driver_res.status_code == 201
    driver_id = driver_res.json()['data']['id']

    # 3. Create a Bus and assign Driver to it
    bus_res = client.post(
        '/api/v1/buses',
        headers=headers,
        json={'registration_number': f"WB-{uuid.uuid4().hex[:4].upper()}", 'assigned_route_id': route_id},
    )
    bus_id = bus_res.json()['data']['id']

    assign_res = client.post(
        f'/api/v1/drivers/{driver_id}/assign',
        headers=headers,
        json={'bus_id': bus_id},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()['data']['assigned_bus_id'] == bus_id
