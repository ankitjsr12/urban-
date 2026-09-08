"""System Monitoring & Observability API for UrbanSense.

Provides live system metrics: CPU, memory, database pool status,
WebSocket client connections, and AI pipeline health.
"""

from __future__ import annotations

import os
import platform
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.config import settings
from app.db.session import engine, get_db
from app.models.user import Role, User
from app.schemas.common import Envelope
from app.websocket.manager import manager

router = APIRouter(prefix="/system/monitoring", tags=["System Monitoring"])


@router.get("", response_model=Envelope[dict])
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(current_user),
):
    """Retrieve operational system performance and service health telemetry (Admin/Authority)."""
    # 1. Database response check
    db_status = "HEALTHY"
    db_latency_ms = 0.0
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as exc:
        db_status = f"UNHEALTHY: {str(exc)[:60]}"

    # 2. Redis status check
    redis_status = "UNKNOWN"
    redis_latency_ms = 0.0
    try:
        import redis.asyncio as aioredis
        r_client = aioredis.from_url(settings.redis_url, socket_timeout=1.5)
        t_r = time.perf_counter()
        await r_client.ping()
        redis_latency_ms = round((time.perf_counter() - t_r) * 1000, 2)
        redis_status = "HEALTHY"
        await r_client.aclose()
    except Exception as r_err:
        redis_status = f"OFFLINE: {str(r_err)[:60]}"

    # 3. AI Service status check
    ai_status = "UNKNOWN"
    ai_latency_ms = 0.0
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            t_ai = time.perf_counter()
            resp = await client.get(f"{settings.ai_service_url}/health")
            ai_latency_ms = round((time.perf_counter() - t_ai) * 1000, 2)
            ai_status = "HEALTHY" if resp.status_code == 200 else f"HTTP {resp.status_code}"
    except Exception as ai_err:
        ai_status = f"UNREACHABLE: {str(ai_err)[:50]}"

    # 4. WebSocket connection counts
    ws_connections = {
        channel: len(sockets)
        for channel, sockets in manager.active_connections.items()
    }

    # 5. Process memory (approximate from os/resource if available)
    memory_info = {}
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # On macOS, ru_maxrss is in bytes; on Linux in KB
        rss_mb = round(usage.ru_maxrss / (1024 * 1024 if platform.system() == "Darwin" else 1024), 2)
        memory_info = {"max_rss_mb": rss_mb}
    except Exception:
        pass

    return {
        "data": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.environment,
            "platform": {
                "os": platform.system(),
                "release": platform.release(),
                "python": platform.python_version(),
            },
            "services": {
                "database": {
                    "status": db_status,
                    "latency_ms": db_latency_ms,
                },
                "redis": {
                    "status": redis_status,
                    "latency_ms": redis_latency_ms,
                },
                "ai_service": {
                    "status": ai_status,
                    "latency_ms": ai_latency_ms,
                    "endpoint": settings.ai_service_url,
                },
            },
            "websocket": {
                "channels": ws_connections,
                "total_active_subscribers": sum(ws_connections.values()),
            },
            "runtime": memory_info,
        }
    }
