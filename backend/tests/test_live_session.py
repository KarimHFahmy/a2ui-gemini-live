"""The bridge between a model tool call and the A2UI stream.

Driven with a stub in place of the Live API session, so the whole path —
function call in, surfaces composed, envelopes emitted, function response
returned — is exercised without a network connection or credentials.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.config import Settings
from app.journeys import get_journey
from app.live_session import AdvisorySession, build_config


class StubSession:
    """Stands in for `client.aio.live.connect(...)`'s session object."""

    def __init__(self) -> None:
        self.tool_responses: list[Any] = []

    async def send_tool_response(self, function_responses: list[Any]) -> None:
        self.tool_responses.extend(function_responses)


def make_session(journey_id: str = "energie") -> tuple[AdvisorySession, list, list]:
    audio: list[bytes] = []
    events: list[dict[str, Any]] = []

    async def audio_sink(chunk: bytes) -> None:
        audio.append(chunk)

    async def event_sink(event: dict[str, Any]) -> None:
        events.append(event)

    session = AdvisorySession(
        settings=Settings(),
        journey=get_journey(journey_id),
        client=SimpleNamespace(),  # never touched on this path
        audio_sink=audio_sink,
        event_sink=event_sink,
    )
    return session, audio, events


def tool_call(name: str, args: dict[str, Any], call_id: str = "call-1"):
    return SimpleNamespace(
        function_calls=[SimpleNamespace(name=name, args=args, id=call_id)]
    )


@pytest.mark.asyncio
async def test_a_tool_call_streams_a2ui_and_answers_the_model():
    session, _, events = make_session()
    stub = StubSession()

    await session._handle_tool_call(
        stub, tool_call("profil_aktualisieren", {"baujahr": 1985, "wohnflaeche_qm": 150})
    )

    a2ui = [e for e in events if e["type"] == "a2ui"]
    kinds = [next(k for k in e["payload"] if k != "version") for e in a2ui]
    assert kinds == ["createSurface", "updateDataModel", "updateComponents"]

    meta = next(e for e in events if e["type"] == "surface_meta")
    assert meta["surfaceId"] == "profil"
    assert meta["isNew"] is True

    # The model gets a result it can talk about without re-deriving numbers.
    assert len(stub.tool_responses) == 1
    assert stub.tool_responses[0].name == "profil_aktualisieren"
    assert "waermebedarf_kwh_a" in stub.tool_responses[0].response


@pytest.mark.asyncio
async def test_calling_the_same_tool_twice_updates_in_place():
    session, _, events = make_session()
    stub = StubSession()

    call = tool_call("profil_aktualisieren", {"baujahr": 1985})
    await session._handle_tool_call(stub, call)
    events.clear()
    await session._handle_tool_call(stub, call)

    kinds = [
        next(k for k in e["payload"] if k != "version")
        for e in events
        if e["type"] == "a2ui"
    ]
    assert "createSurface" not in kinds
    assert kinds == ["updateDataModel", "updateComponents"]


@pytest.mark.asyncio
async def test_the_closing_tool_emits_a_handover_summary():
    session, _, events = make_session()
    stub = StubSession()

    await session._handle_tool_call(
        stub,
        tool_call(
            "naechsten_schritt_anbieten",
            {
                "empfehlung": "Wärmepumpe passt.",
                "begruendung": ["Gute Eignung"],
                "schritt": "beratungstermin",
            },
        ),
    )

    handover = next(e for e in events if e["type"] == "handover")
    assert handover["summary"]["journey"] == "energie"
    assert handover["summary"]["empfehlung"]["szenario"]


@pytest.mark.asyncio
async def test_a_failing_tool_keeps_the_conversation_alive():
    """A broken view must not end the call — the agent should talk on."""
    session, _, events = make_session()
    stub = StubSession()

    journey = session._journey
    original = journey.handlers["waermepumpen_eignung_zeigen"]

    def explode(state, args):
        raise RuntimeError("composer broke")

    journey.handlers["waermepumpen_eignung_zeigen"] = explode
    try:
        await session._handle_tool_call(stub, tool_call("waermepumpen_eignung_zeigen", {}))
    finally:
        journey.handlers["waermepumpen_eignung_zeigen"] = original

    assert not [e for e in events if e["type"] == "a2ui"]
    assert "fehler" in stub.tool_responses[0].response


@pytest.mark.asyncio
async def test_audio_and_transcripts_reach_the_browser():
    session, audio, events = make_session()

    response = SimpleNamespace(
        server_content=SimpleNamespace(
            model_turn=SimpleNamespace(
                parts=[SimpleNamespace(inline_data=SimpleNamespace(data=b"\x01\x02"))]
            ),
            input_transcription=SimpleNamespace(text="Unser Haus ist von 1985"),
            output_transcription=SimpleNamespace(text="Verstanden."),
            interrupted=False,
            turn_complete=True,
        ),
        tool_call=None,
        go_away=None,
    )

    await session._handle_response(StubSession(), response)

    assert audio == [b"\x01\x02"]
    roles = [(e["role"], e["text"]) for e in events if e["type"] == "transcript"]
    assert roles == [("user", "Unser Haus ist von 1985"), ("agent", "Verstanden.")]
    assert any(e["type"] == "turn_complete" for e in events)


@pytest.mark.asyncio
async def test_barge_in_is_forwarded():
    session, _, events = make_session()

    response = SimpleNamespace(
        server_content=SimpleNamespace(
            model_turn=None,
            input_transcription=None,
            output_transcription=None,
            interrupted=True,
            turn_complete=False,
        ),
        tool_call=None,
        go_away=None,
    )
    await session._handle_response(StubSession(), response)

    assert any(e["type"] == "interrupted" for e in events)


def test_a_ui_interaction_becomes_a_conversational_turn():
    session, _, _ = make_session()

    session.push_renderer_action(
        {"name": "szenario_gewaehlt", "context": {"szenarioId": "waermepumpe"}}
    )

    text = session._text_in.get_nowait()
    assert "szenario_gewaehlt" in text
    assert "waermepumpe" in text


class TestLiveConfig:
    def test_the_config_is_german_and_audio_first(self):
        config = build_config(Settings(), get_journey("energie"))

        assert config.speech_config.language_code == "de-DE"
        assert config.input_audio_transcription is not None
        assert config.output_audio_transcription is not None

    def test_every_journey_tool_reaches_the_model(self):
        journey = get_journey("mobilitaet")
        config = build_config(Settings(), journey)

        names = {fn.name for fn in config.tools[0].function_declarations}
        assert names == {decl["name"] for decl in journey.function_declarations}
