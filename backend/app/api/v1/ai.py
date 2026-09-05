import logging
from typing import Any
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


@router.get("/health")
async def ai_service_health() -> dict[str, Any]:
    """Check connectivity and health of the external AI microservice."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ai_service_url}/health")
            if resp.status_code == 200:
                return {"status": "ok", "ai_service": resp.json()}
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service returned unexpected status: {resp.status_code}",
            )
    except httpx.RequestError as exc:
        logger.error(f"Cannot connect to AI service at {settings.ai_service_url}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable at {settings.ai_service_url}: {str(exc)}",
        )


@router.post("/detect")
async def proxy_detect(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.4, ge=0.0, le=1.0),
    track: bool = Query(True),
    frame_id: int | None = Query(None),
) -> dict[str, Any]:
    """Forward image to AI service for YOLO object detection."""
    content = await file.read()
    files = {"file": (file.filename or "frame.jpg", content, file.content_type or "image/jpeg")}
    params = {"confidence_threshold": confidence_threshold, "track": track}
    if frame_id is not None:
        params["frame_id"] = frame_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/ai/detect",
                files=files,
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.text,
            )
    except httpx.RequestError as exc:
        logger.error(f"AI detection request failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service connection failed: {str(exc)}",
        )


@router.post("/ocr")
async def proxy_ocr(file: UploadFile = File(...)) -> dict[str, Any]:
    """Forward image to AI service for PaddleOCR text recognition."""
    content = await file.read()
    files = {"file": (file.filename or "crop.jpg", content, file.content_type or "image/jpeg")}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/ai/ocr",
                files=files,
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.text,
            )
    except httpx.RequestError as exc:
        logger.error(f"AI OCR request failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service connection failed: {str(exc)}",
        )


@router.post("/anpr")
async def proxy_anpr(file: UploadFile = File(...)) -> dict[str, Any]:
    """Forward vehicle crop to AI service for ANPR license plate recognition."""
    content = await file.read()
    files = {"file": (file.filename or "vehicle.jpg", content, file.content_type or "image/jpeg")}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/ai/anpr",
                files=files,
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.text,
            )
    except httpx.RequestError as exc:
        logger.error(f"AI ANPR request failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service connection failed: {str(exc)}",
        )


@router.post("/process-frame")
async def proxy_process_frame(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.4, ge=0.0, le=1.0),
    track: bool = Query(True),
    frame_id: int | None = Query(None),
) -> dict[str, Any]:
    """Forward video frame to AI service for full multi-stage detection + ANPR pipeline."""
    content = await file.read()
    files = {"file": (file.filename or "frame.jpg", content, file.content_type or "image/jpeg")}
    params = {"confidence_threshold": confidence_threshold, "track": track}
    if frame_id is not None:
        params["frame_id"] = frame_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/ai/process-frame",
                files=files,
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.text,
            )
    except httpx.RequestError as exc:
        logger.error(f"AI process-frame request failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service connection failed: {str(exc)}",
        )
