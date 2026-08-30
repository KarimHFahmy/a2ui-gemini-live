"""The experiment: what happens when the model writes the A2UI itself.

`app.journeys.generative` removes the composers. These do not test taste — no
test can tell you whether a model-authored layout is any good — they test the
mechanism the experiment stands on: the model's JSON reaches the renderer when
it is right, and comes back as a correction it can act on when it is wrong.

The wrong cases matter more than the right one. A tree with a dangling child id
renders as a permanent "[Loading ...]" in the browser, which during a live demo
looks like a hang, so the pipeline has to catch it server-side and tell the
model what to fix.
"""

from __future__ import annotations

import json
import re

import pytest

from app.journeys import generative


@pytest.fixture(params=["energie", "mobilitaet"])
def tools(request):
    profil_merken, daten_abrufen, oberflaeche_zeigen = generative.make_tools(request.param)
    return {
        "journey": request.param,
        "merken": profil_merken,
        "daten": daten_abrufen,
        "zeigen": oberflaeche_zeigen,
    }


def tree(*components) -> str:
    return json.dumps(list(components))


VALID = [
    {"id": "t", "component": "Text", "text": "Ihr Haus ist gut geeignet", "variant": "h2"},
    {"id": "root", "component": "Column", "children": ["t"]},
]


class TestTheModelDrawsSomething:
    def test_a_valid_tree_reaches_the_browser(self, tools, ctx):
        result = tools["zeigen"](
            tool_context=ctx, surface_id="eignung", titel="Eignung", components_json=tree(*VALID)
        )

        assert result["status"] == "angezeigt"
        assert result["komponenten"] == 2

        [widget] = ctx.widgets
        assert widget.payload["surfaceId"] == "eignung"
        components = next(
            m for m in widget.payload["messages"] if "updateComponents" in m
        )["updateComponents"]["components"]
        assert components == VALID

    def test_a_data_model_travels_with_it(self, tools, ctx):
        tools["zeigen"](
            tool_context=ctx,
            surface_id="x",
            titel="X",
            components_json=tree(
                {"id": "root", "component": "Text", "text": {"path": "/titel"}}
            ),
            data_json=json.dumps({"titel": "Aus dem Datenmodell"}),
        )

        data = next(
            m for m in ctx.widgets[0].payload["messages"] if "updateDataModel" in m
        )["updateDataModel"]["value"]
        assert data == {"titel": "Aus dem Datenmodell"}


class TestTheModelGetsItWrong:
    """Each of these would be a broken screen. None of them reaches the browser."""

    def test_malformed_json_comes_back_as_a_correction(self, tools, ctx):
        result = tools["zeigen"](
            tool_context=ctx, surface_id="x", titel="X", components_json="[{'id': broken"
        )

        assert "fehler" in result
        assert "hinweis" in result, "the model needs to know what to do next"
        assert not ctx.widgets

    def test_a_tree_with_no_root_is_refused(self, tools, ctx):
        result = tools["zeigen"](
            tool_context=ctx,
            surface_id="x",
            titel="X",
            components_json=tree({"id": "t", "component": "Text", "text": "kein root"}),
        )

        assert "root" in result["fehler"]
        assert not ctx.widgets

    def test_a_dangling_child_is_refused(self, tools, ctx):
        """The failure mode that renders as a permanent "[Loading ...]"."""
        result = tools["zeigen"](
            tool_context=ctx,
            surface_id="x",
            titel="X",
            components_json=tree(
                {"id": "root", "component": "Column", "children": ["gibtsnicht"]}
            ),
        )

        assert "gibtsnicht" in result["fehler"]
        assert not ctx.widgets

    def test_duplicate_ids_are_refused(self, tools, ctx):
        result = tools["zeigen"](
            tool_context=ctx,
            surface_id="x",
            titel="X",
            components_json=tree(
                {"id": "root", "component": "Column", "children": ["a"]},
                {"id": "a", "component": "Text", "text": "eins"},
                {"id": "a", "component": "Text", "text": "zwei"},
            ),
        )

        assert "a" in result["fehler"]
        assert not ctx.widgets


