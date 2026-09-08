# AI UrbanSense: Production Deployment & Operations Guide

This guide covers **Steps 11 through 17** of the UrbanSense platform architecture:

```
final architecture:
                 ┌─────────────────┐
                 │  React Admin    │
                 │     Vercel      │
                 └────────┬────────┘
                          │ HTTPS / WSS
                          ▼
┌──────────────┐    ┌─────────────────┐    ┌───────────────┐
│ Flutter App  │───►│ FastAPI Backend │◄───│   AI Service  │
│ Bus Device   │    │    LIVE API     │    │ Edge / Server │
└──────────────┘    └────────┬────────┘    └───────────────┘
                             │
                    ┌────────▼────────┐
                    │   PostgreSQL    │
                    │    + PostGIS    │
                    └─────────────────┘
```

---

## STEP 11: GitHub Repository Setup & Push

1. **Verify git status & cleanliness**:
   ```bash
   git status
   ```
   Ensure `.env`, `.venv_local/`, `node_modules/`, and `.dart_tool/` are ignored.

2. **Commit all production-ready changes**:
   ```bash
   git add .
   git commit -m "feat(urbansense): production ready backend, postgis migrations, admin vercel SPA config, and e2e integration test suite"
   ```

3. **Link remote repository and push**:
   ```bash
   # Replace with your GitHub repository URL:
   git remote add origin https://github.com/<your-username>/urbansense.git
   git branch -M main
   git push -u origin main
   ```

---

## STEP 12: Free Cloud PostgreSQL + PostGIS (Neon / Supabase)

UrbanSense requires PostgreSQL with the **PostGIS** spatial extension.

