from fastapi.testclient import TestClient
from app.main import app
from app.core.security import hash_password, verify_password, create_token, decode_token
from datetime import timedelta

client = TestClient(app)

def test_health():
    response=client.get('/health')
    assert response.status_code==200
    assert response.json()['status']=='ok'

def test_openapi_and_channels():
    spec=client.get('/openapi.json').json()
    assert '/api/v1/auth/login' in spec['paths']
    assert '/api/v1/evidence/upload' in spec['paths']
    assert any(route.path=='/live/{channel}' for route in app.routes)

def test_password_hashing():
    hashed=hash_password('CorrectHorseBatteryStaple!')
    assert hashed != 'CorrectHorseBatteryStaple!'
    assert verify_password('CorrectHorseBatteryStaple!',hashed)
    assert not verify_password('wrong',hashed)

def test_jwt_claims():
    token=create_token('user-id','CITIZEN','access',timedelta(minutes=5))
    payload=decode_token(token)
    assert payload['sub']=='user-id'
    assert payload['kind']=='access'

def test_detection_confidence_validation():
    response=client.post('/api/v1/detections',json={'confidence':1.5,'model_name':'x','model_version':'1','detection_type':'POTHOLE'})
    assert response.status_code in (401,422)
