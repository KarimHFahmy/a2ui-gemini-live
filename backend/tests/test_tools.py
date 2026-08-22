"""The agent-facing contract of each journey's tools.

The model can only reach the UI through these functions, so their shape *is*
the guardrail. ADK derives each declaration from the signature and docstring,
which is what these assert against.
"""

from __future__ import annotations

import inspect

import pytest
from google.adk.tools import FunctionTool

from app.a2ui import protocol
from app.journeys import all_journeys, energie, get_journey, mobilitaet

JOURNEY_TOOLS = [("energie", energie), ("mobilitaet", mobilitaet)]
ALL_TOOLS = [
    pytest.param(module, tool, id=f"{name}.{tool.__name__}")
    for name, module in JOURNEY_TOOLS
    for tool in module.TOOLS
]


@pytest.mark.parametrize("module,tool", ALL_TOOLS)
class TestToolContract:
    def test_adk_can_build_a_declaration(self, module, tool):
        """A tool ADK cannot describe is a tool the model never sees."""
        declaration = FunctionTool(func=tool)._get_declaration()

        assert declaration.name == tool.__name__
        assert declaration.description, f"{tool.__name__} has no docstring"
        # `tool_context` is injected by ADK and must not reach the model.
        schema = declaration.parameters_json_schema or {}
        assert "tool_context" not in schema.get("properties", {})

    def test_documents_every_parameter(self, module, tool):
        """An undocumented parameter is one the model will guess at."""
        doc = inspect.getdoc(tool) or ""
        parameters = [
            name
            for name in inspect.signature(tool).parameters
            if name != "tool_context"
        ]
        if not parameters:
            return

        assert "Args:" in doc, f"{tool.__name__} takes arguments but documents none"
        for name in parameters:
            assert f"{name}:" in doc, f"{tool.__name__} does not document {name!r}"

    def test_produces_a_renderable_surface(self, module, tool, ctx):
        """Called with only its required arguments, a tool must still work.

        A live model routinely calls a tool before it has gathered everything,
        so every one has to cope with a half-filled profile.
        """
        tool(tool_context=ctx, **_minimal_args(tool))

        assert ctx.widgets, f"{tool.__name__} pushed no surface"
        for widget in ctx.widgets:
            assert widget.provider == "a2ui"
            kinds = [
                next(k for k in message if k != "version")
                for message in widget.payload["messages"]
            ]
            assert kinds == ["createSurface", "updateDataModel", "updateComponents"]


@pytest.mark.parametrize("name,module", JOURNEY_TOOLS)
class TestJourney:
    def test_repeating_a_tool_updates_the_surface_in_place(self, name, module, ctx):
        """A refined answer replaces the card the client is looking at."""
        tool = module.TOOLS[0]

        tool(tool_context=ctx, **_minimal_args(tool))
        first = ctx.widgets[0].payload
        ctx.reset_event()
        tool(tool_context=ctx, **_minimal_args(tool))
        second = ctx.widgets[0].payload

        assert first["isNew"] is True
        assert second["isNew"] is False
        assert first["surfaceId"] == second["surfaceId"]
        assert all("createSurface" not in m for m in second["messages"])

    def test_surfaces_declare_the_advisory_catalog(self, name, module, ctx):
        tool = module.TOOLS[0]
        tool(tool_context=ctx, **_minimal_args(tool))

        created = ctx.widgets[0].payload["messages"][0]["createSurface"]
        assert created["catalogId"] == protocol.ADVISORY_CATALOG_ID

    def test_the_profile_survives_across_tool_calls(self, name, module, ctx):
        """State is what makes the conversation cumulative."""
        first, second = module.TOOLS[0], module.TOOLS[1]

        first(tool_context=ctx, **_minimal_args(first))
        before = dict(ctx.state)
        ctx.reset_event()
        second(tool_context=ctx, **_minimal_args(second))

        assert before, "the first tool stored nothing"
        assert ctx.state["_advisory_profile"] == before["_advisory_profile"]

    def test_every_data_binding_resolves_against_the_data_model(
        self, name, module, ctx
    ):
        """A binding to a missing path renders as a blank block."""
        for tool in module.TOOLS:
            ctx.reset_event()
            tool(tool_context=ctx, **_minimal_args(tool))

            for widget in ctx.widgets:
                messages = widget.payload["messages"]
                data = next(m for m in messages if "updateDataModel" in m)[
                    "updateDataModel"
                ]["value"]
                components = next(m for m in messages if "updateComponents" in m)[
                    "updateComponents"
                ]["components"]

                for component in components:
                    for prop, value in component.items():
                        for path in _absolute_paths(value):
                            assert path.lstrip("/") in data, (
                                f"{name}/{tool.__name__}: {component['id']}.{prop} "
                                f"binds to {path}, which the data model lacks"
                            )

    def test_the_closing_tool_produces_a_handover_summary(self, name, module, ctx):
        tool = module.naechsten_schritt_anbieten
        result = tool(tool_context=ctx, **_minimal_args(tool))

        summary = result["zusammenfassung"]
        assert summary["journey"] == name
        assert summary["empfehlung"]


class TestJourneyRegistry:
    def test_every_journey_builds_an_agent_with_its_tools(self):
        for journey in all_journeys():
            names = {t.__name__ for t in journey.agent.tools}
            assert names, f"{journey.id} has no tools"
            assert journey.agent.instruction
            assert journey.opener

    def test_instructions_are_german_and_carry_the_guardrail(self):
        for journey in all_journeys():
            instruction = journey.agent.instruction
            assert len(instruction) > 1500
            assert "Du bist" in instruction
            assert "Nie Zahlen erfinden" in instruction

    def test_get_journey_falls_back_to_the_default(self):
        assert get_journey(None).id == "energie"
        assert get_journey("nonexistent").id == "energie"
        assert get_journey("mobilitaet").id == "mobilitaet"

    def test_journeys_are_cached(self):
        """Building an Agent is not free, and every connection asks for one."""
        assert get_journey("energie") is get_journey("energie")


def _absolute_paths(value: object) -> list[str]:
    """Collects `{"path": "/…"}` bindings.

    Relative paths inside a `List` template resolve against the item, not the
    root, so only absolute ones can be checked here.
    """
    if isinstance(value, dict):
        if set(value) == {"path"} and str(value["path"]).startswith("/"):
            return [value["path"]]
        return [p for v in value.values() for p in _absolute_paths(v)]
    if isinstance(value, list):
        return [p for v in value for p in _absolute_paths(v)]
    return []


def _minimal_args(tool) -> dict:
    """Builds the smallest argument set a tool accepts."""
    args: dict = {}
    for name, parameter in inspect.signature(tool).parameters.items():
        if name == "tool_context" or parameter.default is not inspect.Parameter.empty:
            continue
        args[name] = _sample_value(parameter.annotation, name)
    return args


def _sample_value(annotation, name: str):
    text = str(annotation)
    if "Literal" in text:
        # Use the first permitted value.
        return text.split("'")[1]
    if "list[dict" in text:
        return [{"titel": "Punkt", "text": "Erklärung", "tone": "neutral"}]
    if "list[str" in text:
        return ["Beispiel"]
    if "int" in text:
        return 1
    if "float" in text:
        return 1.0
    if "bool" in text:
        return True
    return f"Beispiel {name}"
