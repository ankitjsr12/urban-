import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_registration_and_login_flow():
    # 1. Register new user
    reg_payload = {
        'name': 'Test Operator',
        'email': 'operator.test@urbansense.local',
        'password': 'StrongPassword123!',
        'role': 'AUTHORITY',
        'phone': '+15551112222',
    }
    res = client.post('/api/v1/auth/register', json=reg_payload)
    assert res.status_code == 201
    data = res.json()['data']
    assert data['email'] == reg_payload['email']
    assert data['role'] == 'AUTHORITY'
    assert data['is_active'] is True

    # 2. Duplicate registration fails with 409
    dup_res = client.post('/api/v1/auth/register', json=reg_payload)
    assert dup_res.status_code == 409

    # 3. Login with correct credentials
    login_res = client.post(
        '/api/v1/auth/login',
        json={'email': reg_payload['email'], 'password': 'StrongPassword123!'},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()['data']
    assert 'access_token' in token_data
    assert 'refresh_token' in token_data
    assert token_data['token_type'] == 'bearer'

    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']

    # 4. Access /auth/me with access token
    me_res = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {access_token}'})
    assert me_res.status_code == 200
    assert me_res.json()['data']['email'] == reg_payload['email']

    # 5. Refresh token flow
    refresh_res = client.post('/api/v1/auth/refresh', json={'refresh_token': refresh_token})
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()['data']
    assert 'access_token' in new_tokens
    assert 'refresh_token' in new_tokens

    # 6. Logout flow
    logout_res = client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': f'Bearer {access_token}'},
        json={'refresh_token': new_tokens['refresh_token']},
    )
    assert logout_res.status_code == 200

    # 7. Revoked refresh token is rejected
    stale_refresh_res = client.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': new_tokens['refresh_token']},
    )
    assert stale_refresh_res.status_code == 401


def test_auth_invalid_credentials():
    res = client.post(
        '/api/v1/auth/login',
        json={'email': 'nonexistent@urbansense.local', 'password': 'RandomPassword!'},
    )
    assert res.status_code == 401


def test_rbac_authorization_enforcement():
    # Register a CITIZEN user
    citizen_payload = {
        'name': 'Regular Citizen',
        'email': 'citizen.regular@urbansense.local',
        'password': 'CitizenPassword123!',
        'role': 'CITIZEN',
    }
    client.post('/api/v1/auth/register', json=citizen_payload)
    login_res = client.post(
        '/api/v1/auth/login',
        json={'email': citizen_payload['email'], 'password': 'CitizenPassword123!'},
    )
    citizen_token = login_res.json()['data']['access_token']

    # Attempt to access Admin-only / Authority-only endpoints (e.g. creating a bus)
    bus_payload = {
        'registration_number': 'CA99ZZ9999',
        'capacity': 50,
    }
    denied_res = client.post(
        '/api/v1/buses',
        headers={'Authorization': f'Bearer {citizen_token}'},
        json=bus_payload,
    )
    assert denied_res.status_code == 403
