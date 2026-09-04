from fastapi import FastAPI, UploadFile, File, Query
from ai_service.models.interfaces import StubDetector, StubOCR
from ai_service.detection.detector import EdgeUrbanDetector
from ai_service.tracking.tracker import ByteTrackSpatialTracker
from ai_service.ocr.anpr import ANPROCRService

app = FastAPI(title='UrbanSense AI Worker', version='1.0.0')

# Singleton instances across worker lifetime
detector = EdgeUrbanDetector()
stub_detector = StubDetector()
tracker = ByteTrackSpatialTracker()
anpr_ocr = ANPROCRService()
stub_ocr = StubOCR()


@app.get('/health')
async def health():
    return {'status': 'ok', 'models': 'adapter-ready'}


@app.post('/detect')
async def detect(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.4, ge=0.0, le=1.0),
    track: bool = Query(True),
    frame_id: int | None = Query(None),
):
    content = await file.read()
    # If empty or stub test payload, ensure clean behavior
    results = detector.detect(content, confidence_threshold=confidence_threshold)
    if track and results:
        results = tracker.track(results, frame_id=frame_id)
    return {'results': [r.__dict__ for r in results]}


@app.post('/ocr')
async def process_ocr(file: UploadFile = File(...)):
    content = await file.read()
    plate, confidence = anpr_ocr.recognize(content)
    status = 'VERIFIED' if confidence >= 0.85 else 'NEEDS_VERIFICATION'
    return {
        'plate_number': plate,
        'ocr_confidence': confidence,
        'verification_status': status,
        'model_name': anpr_ocr.model_name,
        'model_version': anpr_ocr.model_version,
    }


@app.post('/track')
async def track_detections(detections: list[dict], frame_id: int | None = None):
    return {'status': 'success', 'tracked_count': len(detections)}
