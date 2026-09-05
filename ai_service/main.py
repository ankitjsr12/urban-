import time
from fastapi import FastAPI, UploadFile, File, Query
from ai_service.models.interfaces import StubDetector, StubOCR
from ai_service.detection.detector import EdgeUrbanDetector
from ai_service.tracking.tracker import ByteTrackSpatialTracker
from ai_service.ocr.anpr import ANPROCRService
from ai_service.vision.opencv_adapter import OpenCVAdapter

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
@app.post('/ai/detect')
async def detect(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.4, ge=0.0, le=1.0),
    track: bool = Query(True),
    frame_id: int | None = Query(None),
):
    content = await file.read()
    results = detector.detect(content, confidence_threshold=confidence_threshold)
    if track and results:
        results = tracker.track(results, frame_id=frame_id)
    
    detections_list = [
        {
            'class_name': r.label,
            'confidence': r.confidence,
            'bbox': [
                r.bounding_box.get('x_min', 0.0),
                r.bounding_box.get('y_min', 0.0),
                r.bounding_box.get('x_max', 0.0),
                r.bounding_box.get('y_max', 0.0),
            ] if r.bounding_box else [],
        }
        for r in results
    ]
    return {
        'results': [r.__dict__ for r in results],
        'detections': detections_list,
    }


@app.post('/ocr')
@app.post('/ai/ocr')
async def process_ocr(file: UploadFile = File(...)):
    content = await file.read()
    plate, confidence = anpr_ocr.recognize(content)
    status = 'VERIFIED' if confidence >= 0.85 else 'NEEDS_VERIFICATION'
    return {
        'text': plate,
        'confidence': confidence,
        'plate_number': plate,
        'ocr_confidence': confidence,
        'verification_status': status,
        'model_name': anpr_ocr.model_name,
        'model_version': anpr_ocr.model_version,
    }


@app.post('/anpr')
@app.post('/ai/anpr')
async def process_anpr(file: UploadFile = File(...)):
    content = await file.read()
    plate, confidence = anpr_ocr.recognize(content)
    status = 'VERIFIED' if confidence >= 0.85 else 'NEEDS_VERIFICATION'
    return {
        'plate_number': plate,
        'confidence': confidence,
        'verification_status': status,
        'model_name': anpr_ocr.model_name,
        'model_version': anpr_ocr.model_version,
    }


@app.post('/process-frame')
@app.post('/ai/process-frame')
async def process_frame(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.4, ge=0.0, le=1.0),
    track: bool = Query(True),
    frame_id: int | None = Query(None),
):
    start_time = time.time()
    content = await file.read()
    
    # 1. Decode image via OpenCV
    img, _ = OpenCVAdapter.decode_image(content)

    # 2. YOLO Object Detection
    results = detector.detect(content, confidence_threshold=confidence_threshold)
    if track and results:
        results = tracker.track(results, frame_id=frame_id)

    # 3. Crop detected objects when applicable for OCR
    ocr_items = []
    if img is not None and results:
        for r in results:
            if r.bounding_box:
                cropped = OpenCVAdapter.crop_image(img, r.bounding_box)
                if cropped is not None and cropped.size > 0:
                    text, conf = anpr_ocr.ocr_adapter.extract_text(cropped)
                    if text:
                        ocr_items.append({'text': text, 'confidence': round(conf, 4)})

    # Fallback to full image / ANPR if no crop yielded text
    if not ocr_items:
        plate, plate_conf = anpr_ocr.recognize(content)
        if plate:
            ocr_items.append({'text': plate, 'confidence': round(plate_conf, 4)})

    proc_time_ms = int((time.time() - start_time) * 1000)

    detections_list = [
        {
            'class_name': r.label,
            'confidence': r.confidence,
            'bbox': [
                r.bounding_box.get('x_min', 0.0),
                r.bounding_box.get('y_min', 0.0),
                r.bounding_box.get('x_max', 0.0),
                r.bounding_box.get('y_max', 0.0),
            ] if r.bounding_box else [],
        }
        for r in results
    ]

    return {
        'results': [r.__dict__ for r in results],
        'detections': detections_list,
        'ocr': ocr_items,
        'processing_time_ms': proc_time_ms,
    }


@app.post('/track')
async def track_detections(detections: list[dict], frame_id: int | None = None):
    return {'status': 'success', 'tracked_count': len(detections)}
