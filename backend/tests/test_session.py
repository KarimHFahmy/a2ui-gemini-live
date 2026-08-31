"""Translating ADK events into what the browser needs.

ADK owns the Live connection and tool dispatch; this layer only decides what
reaches the WebSocket. These drive it with hand-built events, so the whole
translation is covered without a runner or credentials.
"""

from __future__ import annotations

from typing import Any

import pytest
from google.adk.events import Event, EventActions
from google.adk.events.ui_widget import UiWidget
from google.genai import types

from app.config import Settings
from app.journeys import get_journey
from app.session import AdvisorySession, build_run_config


@pytest.fixture
def session() -> tuple[AdvisorySession, list[bytes], list[dict[str, Any]]]:
    audio: list[bytes] = []
    events: list[dict[str, Any]] = []

    async def audio_sink(chunk: bytes) -> None:
        audio.append(chunk)

    async def event_sink(event: dict[str, Any]) -> None:
        events.append(event)

    advisory = AdvisorySession(
        settings=Settings(),
        journey=get_journey("energie"),
        audio_sink=audio_sink,
        event_sink=event_sink,
    )
    return advisory, audio, events


def a2ui_event(**payload: Any) -> Event:
    return Event(
        author="berater_energie",
        actions=EventActions(
            render_ui_widgets=[
                UiWidget(id=payload["surfaceId"], provider="a2ui", payload=payload)
            ]
        ),
    )


class TestToolAnnouncements:
    @pytest.mark.asyncio
    async def test_a_function_call_is_announced_by_name(self, session):
        """The client shows what is being worked on, so it needs the name.

        This used to send surface ids under a `surfaces` key while the client
        read `name`, so the busy indicator never appeared at all.
        """
        advisory, _, events = session

        await advisory._handle_event(
            Event(
                author="berater_energie",
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name="wirtschaftlichkeit_zeigen", args={}
                            )
                        )
                    ],
                ),
            )
        )

        assert events == [{"type": "tool", "name": "wirtschaftlichkeit_zeigen"}]


class TestSurfaceForwarding:
    @pytest.mark.asyncio
    async def test_a2ui_widgets_become_a2ui_frames(self, session):
        advisory, _, events = session

        await advisory._handle_event(
            a2ui_event(
                surfaceId="profil",
                title="Ihre Situation",
                isNew=True,
                messages=[{"version": "v0.9.1", "createSurface": {"surfaceId": "profil"}}],
            )
        )

        assert [e["type"] for e in events] == ["a2ui", "surface_meta"]
        assert events[0]["payload"]["createSurface"]["surfaceId"] == "profil"
        assert events[1] == {
            "type": "surface_meta",
            "surfaceId": "profil",
            "title": "Ihre Situation",
            "isNew": True,
        }

    @pytest.mark.asyncio
    async def test_widgets_from_other_providers_are_left_alone(self, session):
        """`provider` is ADK's dispatch field; another host owns those."""
        advisory, _, events = session

        await advisory._handle_event(
            Event(
                author="berater_energie",
                actions=EventActions(
                    render_ui_widgets=[
                        UiWidget(id="w", provider="mcp", payload={"resource_uri": "ui://x"})
                    ]
                ),
            )
        )

        assert not [e for e in events if e["type"] in {"a2ui", "surface_meta"}]

    @pytest.mark.asyncio
    async def test_an_event_without_widgets_is_quiet(self, session):
        advisory, _, events = session
        await advisory._handle_event(Event(author="berater_energie"))
        assert events == []


class TestStreamTranslation:
    @pytest.mark.asyncio
    async def test_audio_and_transcripts_reach_the_browser(self, session):
        advisory, audio, events = session

        await advisory._handle_event(
            Event(
                author="berater_energie",
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                data=b"\x01\x02", mime_type="audio/pcm"
                            )
                        )
                    ],
                ),
                input_transcription=types.Transcription(text="Unser Haus ist von 1985"),
                output_transcription=types.Transcription(text="Verstanden."),
                turn_complete=True,
            )
        )

        assert audio == [b"\x01\x02"]
        assert [(e["role"], e["text"]) for e in events if e["type"] == "transcript"] == [
            ("user", "Unser Haus ist von 1985"),
            ("agent", "Verstanden."),
        ]
        assert any(e["type"] == "turn_complete" for e in events)

    @pytest.mark.asyncio
    async def test_barge_in_is_forwarded(self, session):
        advisory, _, events = session
        await advisory._handle_event(Event(author="berater_energie", interrupted=True))
        assert any(e["type"] == "interrupted" for e in events)


class TestInbound:
    def test_a_ui_interaction_becomes_a_conversational_turn(self, session):
        advisory, _, _ = session

        advisory.push_renderer_action(
            {"name": "szenario_gewaehlt", "context": {"szenarioId": "waermepumpe"}}
        )

        request = advisory._queue._queue.get_nowait()
        text = request.content.parts[0].text
        assert "szenario_gewaehlt" in text
        assert "waermepumpe" in text

    def test_a_closed_session_stops_accepting_audio(self, session):
        advisory, _, _ = session
        advisory.close()
        advisory.push_audio(b"\x00\x01")

        # close() enqueues its own sentinel; nothing may follow it.
        queue = advisory._queue._queue
        queued = [queue.get_nowait() for _ in range(queue.qsize())]
        assert [request.close for request in queued] == [True]


class TestRunConfig:
    def test_the_config_speaks_the_session_language_and_is_audio_first(self):
        config = build_run_config(Settings(), "de")

        assert config.response_modalities == ["AUDIO"]
        assert config.speech_config.language_code == "de-DE"
        assert build_run_config(Settings(), "en").speech_config.language_code == "en-GB"
        assert config.input_audio_transcription is not None
        assert config.output_audio_transcription is not None

    def test_bidi_streaming_is_requested(self):
        from google.adk.agents.run_config import StreamingMode

        assert build_run_config(Settings(), "de").streaming_mode == StreamingMode.BIDI
