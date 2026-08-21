"""Gemini Live session orchestration over Vertex AI.

One :class:`AdvisorySession` per browser connection. It owns the Live API
websocket, pumps audio in both directions, executes the journey's advisory
tools and turns their results into A2UI messages for the renderer.

The model never emits UI JSON itself. It calls semantic tools ("show the
suitability check"), the journey composes the surface from deterministic
domain calculations, and only that composed surface reaches the browser. That
is the guardrail the briefing asks for: a fixed catalogue of approved
components, and no invented numbers.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import traceback
from typing import Any, Awaitable, Callable

from google import genai
from google.genai import types

from .a2ui.protocol import A2uiMessage
from .config import Settings
from .journeys import Journey

logger = logging.getLogger(__name__)

AudioSink = Callable[[bytes], Awaitable[None]]
EventSink = Callable[[dict[str, Any]], Awaitable[None]]


def build_client(settings: Settings) -> genai.Client:
    """Creates the genai client.

    On Vertex AI authentication comes from Application Default Credentials, so
    on Cloud Run the service account is picked up with no key material in the
    image. The API-key path exists only for local development.
    """
    if settings.use_vertex_ai:
        logger.info(
            "Using Vertex AI (project=%s, location=%s)",
            settings.project,
            settings.location,
        )
        return genai.Client(
            vertexai=True,
            project=settings.project,
            location=settings.location,
        )
    logger.info("Using the Gemini Developer API (AI Studio)")
    return genai.Client(api_key=settings.api_key)


def build_config(settings: Settings, journey: Journey) -> types.LiveConnectConfig:
    """Assembles the LiveConnectConfig for one journey.

    Optional native-audio features are attached defensively: model support for
    them moves during preview, and a rejected config would take the whole
    session down rather than degrading one feature.
    """
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(**decl)
                for decl in journey.function_declarations
            ]
        )
    ]

    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(
            parts=[types.Part(text=journey.system_instruction)]
        ),
        speech_config=types.SpeechConfig(
            language_code=settings.language_code,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=settings.voice_name
                )
            ),
        ),
        # Both transcripts are surfaced live in the UI — the briefing asks for
        # a visible transcript, and it also makes the demo debuggable on stage.
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        tools=tools,
    )

    if settings.affective_dialog:
        _try_set(config, "enable_affective_dialog", True)
    if settings.proactive_audio:
        _try_set(config, "proactivity", types.ProactivityConfig(proactive_audio=True))

    return config


def _try_set(config: types.LiveConnectConfig, field: str, value: Any) -> None:
    """Sets an optional config field, logging instead of failing if unsupported."""
    try:
        setattr(config, field, value)
    except Exception as exc:  # pragma: no cover - depends on SDK version
        logger.warning("Live config field %r not applied: %s", field, exc)


class AdvisorySession:
    """Drives one advisory conversation."""

    def __init__(
        self,
        *,
        settings: Settings,
        journey: Journey,
        client: genai.Client,
        audio_sink: AudioSink,
        event_sink: EventSink,
    ) -> None:
        self._settings = settings
        self._journey = journey
        self._client = client
        self._audio_sink = audio_sink
        self._event_sink = event_sink

        self._state = journey.state_factory()
        #: Surfaces already on screen, so a repeated tool call updates in place.
        self._live_surfaces: set[str] = set()

        self._audio_in: asyncio.Queue[bytes] = asyncio.Queue()
        self._text_in: asyncio.Queue[str] = asyncio.Queue()
        self._closing = asyncio.Event()

    # -- inbound from the browser -----------------------------------------

    def push_audio(self, chunk: bytes) -> None:
        self._audio_in.put_nowait(chunk)

    def push_text(self, text: str) -> None:
        self._text_in.put_nowait(text)

    def push_renderer_action(self, action: dict[str, Any]) -> None:
        """Feeds a UI interaction back into the conversation.

        A click on a scenario card is a turn in the dialogue, not a side
        channel: the agent should react to it in speech the same way it reacts
        to a spoken sentence.
        """
        name = action.get("name", "")
        context = action.get("context") or {}
        self._text_in.put_nowait(
            "[Interaktion auf dem Bildschirm] "
            f"Die Person hat '{name}' ausgelöst. Kontext: {context}. "
            "Reagiere kurz und passend darauf."
        )

    def close(self) -> None:
        self._closing.set()

    # -- the session loop --------------------------------------------------

    async def run(self) -> None:
        """Opens the Live connection and runs until the browser disconnects."""
        config = build_config(self._settings, self._journey)

        try:
            async with self._client.aio.live.connect(
                model=self._settings.model, config=config
            ) as session:
                logger.info("Live session open (journey=%s)", self._journey.id)
                await self._event_sink({"type": "status", "status": "verbunden"})

                # Kick off the greeting so the client hears a voice immediately.
                await session.send_client_content(
                    turns=types.Content(
                        role="user", parts=[types.Part(text=self._journey.opener)]
                    )
                )

                tasks = [
                    asyncio.create_task(self._pump_audio(session), name="audio-in"),
                    asyncio.create_task(self._pump_text(session), name="text-in"),
                    asyncio.create_task(self._receive(session), name="receive"),
                    asyncio.create_task(self._await_close(), name="close-watch"),
                ]
                done, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    exc = task.exception()
                    if exc is not None:
                        raise exc

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Live session failed: %s: %s\n%s",
                type(exc).__name__,
                exc,
                traceback.format_exc(),
            )
            await self._event_sink(
                {
                    "type": "error",
                    "message": (
                        "Die Verbindung zum Sprachdienst ist abgebrochen. "
                        "Bitte laden Sie die Seite neu."
                    ),
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
        finally:
            logger.info("Live session closed (journey=%s)", self._journey.id)
            await self._event_sink({"type": "status", "status": "beendet"})

    async def _await_close(self) -> None:
        await self._closing.wait()

    async def _pump_audio(self, session: Any) -> None:
        mime = f"audio/pcm;rate={self._settings.input_sample_rate}"
        while True:
            chunk = await self._audio_in.get()
            await session.send_realtime_input(
                audio=types.Blob(data=chunk, mime_type=mime)
            )

    async def _pump_text(self, session: Any) -> None:
        while True:
            text = await self._text_in.get()
            await session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=text)])
            )

    async def _receive(self, session: Any) -> None:
        """Consumes the model stream until the connection ends."""
        while not self._closing.is_set():
            async for response in session.receive():
                await self._handle_response(session, response)
            # The iterator completes at the end of a turn; re-entering keeps
            # the session listening for the next one.

    async def _handle_response(self, session: Any, response: Any) -> None:
        server_content = getattr(response, "server_content", None)

        if server_content:
            if server_content.model_turn:
                for part in server_content.model_turn.parts or []:
                    if part.inline_data and part.inline_data.data:
                        await self._audio_sink(part.inline_data.data)

            transcription = getattr(server_content, "input_transcription", None)
            if transcription and transcription.text:
                await self._event_sink(
                    {"type": "transcript", "role": "user", "text": transcription.text}
                )

            output = getattr(server_content, "output_transcription", None)
            if output and output.text:
                await self._event_sink(
                    {"type": "transcript", "role": "agent", "text": output.text}
                )

            if server_content.interrupted:
                # Barge-in: the client started talking, drop queued audio.
                await self._event_sink({"type": "interrupted"})

            if server_content.turn_complete:
                await self._event_sink({"type": "turn_complete"})

        tool_call = getattr(response, "tool_call", None)
        if tool_call:
            await self._handle_tool_call(session, tool_call)

        go_away = getattr(response, "go_away", None)
        if go_away:
            logger.warning("Live API sent GoAway: %s", go_away)
            await self._event_sink(
                {"type": "status", "status": "verbindung_wird_beendet"}
            )

    async def _handle_tool_call(self, session: Any, tool_call: Any) -> None:
        """Executes the advisory tools and streams the resulting A2UI surfaces."""
        responses: list[types.FunctionResponse] = []

        for call in tool_call.function_calls or []:
            name = call.name
            args = dict(call.args or {})
            logger.info("Tool call: %s(%s)", name, sorted(args))

            try:
                result = await _maybe_await(
                    self._journey.handle(self._state, name, args)
                )
            except Exception as exc:
                logger.error(
                    "Tool %s failed: %s\n%s", name, exc, traceback.format_exc()
                )
                responses.append(
                    types.FunctionResponse(
                        name=name,
                        id=call.id,
                        response={
                            "fehler": (
                                "Die Ansicht konnte nicht erstellt werden. "
                                "Sprich normal weiter und versuche es später erneut."
                            )
                        },
                    )
                )
                continue

            for surface in result.surfaces:
                await self._emit_surface(surface)

            responses.append(
                types.FunctionResponse(name=name, id=call.id, response=result.result)
            )

            await self._event_sink(
                {
                    "type": "tool",
                    "name": name,
                    "surfaces": [s.surface_id for s in result.surfaces],
                }
            )

            if name == "naechsten_schritt_anbieten":
                await self._event_sink(
                    {"type": "handover", "summary": self._state.snapshot()}
                )

        if responses:
            await session.send_tool_response(function_responses=responses)

    async def _emit_surface(self, surface: Any) -> None:
        """Streams one surface, creating it only the first time it appears."""
        exists = surface.surface_id in self._live_surfaces
        try:
            messages: list[A2uiMessage] = surface.messages(exists=exists)
        except ValueError as exc:
            # A malformed tree would render as a permanent placeholder in the
            # browser, so drop it here and keep the conversation going.
            logger.error("Invalid surface %s: %s", surface.surface_id, exc)
            return

        self._live_surfaces.add(surface.surface_id)

        for message in messages:
            await self._event_sink({"type": "a2ui", "payload": message})

        await self._event_sink(
            {
                "type": "surface_meta",
                "surfaceId": surface.surface_id,
                "title": surface.title,
                "isNew": not exists,
            }
        )


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value
