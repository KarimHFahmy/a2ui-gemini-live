"""The advisory session, running on ADK's bidi-streaming runner.

ADK owns the Live API connection, the session store, tool dispatch and event
plumbing. What is left here is the translation between ADK events and what the
browser needs: audio frames, transcripts, and the A2UI stream that tools attach
to their events as UI widgets.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from google.adk.agents import LiveRequestQueue, RunConfig
from google.adk.agents.run_config import StreamingMode
from google.adk.events import Event
from google.adk.runners import InMemoryRunner
from google.genai import types

from .config import Settings
from .journeys import A2UI_PROVIDER, Journey
from .journeys.base import LOCALE_KEY
from .texts import Texts

logger = logging.getLogger(__name__)

AudioSink = Callable[[bytes], Awaitable[None]]
EventSink = Callable[[dict[str, Any]], Awaitable[None]]

APP_NAME = "adaptive-advisory"


def build_run_config(settings: Settings, locale: str) -> RunConfig:
    """Audio in, audio out, in the session's language, with both sides transcribed.

    Optional native-audio features are attached defensively: model support for
    them moves during preview, and a rejected config would take the whole
    session down rather than degrading one feature.
    """
    config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            language_code=settings.language_code(locale),
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=settings.voice_name
                )
            ),
        ),
        # The briefing asks for a visible transcript; it also makes the demo
        # debuggable on stage.
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        # Lets a dropped connection resume instead of restarting the advice.
        session_resumption=types.SessionResumptionConfig(),
    )

    if settings.affective_dialog:
        _try_set(config, "enable_affective_dialog", True)
    if settings.proactive_audio:
        _try_set(config, "proactivity", types.ProactivityConfig(proactive_audio=True))

    return config


def _try_set(config: RunConfig, field: str, value: Any) -> None:
    try:
        setattr(config, field, value)
    except Exception as exc:  # pragma: no cover - depends on SDK version
        logger.warning("RunConfig field %r not applied: %s", field, exc)


class AdvisorySession:
    """Drives one advisory conversation."""

    def __init__(
        self,
        *,
        settings: Settings,
        journey: Journey,
        audio_sink: AudioSink,
        event_sink: EventSink,
    ) -> None:
        self._settings = settings
        self._journey = journey
        self._audio_sink = audio_sink
        self._event_sink = event_sink

        self._t = Texts(journey.locale)
        self._runner = InMemoryRunner(agent=journey.agent, app_name=APP_NAME)
        self._queue = LiveRequestQueue()
        self._mime = f"audio/pcm;rate={settings.input_sample_rate}"
        self._closing = False

    # -- inbound from the browser -----------------------------------------

    def push_audio(self, chunk: bytes) -> None:
        if not self._closing:
            self._queue.send_realtime(types.Blob(data=chunk, mime_type=self._mime))

    def push_text(self, text: str) -> None:
        if text and not self._closing:
            self._queue.send_content(
                types.Content(role="user", parts=[types.Part(text=text)])
            )

    def push_renderer_action(self, action: dict[str, Any]) -> None:
        """Feeds a UI interaction back into the conversation.

        A tap on a card is a turn in the dialogue, not a side channel: the
        agent reacts to it in speech the same way it reacts to a spoken
        sentence. The values a control carries are spelled out rather than
        dumped as a dict, because they are usually exactly the arguments the
        matching tool needs — a slider the person has just dragged into place.
        """
        context = action.get("context") or {}
        werte = ", ".join(f"{key} = {value}" for key, value in context.items())
        self.push_text(
            self._t(
                "prompt.interaction",
                name=action.get("name", ""),
                werte=self._t("prompt.interaction.values", werte=werte) if werte else ".",
            )
        )

    def close(self) -> None:
        self._closing = True
        self._queue.close()

    # -- the session loop --------------------------------------------------

    async def run(self) -> None:
        """Opens the live connection and streams until the browser disconnects."""
        try:
            session = await self._runner.session_service.create_session(
                app_name=APP_NAME,
                user_id="demo",
                # The tools are module-level functions shared by every session
                # of a journey, so the language has to reach them through the
                # session rather than through a closure. See `base.texts_for`.
                state={LOCALE_KEY: self._journey.locale},
            )
            await self._event_sink({"type": "status", "status": self._t("status.connected")})

            # Kick off the greeting so the client hears a voice immediately.
            self.push_text(self._journey.opener)

            async for event in self._runner.run_live(
                user_id="demo",
                session_id=session.id,
                live_request_queue=self._queue,
                run_config=build_run_config(self._settings, self._journey.locale),
            ):
                await self._handle_event(event)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Live session failed")
            await self._event_sink(
                {
                    "type": "error",
                    "message": self._t("error.connection"),
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
        finally:
            await self._event_sink({"type": "status", "status": self._t("status.ended")})

    async def _handle_event(self, event: Event) -> None:
        """Translates one ADK event into what the browser needs."""
        await self._announce_tools(event)
        await self._forward_surfaces(event)

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.inline_data and part.inline_data.data:
                    await self._audio_sink(part.inline_data.data)

        if event.input_transcription and event.input_transcription.text:
            await self._event_sink(
                {
                    "type": "transcript",
                    "role": "user",
                    "text": event.input_transcription.text,
                }
            )

        if event.output_transcription and event.output_transcription.text:
            await self._event_sink(
                {
                    "type": "transcript",
                    "role": "agent",
                    "text": event.output_transcription.text,
                }
            )

        if event.interrupted:
            # Barge-in: the client started talking, so drop queued speech.
            await self._event_sink({"type": "interrupted"})

        if event.turn_complete:
            await self._event_sink({"type": "turn_complete"})

        if event.error_message:
            logger.error("ADK event error: %s", event.error_message)

    async def _announce_tools(self, event: Event) -> None:
        """Tells the browser which tool is running, by name.

        A tool call is the one moment where the person waits without hearing
        anything — the model has stopped speaking and the surface has not
        arrived yet. The name lets the client say what is being worked on
        instead of showing a bare spinner.
        """
        for call in event.get_function_calls() or []:
            await self._event_sink({"type": "tool", "name": call.name})

    async def _forward_surfaces(self, event: Event) -> None:
        """Forwards the A2UI widgets a tool attached to this event.

        `provider` is ADK's dispatch field for rendering strategies, so
        anything that is not ours is left for another host to deal with.
        """
        widgets = (event.actions.render_ui_widgets or []) if event.actions else []

        for widget in widgets:
            if widget.provider != A2UI_PROVIDER:
                continue

            payload = widget.payload or {}
            for message in payload.get("messages", []):
                await self._event_sink({"type": "a2ui", "payload": message})

            await self._event_sink(
                {
                    "type": "surface_meta",
                    "surfaceId": payload.get("surfaceId", widget.id),
                    "title": payload.get("title", ""),
                    "isNew": bool(payload.get("isNew")),
                }
            )