### Recommended Provider: Neon Serverless Postgres (Free Tier)
1. Sign up at [Neon.tech](https://neon.tech).
2. Create a new project named `urbansense-prod`.
3. In the Neon SQL Console, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```
4. Copy your pooled connection string:
   ```
   postgresql://urbansense:<PASSWORD>@<HOST>/neondb?sslmode=require
   ```
   > [!NOTE]
   > The UrbanSense backend automatically converts `postgres://` or `postgresql://` to `postgresql+asyncpg://` and configures SSL context automatically.

5. Run database migrations:
   ```bash
   DATABASE_URL="postgresql+asyncpg://urbansense:<PASSWORD>@<HOST>/neondb?sslmode=require" alembic upgrade head
   ```

6. Seed initial test routes, buses, and admin account (optional):
   ```bash
   DATABASE_URL="postgresql+asyncpg://urbansense:<PASSWORD>@<HOST>/neondb?sslmode=require" python3 -m app.seed
   ```

---

## STEP 13: Free FastAPI Hosting (Render)

Render hosts the containerized FastAPI backend using the included `Dockerfile` and `render.yaml`.

1. Sign in to [Render.com](https://render.com).
2. Click **New +** → **Blueprint** and connect your GitHub repository.
3. Render reads [render.yaml](file:///Users/ak/Downloads/urban-/render.yaml) and configures the `urbansense-api` service.
4. Set the following Environment Variables in the Render Dashboard:
   | Variable | Value / Description |
   |---|---|
   | `DATABASE_URL` | Neon connection string with `?sslmode=require` |
   | `JWT_SECRET_KEY` | Auto-generated secure random string |
   | `REDIS_URL` | Upstash Redis connection string (or Render Redis) |
   | `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173,https://<your-admin>.vercel.app` |
   | `AI_SERVICE_URL` | URL of your deployed AI Service (see Step 16) |
   | `RATE_LIMIT_PER_MINUTE` | `120` |
5. Click **Deploy**. Your live API URL will be:
   ```
   https://urbansense-api.onrender.com
   ```
6. Verify live health check:
   ```bash
   curl -s https://urbansense-api.onrender.com/health
   # Expected response: {"status":"ok","service":"urbansense-api"}
   ```

---

## STEP 14: Admin Frontend Hosting (Vercel)

The React Admin dashboard is built with Vite and TypeScript and deployed directly to Vercel.

1. Sign in to [Vercel.com](https://vercel.com).
2. Click **Add New** → **Project** and import your GitHub repository.
3. Configure the Project Settings:
   - **Root Directory**: `Frontend/admin-dashboard`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variables:
   | Variable | Production Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://urbansense-api.onrender.com` |
   | `VITE_WS_URL` | `wss://urbansense-api.onrender.com` |
   | `VITE_MAP_PROVIDER` | `leaflet` |
   | `VITE_MOCK_MODE` | `false` |
5. Click **Deploy**.
   > [!TIP]
   > The included [vercel.json](file:///Users/ak/Downloads/urban-/Frontend/admin-dashboard/vercel.json) rewrites all SPA routes to `/index.html`, ensuring deep links (`/fleet`, `/incidents`, `/analytics`) work on refresh.

---

## STEP 15: Mobile App Production URL (Flutter)

The Flutter mobile bus client uses compile-time `--dart-define` flags to configure production endpoints without editing source code.

### 1. Build Android APK for Production:
```bash
cd Frontend/mobile
flutter build apk --release \
  --dart-define=API_BASE_URL=https://urbansense-api.onrender.com \
  --dart-define=WS_BASE_URL=wss://urbansense-api.onrender.com \
  --dart-define=MOCK_MODE=false
```
The output APK is generated at:
`Frontend/mobile/build/app/outputs/flutter-apk/app-release.apk`

### 2. Run Locally Against Production Backend:
```bash
flutter run -d chrome \
  --dart-define=API_BASE_URL=https://urbansense-api.onrender.com \
  --dart-define=WS_BASE_URL=wss://urbansense-api.onrender.com \
  --dart-define=MOCK_MODE=false
```

---

## STEP 16: AI Service Production URL

The AI microservice (`ai_service/`) processes object detection (YOLO), ANPR OCR, and ByteTrack spatial tracking.

### Hosting Options:
1. **Render / Railway / Fly.io (Cloud Web Service)**:
   - Command: `uvicorn ai_service.main:app --host 0.0.0.0 --port $PORT`
   - Set in FastAPI backend environment: `AI_SERVICE_URL=https://urbansense-ai.onrender.com`
2. **Edge Hardware (On-Bus Raspberry Pi 5 / NVIDIA Jetson Orin)**:
   - Run AI worker locally on bus edge device:
     ```bash
     uvicorn ai_service.main:app --host 0.0.0.0 --port 8001
     ```
   - Flutter App or edge daemon calls `http://localhost:8001/ai/process-frame` directly for zero-latency edge inference, then forwards detected defects to the Central FastAPI backend.

---

## STEP 17: Final End-to-End Production Verification

Run this verification script against your production deployment:

```bash
#!/bin/bash
API_URL="https://urbansense-api.onrender.com"

echo "1. Checking API Root & Health..."
curl -s "${API_URL}/health" | grep -q "ok" && echo "✅ API is Healthy" || echo "❌ API Health Failed"

echo "2. Checking Detailed System Health (DB, Redis, AI)..."
curl -s "${API_URL}/health/detailed" | jq .

echo "3. Testing User Authentication..."
LOGIN_PAYLOAD='{"email":"admin@urbansense.local","password":"ChangeMe!123"}'
TOKEN=$(curl -s -X POST "${API_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "${LOGIN_PAYLOAD}" | jq -r '.data.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✅ Authentication Successful. JWT token acquired."
else
  echo "❌ Authentication Failed."
  exit 1
fi

echo "4. Testing Fleet Bus Listing..."
curl -s -X GET "${API_URL}/api/v1/buses" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data | {total_buses: (.items | length)}'

echo "5. Testing PostGIS Nearby Locations Query..."
curl -s -X GET "${API_URL}/api/v1/locations/nearby?latitude=22.5726&longitude=88.3639&radius_km=10" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data | {nearby_buses: (.items | length)}'

echo "6. Testing Analytics Overview..."
curl -s -X GET "${API_URL}/api/v1/analytics/overview" \
  -H "Authorization: Bearer ${TOKEN}" | jq .data

echo "🎉 UrbanSense Platform End-to-End Verification Complete!"
```
