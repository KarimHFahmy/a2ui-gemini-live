"""FastAPI application: WebSocket bridge plus the built frontend.

Both halves of the demo live in one container, which is what Cloud Run wants:
a single service, one URL, no CORS, and the browser talks to the same origin it
was served from.

    GET  /                 the React SPA
    GET  /healthz          liveness
    GET  /api/journeys     the two advisory journeys for the landing page
    WS   /ws?journey=...   the live advisory session
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .journeys import all_journeys, get_journey
from .session import AdvisorySession

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    problems = settings.validate()
    for problem in problems:
        logger.error("Configuration problem: %s", problem)
    if settings.dotenv_path:
        logger.info("Loaded configuration from %s", settings.dotenv_path)

    if not problems:
        logger.info(
            "Adaptive Advisory backend ready (model=%s, vertex=%s, voice=%s/%s)",
            settings.model,
            settings.use_vertex_ai,
            settings.voice_name,
            settings.language_code,
        )

    # ADK reads its Gemini configuration from the environment.
    settings.apply_to_environment()

    app.state.settings = settings
    app.state.config_problems = problems

    yield


app = FastAPI(title="Adaptive Advisory Experiences", lifespan=lifespan)

_allowed_origins = get_settings().allowed_origins
if _allowed_origins:
    # Only needed when the Vite dev server runs on a different origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


@app.get("/healthz")
async def healthz() -> JSONResponse:
    settings = get_settings()
    problems = getattr(app.state, "config_problems", [])
    return JSONResponse(
        status_code=200 if not problems else 503,
        content={
            "status": "ok" if not problems else "misconfigured",
            "model": settings.model,
            "vertexAi": settings.use_vertex_ai,
            "problems": problems,
        },
    )


@app.get("/api/journeys")
async def journeys() -> dict[str, Any]:
    """Feeds the landing page: "Mein Zuhause" or "Meine Mobilität"."""
    return {
        "journeys": [
            {"id": j.id, "label": j.label, "tagline": j.tagline}
            for j in all_journeys()
        ]
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def advisory_socket(
    websocket: WebSocket,
    journey: str = Query(default="energie"),
) -> None:
    """One advisory session.

    Binary frames carry 16 kHz PCM16 microphone audio up and 24 kHz PCM16
    speech down. Text frames carry JSON control messages, transcripts and the
    A2UI stream.
    """
    await websocket.accept()

    settings = get_settings()
    problems = getattr(app.state, "config_problems", [])
    if problems:
        await websocket.send_json(
            {
                "type": "error",
                "message": (
                    "Der Dienst ist nicht vollständig konfiguriert. "
                    "Bitte prüfen Sie die Projekteinstellungen."
                ),
                "detail": "; ".join(problems),
            }
        )
        await websocket.close()
        return

    selected = get_journey(journey)
    logger.info("WebSocket accepted (journey=%s)", selected.id)

    async def audio_sink(chunk: bytes) -> None:
        await websocket.send_bytes(chunk)

    async def event_sink(event: dict[str, Any]) -> None:
        await websocket.send_json(event)

    session = AdvisorySession(
        settings=settings,
        journey=selected,
        audio_sink=audio_sink,
        event_sink=event_sink,
    )

    await websocket.send_json(
        {
            "type": "session",
            "journey": {
                "id": selected.id,
                "label": selected.label,
                "tagline": selected.tagline,
                # The advisory arc, so the client can show where the
                # conversation stands without guessing at surface ids.
                "steps": [
                    {"surfaceId": surface_id, "label": label}
                    for surface_id, label in selected.steps
                ],
            },
            "audio": {
                "inputSampleRate": settings.input_sample_rate,
                "outputSampleRate": settings.output_sample_rate,
            },
        }
    )

    session_task = asyncio.create_task(session.run())

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                session.push_audio(message["bytes"])
                continue

            raw = message.get("text")
            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Ignoring non-JSON text frame")
                continue

            kind = payload.get("type")
            if kind == "text":
                session.push_text(payload.get("text", ""))
            elif kind == "action":
                # An A2UI renderer-to-agent action: a click on a rendered card.
                session.push_renderer_action(payload.get("action") or {})
            elif kind == "close":
                break
            else:
                logger.debug("Unhandled client message type: %s", kind)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as exc:
        logger.error("WebSocket error: %s: %s", type(exc).__name__, exc)
    finally:
        session.close()
        await _drain_session(websocket, session_task)
        try:
            await websocket.close()
        except Exception:
            logger.debug("WebSocket already closed")


async def _drain_session(websocket: WebSocket, task: "asyncio.Task[None]") -> None:
    """Shuts the session task down and reports an unexpected death.

    The session normally reports its own failures. A few do not go through that
    path — an interpreter-level error during credential loading, for instance,
    raises a BaseException that no `except Exception` will see. Rather than
    widening the catch inside the session, the transport checks the outcome
    here, so the browser never just goes quiet.
    """
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return
    except BaseException as exc:  # noqa: BLE001 - last line before silence
        logger.error("Session ended unexpectedly: %s: %s", type(exc).__name__, exc)
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": (
                        "Die Beratung wurde unerwartet beendet. "
                        "Bitte laden Sie die Seite neu."
                    ),
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
        except Exception:
            logger.debug("Could not deliver the error to the client")


# ---------------------------------------------------------------------------
# Static SPA (mounted last so it never shadows the API routes)
# ---------------------------------------------------------------------------


def _mount_frontend(application: FastAPI) -> None:
    static_dir = Path(get_settings().static_dir)
    if not static_dir.is_dir():
        logger.warning(
            "Static directory %s not found — serving the API only. "
            "Run the frontend build, or use the Vite dev server.",
            static_dir,
        )
        return

    assets = static_dir / "assets"
    if assets.is_dir():
        application.mount(
            "/assets", StaticFiles(directory=assets), name="assets"
        )

    index = static_dir / "index.html"

    @application.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        """Serves static files, falling back to index.html for SPA routes."""
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    logger.info("Serving frontend from %s", static_dir.resolve())


_mount_frontend(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level=get_settings().log_level.lower(),
    )
