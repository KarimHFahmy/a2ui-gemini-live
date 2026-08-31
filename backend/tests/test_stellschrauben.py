"""The what-if surfaces: does the browser compute what the backend would?

These surfaces are the one place where a number reaches the client as an
*expression* rather than as a finished string — a slider writes into the data
model and the renderer re-evaluates every figure built from it, in the browser,
with no round trip.

That is a real risk: the arithmetic now lives in two places. So these tests
evaluate the emitted expression trees the same way `@a2ui/web_core`'s basic
functions do, and hold the result against the domain module. If a coefficient
ever stops meaning what the formula assumes, this fails here rather than on
stage.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.a2ui import composer_energie, composer_mobilitaet
from app.texts import Texts
from app.domain import energie, mobilitaet


#: These tests are about tone, bindings and arithmetic, none of which is
#: language-specific; the bilingual coverage is in test_readback and test_texts.
TEXTS = Texts("de")


# ---------------------------------------------------------------------------
# A stand-in for the renderer's expression evaluation
# ---------------------------------------------------------------------------

#: The subset of `BASIC_FUNCTIONS` the composers use. Same names, same argument
#: names, same semantics as `@a2ui/web_core/v0_9/basic_catalog`.
_FUNCTIONS = {
    "add": lambda a, b, **_: a + b,
    "subtract": lambda a, b, **_: a - b,
    "multiply": lambda a, b, **_: a * b,
    "divide": lambda a, b, **_: a / b if b else float("inf"),
    "formatCurrency": lambda value, **_: value,
    "formatNumber": lambda value, **_: value,
}


def evaluate(value: Any, data: dict[str, Any]) -> Any:
    """Resolves a DynamicValue against a data model, as the renderer does."""
    if isinstance(value, dict) and set(value) == {"path"}:
        current: Any = data
        for segment in value["path"].strip("/").split("/"):
            current = current[segment]
        return current
    if isinstance(value, dict) and "call" in value:
        args = {k: evaluate(v, data) for k, v in value["args"].items()}
        return _FUNCTIONS[value["call"]](**args)
    return value


def find(surface, component_id_prefix: str) -> list[dict[str, Any]]:
    return [c for c in surface.components if c.get("component") == component_id_prefix]


def live_values(surface) -> list[Any]:
    """Every figure on the surface that is computed in the browser.

    The what-if figures are `StatCard` metrics whose value is a function-call
    expression rather than a string the backend already rendered.
    """
    return [
        c["metric"]
        for c in surface.components
        if c.get("component") == "StatCard"
        and isinstance(c.get("metric"), dict)
        and "call" in c["metric"]
    ]


# ---------------------------------------------------------------------------
# Energie
# ---------------------------------------------------------------------------


@pytest.fixture
def energie_surface():
    profil = energie.Gebaeudeprofil()
    szenarien = energie.szenarien(profil)
    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next(s for s in szenarien if s.id == "waermepumpe")
    surface = composer_energie.stellschrauben_surface(TEXTS, profil, bestand, fokus)
    return surface, bestand, fokus


class TestEnergieStellschrauben:
    def test_the_sliders_start_where_the_calculation_stands(self, energie_surface):
        surface, _, _ = energie_surface
        sliders = find(surface, "Slider")

        assert len(sliders) == 2
        for slider in sliders:
            start = evaluate(slider["value"], surface.data)
            assert slider["min"] <= start <= slider["max"], (
                f"{slider['label']} opens outside its own range"
            )
            # A range input steps in ones, so a fractional start would put the
            # thumb half a step away from the figures below it.
            assert start == int(start), f"{slider['label']} opens off the step grid"

    def test_the_untouched_sliders_reproduce_the_domain_figures(self, energie_surface):
        """At the starting position the browser must agree with the backend."""
        surface, bestand, fokus = energie_surface
        heute, danach, monat, zwanzig = [
            evaluate(value, surface.data) for value in live_values(surface)
        ]

        assert heute == pytest.approx(bestand.betriebskosten_eur_a, abs=1)
        assert danach == pytest.approx(fokus.betriebskosten_eur_a, abs=1)

        ersparnis = bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a
        assert monat == pytest.approx(ersparnis / 12, abs=1)
        assert zwanzig == pytest.approx(ersparnis * 20 - fokus.eigenanteil_eur, abs=20)

    def test_a_dragged_slider_lands_where_the_backend_would(self, energie_surface):
        """Drag both sliders, then let the backend recompute from the same values."""
        surface, _, _ = energie_surface
        data = {**surface.data, "wenn": {"preis_alt_ct": 20.0, "preis_strom_ct": 38.0}}

        heute, danach, _, _ = [evaluate(value, data) for value in live_values(surface)]

        profil = energie.Gebaeudeprofil(preis_alt_ct=20.0, preis_strom_ct=38.0)
        szenarien = energie.szenarien(profil)
        assert heute == pytest.approx(
            next(s for s in szenarien if s.id == "bestand").betriebskosten_eur_a, abs=2
        )
        assert danach == pytest.approx(
            next(s for s in szenarien if s.id == "waermepumpe").betriebskosten_eur_a,
            abs=2,
        )

    def test_the_button_hands_the_slider_values_back(self, energie_surface):
        surface, _, _ = energie_surface
        button = find(surface, "Button")[0]
        context = button["action"]["event"]["context"]

        assert button["action"]["event"]["name"] == "annahmen_uebernehmen"
        assert context == {
            "preis_alt_ct": {"path": "/wenn/preis_alt_ct"},
            "preis_strom_ct": {"path": "/wenn/preis_strom_ct"},
        }


# ---------------------------------------------------------------------------
# Mobilität
# ---------------------------------------------------------------------------


@pytest.fixture
def mobilitaet_surface():
    profil = mobilitaet.Mobilitaetsprofil()
    return composer_mobilitaet.stellschrauben_surface(TEXTS, profil), profil


class TestMobilitaetStellschrauben:
    def test_the_sliders_start_where_the_calculation_stands(self, mobilitaet_surface):
        surface, _ = mobilitaet_surface
        sliders = find(surface, "Slider")

        assert len(sliders) == 2
        for slider in sliders:
            start = evaluate(slider["value"], surface.data)
            assert slider["min"] <= start <= slider["max"], (
                f"{slider['label']} opens outside its own range"
            )
            assert start == int(start), f"{slider['label']} opens off the step grid"

    def test_the_untouched_sliders_reproduce_the_domain_figures(
        self, mobilitaet_surface
    ):
        surface, profil = mobilitaet_surface
        km, strom, kraftstoff, monat = [
            evaluate(value, surface.data) for value in live_values(surface)
        ]

        assert km == pytest.approx(profil.jahresfahrleistung_km(), abs=1)

        # The cost view carries the same energy figures over the holding period.
        kosten = mobilitaet.kostenvergleich(profil, TEXTS)
        jahre = profil.haltedauer_jahre
        assert strom == pytest.approx(kosten["serien"][0]["werte"][1] / jahre, abs=2)
        assert kraftstoff == pytest.approx(
            kosten["serien"][1]["werte"][1] / jahre, abs=2
        )
        assert monat == pytest.approx((kraftstoff - strom) / 12, abs=1)

    def test_a_dragged_slider_lands_where_the_backend_would(self, mobilitaet_surface):
        surface, _ = mobilitaet_surface
        data = {**surface.data, "wenn": {"taeglich_km": 30, "anteil_zuhause": 80}}

        km, strom, _, _ = [evaluate(value, data) for value in live_values(surface)]

        profil = mobilitaet.Mobilitaetsprofil(taeglich_km=30, anteil_zuhause_laden=80)
        kosten = mobilitaet.kostenvergleich(profil, TEXTS)
        assert km == pytest.approx(profil.jahresfahrleistung_km(), abs=1)
        assert strom == pytest.approx(
            kosten["serien"][0]["werte"][1] / profil.haltedauer_jahre, abs=2
        )

    def test_the_button_hands_the_slider_values_back(self, mobilitaet_surface):
        surface, _ = mobilitaet_surface
        button = find(surface, "Button")[0]

        assert button["action"]["event"]["name"] == "annahmen_uebernehmen"
        assert button["action"]["event"]["context"] == {
            "taeglich_km": {"path": "/wenn/taeglich_km"},
            "anteil_zuhause": {"path": "/wenn/anteil_zuhause"},
        }


# ---------------------------------------------------------------------------
# The round trip
# ---------------------------------------------------------------------------


class TestAnnahmenUebernehmen:
    def test_energie_prices_reach_every_later_view(self, ctx):
        from app.journeys import energie as journey

        journey.stellschrauben_zeigen(tool_context=ctx)
        ctx.reset_event()
        journey.annahmen_uebernehmen(
            tool_context=ctx, preis_alt_ct=25.0, preis_strom_ct=22.0
        )

        profil = journey._profil(ctx)
        assert profil.preis_alt_ct == 25.0
        assert profil.preis_strom_ct == 22.0

        # Cheap electricity against expensive gas: the case must get stronger.
        szenarien = journey._szenarien(ctx)
        bestand = next(s for s in szenarien if s.id == "bestand")
        fokus = next(s for s in szenarien if s.id == "waermepumpe")
        assert bestand.energiekosten_eur_a > fokus.energiekosten_eur_a * 2

        # And the visible assumptions must say whose numbers these are.
        assert any("Ihre eigenen Annahmen" in a for a in energie.annahmen(profil, TEXTS))

    def test_mobilitaet_values_reach_every_later_view(self, ctx):
        from app.journeys import mobilitaet as journey

        journey.stellschrauben_zeigen(tool_context=ctx)
        ctx.reset_event()
        journey.annahmen_uebernehmen(
            tool_context=ctx, taeglich_km=40.0, anteil_zuhause=90.0
        )

        profil = journey._profil(ctx)
        assert profil.taeglich_km == 40.0
        assert profil.anteil_zuhause_laden == 90.0

        # Charging at home is the biggest lever there is; it must show.
        assert mobilitaet.mischpreis_eur_kwh(profil) < mobilitaet.ladepreis_eur_kwh(
            "nur_oeffentlich"
        )
        assert any("von Ihnen gesetzt" in a for a in mobilitaet.annahmen(profil, TEXTS))

    def test_the_view_the_person_is_looking_at_is_rebuilt(self, ctx):
        """Stale figures next to fresh ones would be worse than no update."""
        from app.journeys import mobilitaet as journey

        journey.kosten_vergleichen(tool_context=ctx)
        ctx.reset_event()
        journey.annahmen_uebernehmen(
            tool_context=ctx, taeglich_km=40.0, anteil_zuhause=90.0
        )

        rebuilt = {w.payload["surfaceId"] for w in ctx.widgets}
        assert "kosten" in rebuilt
        assert "stellschrauben" in rebuilt