class TestTheFiguresAreStillOurs:
    """The model lays out the numbers. It does not get to make them up."""

    def test_every_area_returns_real_domain_data(self, tools, ctx):
        areas = generative._AREAS[tools["journey"]]
        for area in sorted(areas):
            data = tools["daten"](tool_context=ctx, bereich=area)
            assert "fehler" not in data, area
            assert data, area

    def test_an_unknown_area_lists_the_real_ones(self, tools, ctx):
        result = tools["daten"](tool_context=ctx, bereich="erfunden")

        assert "fehler" in result
        assert set(result["verfuegbar"]) == generative._AREAS[tools["journey"]]


class TestTheProfileStaysTyped:
    def test_known_fields_are_applied(self, tools, ctx):
        field = "baujahr" if tools["journey"] == "energie" else "taeglich_km"
        result = tools["merken"](tool_context=ctx, aenderungen_json=json.dumps({field: 1975}))

        assert result["uebernommen"] == {field: 1975}

    def test_invented_fields_are_rejected_with_the_real_list(self, tools, ctx):
        result = tools["merken"](
            tool_context=ctx, aenderungen_json=json.dumps({"lieblingsfarbe": "blau"})
        )

        assert result["unbekannt"] == ["lieblingsfarbe"]
        assert "erlaubte_felder" in result

    def test_malformed_json_does_not_crash_the_turn(self, tools, ctx):
        assert "fehler" in tools["merken"](tool_context=ctx, aenderungen_json="{nope")


class TestTheRunIsMeasured:
    def test_the_tally_separates_shown_from_refused(self, tools, ctx):
        tools["zeigen"](
            tool_context=ctx, surface_id="a", titel="A", components_json=tree(*VALID)
        )
        tools["zeigen"](
            tool_context=ctx, surface_id="b", titel="B", components_json="nonsense"
        )

        tally = generative.metrics(ctx.state)
        assert tally["versuche"] == 2
        assert tally["angezeigt"] == 1
        assert tally["abgelehnt"] == 1
        assert tally["zeichen_gesamt"] > 0


class TestTheShellStillHasSomethingToTrack:
    """The shell keys off surface ids, and here the model chooses them.

    With composers, `profil` and the arc's ids are guaranteed by construction.
    Here the only thing that produces them is the instruction saying so — and
    if it stops saying so, the context column stays empty and the progress
    rail never advances, in a run that otherwise looks fine. That would read
    as a verdict on generative UI when it is really a broken prompt.
    """

    @pytest.mark.parametrize("journey_id", ["energie", "mobilitaet"])
    def test_the_model_is_told_every_id_the_shell_watches(self, journey_id):
        instruction = generative._instruction(journey_id)

        for surface_id, _label in generative._STEPS[journey_id]:
            assert f"`{surface_id}`" in instruction, (
                f"{surface_id} drives the progress rail but the prompt never names it"
            )

    @pytest.mark.parametrize("journey_id", ["energie", "mobilitaet"])
    def test_the_context_column_is_asked_for_by_name(self, journey_id):
        # 'profil' is what the client routes into the aside (see
        # frontend/src/ui/surfaces.ts). Naming the id is not enough — the
        # composed journeys push that surface on every profile change, and
        # here nothing does unless the prompt explains what the id is for.
        instruction = generative._instruction(journey_id)

        assert "`profil`" in instruction
        assert "Seitenspalte" in instruction

    @pytest.mark.parametrize("journey_id", ["energie", "mobilitaet"])
    def test_every_area_the_arc_asks_for_actually_exists(self, journey_id):
        # The arc names areas by hand; a typo there sends the model looking for
        # figures that are not there, and it has to recover mid-conversation.
        arc = generative._BOGEN[journey_id]
        named = {a or b for a, b in re.findall(r'daten_abrufen\("(\w+)"\)|\("(\w+)"\)', arc)}
        unknown = named - generative._AREAS[journey_id]
        assert not unknown, f"the arc asks for areas that do not exist: {sorted(unknown)}"
