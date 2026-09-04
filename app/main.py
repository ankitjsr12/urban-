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

app = FastAPI(
    title=settings.app_name,
    version='1.0.0',
    description='AI-Powered Mobile Urban Intelligence Platform Backend for Public Transport Fleets',
    openapi_tags=[
        {'name': 'Authentication', 'description': 'User registration, authentication, token refresh, and profile management'},
        {'name': 'Urban Intelligence', 'description': 'Fleet management, GPS telemetry, AI detections, defects, incidents, and offline sync'},
        {'name': 'Analytics', 'description': 'Geospatial and system-wide intelligence aggregations and heatmaps'},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

limiter = Limiter(key_func=get_remote_address, default_limits=[f'{settings.rate_limit_per_minute}/minute'])
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={'success': False, 'error': {'code': 'RATE_LIMITED', 'message': 'Too many requests'}},
    )


@app.get('/health', tags=['Health'])
async def health():
    return {'status': 'ok', 'service': 'urbansense-api'}


@app.get('/ready', tags=['Health'])
async def ready():
    return {'status': 'ready'}


# Include versioned API routers
app.include_router(auth_router, prefix='/api/v1')
app.include_router(crud_router, prefix='/api/v1')
app.include_router(analytics_router, prefix='/api/v1')


# Real-time WebSocket Channels
@app.websocket('/live/{channel}')
async def live_channel(websocket: WebSocket, channel: str):
    valid_channels = {'buses', 'incidents', 'detections', 'traffic'}
    if channel not in valid_channels:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
