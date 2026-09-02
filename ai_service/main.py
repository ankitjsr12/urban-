from fastapi import FastAPI, UploadFile, File
from ai_service.models.interfaces import StubDetector, StubOCR
app=FastAPI(title='UrbanSense AI Worker')
detector=StubDetector(); ocr=StubOCR()
@app.get('/health')
async def health(): return {'status':'ok','models':'adapter-ready'}
@app.post('/detect')
async def detect(file:UploadFile=File(...)): return {'results':[r.__dict__ for r in detector.detect(await file.read())]}
@app.post('/ocr')
async def process_ocr(file:UploadFile=File(...)):
    plate,confidence=ocr.recognize(await file.read()); return {'plate_number':plate,'ocr_confidence':confidence,'verification_status':'VERIFIED' if confidence>=0.85 else 'NEEDS_VERIFICATION'}
