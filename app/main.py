from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.crud import router as crud_router
from app.api.v1.analytics import router as analytics_router
from app.websocket.manager import manager
app=FastAPI(title=settings.app_name,version='1.0.0',description='Secure urban intelligence backend for public transport fleets')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
limiter=Limiter(key_func=get_remote_address,default_limits=[f'{settings.rate_limit_per_minute}/minute'])
app.state.limiter=limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc): return JSONResponse(status_code=429,content={'success':False,'error':{'code':'RATE_LIMITED','message':'Too many requests'}})
@app.get('/health')
async def health(): return {'status':'ok','service':'urbansense-api'}
@app.get('/ready')
async def ready(): return {'status':'ready'}
app.include_router(auth_router,prefix='/api/v1'); app.include_router(crud_router,prefix='/api/v1'); app.include_router(analytics_router,prefix='/api/v1')

@app.websocket('/live/{channel}')
async def live(websocket: WebSocket, channel: str):
    if channel not in {'buses','incidents','detections','traffic'}:
        await websocket.close(code=1008); return
    await manager.connect(websocket, channel)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket, channel)
