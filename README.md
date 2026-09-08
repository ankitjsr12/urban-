# AI UrbanSense Central Backend

A FastAPI backend and modular AI-service foundation for public-transport urban intelligence. It provides JWT/RBAC authentication, fleet and GPS ingestion, AI detections, road defects, traffic and vehicle records, incidents, citizen reports, analytics, GeoJSON heatmaps, and an adapter boundary for YOLO/OCR/tracking.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`, Swagger at `/docs`, ReDoc at `/redoc`, MinIO at `http://localhost:9001`, and the AI worker is available with `docker compose --profile worker up --build`.

## Database and seed data

```bash
alembic upgrade head
python -m app.seed
```

The local Compose database is PostGIS-enabled. The current service keeps geographic coordinates in validated latitude/longitude columns and exposes GeoJSON heatmap output; a production migration can add native `geometry(Point,4326)` columns and GiST indexes without changing client contracts.

## Authentication

Register at `POST /api/v1/auth/register`, log in at `POST /api/v1/auth/login`, and send `Authorization: Bearer <access_token>` to protected endpoints. Roles are `ADMIN`, `AUTHORITY`, `DRIVER`, and `CITIZEN`; privileged endpoints enforce role and ownership checks.

## Configuration and production notes

All secrets and provider settings are environment variables. MinIO is the local storage target; an S3-compatible storage adapter should be enabled for production evidence. AI weights are intentionally not committed: implement a YOLO/OpenCV/ByteTrack/PaddleOCR provider behind `ai_service/models/interfaces.py` and configure model name/version in every result. Low-confidence OCR is returned as `NEEDS_VERIFICATION`. Large media belongs in object storage, not PostgreSQL. Use a reverse proxy with TLS, managed PostgreSQL/PostGIS, Redis, object storage, and a long-lived WebSocket-capable deployment for production.

## API scope

All routes are versioned under `/api/v1`. The backend deliberately does not implement the Flutter mobile application or React admin dashboard; their integration contract is the generated OpenAPI document.
