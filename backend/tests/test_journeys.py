"""The agent-facing contract of each journey.

The model can only reach the UI through these tools, so their shape *is* the
guardrail. If a tool declaration drifts from its handler, the model calls
something that silently does nothing.
"""

from __future__ import annotations

import pytest

from app.a2ui import protocol
from app.journeys import JOURNEYS, get_journey

ALL_JOURNEYS = list(JOURNEYS.values())
JOURNEY_IDS = [j.id for j in ALL_JOURNEYS]


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_every_declared_tool_has_a_handler(journey):
    declared = {decl["name"] for decl in journey.function_declarations}
    assert declared == set(journey.handlers)


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_tool_declarations_are_well_formed(journey):
    for decl in journey.function_declarations:
        assert decl["name"] and decl["description"]
        params = decl["parameters"]
        assert params["type"] == "OBJECT"

        for prop_name, prop in params.get("properties", {}).items():
            assert prop["type"] in {
                "STRING",
                "NUMBER",
                "INTEGER",
                "BOOLEAN",
                "ARRAY",
                "OBJECT",
            }, f"{decl['name']}.{prop_name}"
            if prop["type"] == "ARRAY":
                assert "items" in prop, f"{decl['name']}.{prop_name} has no items"

        for required in params.get("required", []):
            assert required in params["properties"], f"{decl['name']}: {required}"


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_system_instruction_is_german_and_substantial(journey):
    instruction = journey.system_instruction
    assert len(instruction) > 1500
    # A prompt that drifted to English would take the whole demo with it.
    assert "Du bist" in instruction
    assert "Nie Zahlen erfinden" in instruction


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_an_unknown_tool_is_reported_not_raised(journey):
    result = journey.handle(journey.state_factory(), "gibt_es_nicht", {})
    assert "fehler" in result.result
    assert result.surfaces == []


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_every_tool_produces_a_renderable_surface_from_bare_arguments(journey):
    """Called with nothing but their required arguments, tools must still work.

    A live model routinely calls a tool before it has gathered everything, so
    every handler has to cope with a half-filled profile.
    """
    state = journey.state_factory()

    for decl in journey.function_declarations:
        args = _minimal_args(decl)
        result = journey.handle(state, decl["name"], args)

        assert result.surfaces, f"{decl['name']} produced no surface"
        for surface in result.surfaces:
            # Raises if the tree is malformed or references a missing child.
            messages = surface.messages(exists=False)
            assert messages[0]["createSurface"]["surfaceId"] == surface.surface_id
            assert "updateDataModel" in messages[1]
            assert "updateComponents" in messages[2]


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_repeating_a_tool_updates_the_surface_in_place(journey):
    """A refined answer replaces the card the client is looking at."""
    state = journey.state_factory()
    decl = journey.function_declarations[0]

    first = journey.handle(state, decl["name"], _minimal_args(decl)).surfaces[0]
    second = journey.handle(state, decl["name"], _minimal_args(decl)).surfaces[0]

    assert first.surface_id == second.surface_id
    updates = second.messages(exists=True)
    assert all("createSurface" not in message for message in updates)


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_surfaces_declare_the_advisory_catalog(journey):
    state = journey.state_factory()
    decl = journey.function_declarations[0]
    surface = journey.handle(state, decl["name"], _minimal_args(decl)).surfaces[0]

    created = surface.messages(exists=False)[0]["createSurface"]
    assert created["catalogId"] == protocol.ADVISORY_CATALOG_ID


@pytest.mark.parametrize("journey", ALL_JOURNEYS, ids=JOURNEY_IDS)
def test_every_data_binding_resolves_against_the_data_model(journey):
    """A binding to a path the data model lacks renders as an empty block."""
    state = journey.state_factory()

    for decl in journey.function_declarations:
        result = journey.handle(state, decl["name"], _minimal_args(decl))
        for surface in result.surfaces:
            for component in surface.components:
                for prop, value in component.items():
                    if not (isinstance(value, dict) and set(value) == {"path"}):
                        continue
                    key = value["path"].lstrip("/")
                    assert key in surface.data, (
                        f"{journey.id}/{decl['name']}: {component['id']}.{prop} "
                        f"binds to /{key}, which the data model does not define"
                    )


def test_get_journey_falls_back_to_the_default():
    assert get_journey(None).id == "energie"
    assert get_journey("nonexistent").id == "energie"
    assert get_journey("mobilitaet").id == "mobilitaet"


def _minimal_args(decl: dict) -> dict:
    """Builds the smallest argument set a declaration accepts."""
    params = decl["parameters"]
    properties = params.get("properties", {})
    args: dict = {}

    for name in params.get("required", []):
        args[name] = _sample_value(properties[name])

    return args


def _sample_value(prop: dict):
    kind = prop["type"]
    if kind == "STRING":
        return prop.get("enum", ["Beispieltext"])[0]
    if kind in {"NUMBER", "INTEGER"}:
        return 1
    if kind == "BOOLEAN":
        return True
    if kind == "ARRAY":
        return [_sample_value(prop["items"])]
    return {
        name: _sample_value(sub)
        for name, sub in prop.get("properties", {}).items()
        if name in prop.get("required", [])
    }
