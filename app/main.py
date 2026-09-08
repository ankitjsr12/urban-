import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.crud import router as crud_router
from app.api.v1.fleet_health import router as fleet_health_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.reports import router as reports_router
from app.api.v1.route_intelligence import router as route_intelligence_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.db.session import engine
from app.websocket.manager import manager

logger = logging.getLogger("urbansense.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup table initialization and shutdown resource cleanup."""
    logger.info("Initializing UrbanSense platform...")
    try:
        from app.models import Base
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            except Exception as pe:
                logger.info("PostGIS extension check skipped or not permitted: %s", pe)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema validated and initialized successfully.")
    except Exception as exc:
        logger.warning("Database schema auto-creation notice: %s", exc)

    yield

    logger.info("Shutting down UrbanSense platform...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Powered Mobile Urban Intelligence Platform Backend for Public Transport Fleets",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, authentication, token refresh, and profile management"},
        {"name": "Users", "description": "Administrative user management, role assignments, and account deactivation"},
        {"name": "Urban Intelligence", "description": "Fleet management, GPS telemetry, AI detections, defects, incidents, and offline sync"},
        {"name": "Fleet Health", "description": "Operational telemetry and sensor health monitoring for fleet vehicles"},
        {"name": "Route Intelligence", "description": "Transit corridor speed profiles, defect density, and congestion indices"},
        {"name": "Analytics", "description": "Geospatial and system-wide intelligence aggregations and heatmaps"},
        {"name": "Reports", "description": "Automated aggregation and CSV/JSON report exports"},
        {"name": "System Monitoring", "description": "Service observability, memory, latency, and WebSocket statistics"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.onrender\.com|.*\.vercel\.app|.*\.trycloudflare\.com)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}},
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the request.",
            },
        },
    )


@app.get("/", tags=["Root"])
async def root():
    return {"status": "ok", "service": "urbansense-api", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "urbansense-api"}


@app.get("/health/detailed", tags=["Health"])
async def detailed_health():
    """Comprehensive health check verifying Database, Redis, and AI Service connectivity."""
    components = {}
    overall_status = "healthy"

    # 1. Database check
    t0 = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_lat = round((time.perf_counter() - t0) * 1000, 2)
        components["database"] = {"status": "up", "latency_ms": db_lat}
    except Exception as db_err:
        components["database"] = {"status": "down", "error": str(db_err)[:80]}
        overall_status = "degraded"

    # 2. Redis check
    t_r = time.perf_counter()
    try:
        import redis.asyncio as aioredis
        r_client = aioredis.from_url(settings.redis_url, socket_timeout=1.5)
        await r_client.ping()
        await r_client.aclose()
        r_lat = round((time.perf_counter() - t_r) * 1000, 2)
        components["redis"] = {"status": "up", "latency_ms": r_lat}
    except Exception as r_err:
        components["redis"] = {"status": "down", "error": str(r_err)[:80]}
        overall_status = "degraded"

    # 3. AI Service check
    t_ai = time.perf_counter()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ai_service_url}/health")
            ai_lat = round((time.perf_counter() - t_ai) * 1000, 2)
            if resp.status_code == 200:
                components["ai_service"] = {"status": "up", "latency_ms": ai_lat}
            else:
                components["ai_service"] = {"status": "degraded", "http_status": resp.status_code}
                overall_status = "degraded"
    except Exception as ai_err:
        components["ai_service"] = {"status": "down", "error": str(ai_err)[:80]}
        # AI service down degrades platform but does not take down core API
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "urbansense-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": components,
    }


@app.get("/ready", tags=["Health"])
async def ready():
    return {"status": "ready"}


@app.post("/report", tags=["Health"])
@app.post("/predict", tags=["Health"])
async def legacy_report_endpoint():
    return {"status": "ok", "service": "urbansense-api"}


# Include versioned API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(fleet_health_router, prefix="/api/v1")
app.include_router(route_intelligence_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(crud_router, prefix="/api/v1")


# Real-time WebSocket Channels
@app.websocket("/live/{channel}")
async def live_channel(websocket: WebSocket, channel: str):
    valid_channels = {"buses", "incidents", "detections", "traffic"}
    if channel not in valid_channels:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
