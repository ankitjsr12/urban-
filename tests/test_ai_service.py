import io
from fastapi.testclient import TestClient
from ai_service.main import app as ai_app

ai_client = TestClient(ai_app)

def test_ai_worker_health():
    response = ai_client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['models'] == 'adapter-ready'

def test_ai_detect():
    fake_image = io.BytesIO(b'dummy-image-content')
    response = ai_client.post('/detect', files={'file': ('test.jpg', fake_image, 'image/jpeg')})
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data
    assert isinstance(data['results'], list)


def test_ai_ocr():
    fake_image = io.BytesIO(b'dummy-plate-image')
    response = ai_client.post('/ocr', files={'file': ('plate.jpg', fake_image, 'image/jpeg')})
    assert response.status_code == 200
    data = response.json()
    assert 'plate_number' in data
    assert 'ocr_confidence' in data
    assert data['verification_status'] in ('VERIFIED', 'NEEDS_VERIFICATION')
