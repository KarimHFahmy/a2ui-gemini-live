# syntax=docker/dockerfile:1
#
# One image, both halves: the Vite build produces the SPA, the Python runtime
# serves it alongside the WebSocket bridge. Cloud Run gets a single service and
# the browser talks to the same origin it was served from — no CORS, no second
# deployment to keep in sync.

# ---------------------------------------------------------------------------
# Stage 1 — build the frontend
# ---------------------------------------------------------------------------
FROM node:22-alpine AS frontend

WORKDIR /build

# Dependencies first so a source-only change reuses the install layer.
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=optional 2>/dev/null || npm install --omit=optional

COPY frontend/ ./
# Built into a stage-local directory rather than vite.config.ts's default
# (`../backend/static`, convenient for local development) so the copy below
# does not depend on paths outside the build context.
RUN npm run build -- --outDir dist --emptyOutDir

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    STATIC_DIR=/app/static

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /build/dist ./static

# Cloud Run terminates as a non-root user by preference; nothing here needs
# write access to the image.
RUN useradd --create-home --uid 1001 advisory \
    && chown -R advisory:advisory /app
USER advisory

EXPOSE 8080

# Long-lived WebSockets: a single worker keeps session state in one process,
# and Cloud Run scales by adding instances rather than workers.
CMD exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --timeout-graceful-shutdown 20 \
    --ws-ping-interval 20 \
    --ws-ping-timeout 20
