"""What the agent is told about the screen has to match the screen.

The agent chooses when to show something and the composer chooses what, which
left the agent describing a picture it had never seen. `a2ui.readback` closes
that by reading the composed tree, so these tests are about the one property
that makes the idea safe: it may not say anything the surface does not show,
and it may not stay silent about what it does.

The two failures are not symmetric. Inventing a figure puts a wrong number in
the agent's mouth in front of a client. Omitting one only means the agent
cannot answer a question — worse than it sounds on a chart, because the client
is looking straight at the thing they are asking about.
"""

from __future__ import annotations

import json
import re

import pytest

from app.a2ui import composer_energie as ce
from app.a2ui import composer_mobilitaet as cm
from app.a2ui import readback
from app.a2ui.surface import Surface
from app.domain import energie as calc_e
from app.domain import mobilitaet as calc_m


@pytest.fixture
def haus():
    return calc_e.Gebaeudeprofil(
        baujahr=1985,
        wohnflaeche_qm=200,
        heizung="gas",
        waermesystem="flaechenheizkoerper_gross",
    )


@pytest.fixture
def alltag():
    return calc_m.Mobilitaetsprofil()


@pytest.fixture
def surfaces(haus, alltag):
    """Every composed surface that carries figures, both journeys."""
    szenarien = calc_e.szenarien(haus)
    bestand, fokus = szenarien[0], szenarien[1]
    foerderung = calc_e.foerderung(min(fokus.investition_eur, 30_000))
    return [
        ce.profil_surface(haus, []),
        ce.eignung_surface(haus),
        ce.szenarien_surface(haus, szenarien, empfohlen_id="waermepumpe"),
        ce.wirtschaftlichkeit_surface(haus, szenarien, fokus_id="waermepumpe"),
        ce.foerderung_surface(haus, fokus, foerderung),
        ce.stellschrauben_surface(haus, bestand, fokus),
        cm.profil_surface(alltag, []),
        cm.alltag_surface(alltag),
        cm.laden_surface(alltag),
        cm.fahrzeuge_surface(alltag),
        cm.kosten_surface(alltag),
        cm.stellschrauben_surface(alltag),
    ]


class TestItDescribesWhatIsThere:
    def test_every_chart_and_table_is_mentioned(self, surfaces):
        for surface in surfaces:
            described = readback.describe(surface)
            for component in surface.components:
                kind = component.get("component")
                if kind == "MetricChart":
                    assert "diagramm" in described.lower(), surface.surface_id
                if kind == "ComparisonTable":
                    assert "Vergleichstabelle" in described, surface.surface_id

    def test_a_chart_names_its_axis_and_every_line(self, haus):
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.wirtschaftlichkeit_surface(haus, szenarien, fokus_id="waermepumpe")
        )

        assert "Jahr 20" in described
        for szenario in szenarien:
            assert szenario.label in described, szenario.label

    def test_the_line_crossing_is_named_as_the_client_sees_it(self, haus):
        # The precise break-even comes from `calc.amortisation` in the same
        # tool result; this one has to stay an interval between plotted points
        # so the two can never disagree by a year in front of the client.
        described = readback.describe(
            ce.wirtschaftlichkeit_surface(haus, calc_e.szenarien(haus), fokus_id="waermepumpe")
        )

        assert "kreuzen sich zwischen" in described

    def test_the_sliders_say_they_belong_to_the_client(self, haus):
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.stellschrauben_surface(haus, szenarien[0], szenarien[1])
        )

        assert described.count("Regler") >= 2
        assert "selbst bewegen" in described

    def test_a_bar_chart_says_which_category_is_tallest(self, haus):
        # Bars are read as a comparison between categories, so the height
        # alone leaves out the half the client is pointing at.
        described = readback.describe(ce.eignung_surface(haus))

        assert "am höchsten" in described


class TestItInventsNothing:
    def test_no_number_appears_that_the_surface_does_not_contain(self, surfaces):
        for surface in surfaces:
            # Both sides through the same canonical form: a surface holds some
            # figures as raw JSON numbers and others as strings the composer
            # already set in German, and `18.200 €` and `18200` are the same
            # number.
            present = _numbers(json.dumps([surface.components, surface.data], ensure_ascii=False))

            for number in _numbers(readback.describe(surface)):
                assert number in present, f"{surface.surface_id}: invented {number}"

    def test_a_live_figure_is_never_given_a_value(self, haus):
        # The what-if cards compute in the browser from wherever the client
        # left the slider, so any figure named here would be a guess.
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.stellschrauben_surface(haus, szenarien[0], szenarien[1])
        )

        assert "rechnet live mit den Reglern mit" in described

    def test_an_unresolvable_binding_is_left_out_rather_than_guessed(self):
        surface = Surface(
            surface_id="x",
            title="Test",
            components=[
                {
                    "id": "root",
                    "component": "MetricChart",
                    "title": "Ohne Daten",
                    "categories": {"path": "/fehlt"},
                    "series": {"path": "/auch_weg"},
                }
            ],
            data={},
        )

        assert "Ohne Daten" not in readback.describe(surface)


class TestItReadsGerman:
    def test_figures_use_the_german_decimal_comma(self, surfaces):
        for surface in surfaces:
            # A point grouping thousands is followed by exactly three digits;
            # anything shorter is a decimal point that should be a comma.
            described = readback.describe(surface)

            assert not re.search(r"\d\.\d{1,2}(?!\d)", described), surface.surface_id


class TestItStaysShortEnoughToCarry:
    def test_no_surface_overruns_the_ceiling(self, surfaces):
        # It rides along on every tool result in a live audio session.
        for surface in surfaces:
            assert len(readback.describe(surface)) <= readback.MAX_CHARS + 200

    def test_an_oversized_surface_is_cut_rather_than_sent_whole(self):
        surface = Surface(
            surface_id="viel",
            title="Viel",
            components=[
                {
                    "id": f"s{i}",
                    "component": "StatCard",
                    "title": f"Kennzahl Nummer {i} mit einem ziemlich langen Titel",
                    "metric": f"{i} €",
                }
                for i in range(200)
            ]
            + [{"id": "root", "component": "Column", "children": []}],
            data={},
        )

        described = readback.describe(surface)

        assert len(described) <= readback.MAX_CHARS + 200
        assert "gekürzt" in described


def _numbers(text: str) -> set[float]:
    """Every figure in a piece of text, as a plain number.

    Applies the German reading: a point followed by exactly three digits groups
    thousands, anything else is a decimal point. That maps `18.200 €` and a raw
    JSON `18200` onto the same value, which is what lets the same function
    canonicalise both the readback and the surface it came from.
    """
    found: set[float] = set()
    for token in re.findall(r"\d[\d.,]*", text):
        plain = re.sub(r"\.(?=\d{3}(?!\d))", "", token.rstrip(".,")).replace(",", ".")
        try:
            found.add(float(plain))
        except ValueError:
            continue
    return found


class TestItReadsEachChartTheWayItIsDrawn:
    def test_a_flat_reference_line_is_not_described_as_a_range(self, alltag):
        # The winter range is drawn straight across the week. "258 km bis
        # 258 km, am höchsten (Mo)" is what a naive shape description says
        # about it, and it reads as broken.
        described = readback.describe(cm.alltag_surface(alltag))

        assert "durchgehend" in described
        assert not re.search(r"(\S+ km) bis \1", described)
