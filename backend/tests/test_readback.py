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

Everything here runs in both languages, and the assertions look up what they
expect in the catalog rather than spelling out a German phrase: a test that
hard-codes "am höchsten" passes in German and proves nothing about the English
session, which is the half more likely to be broken.
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
from app.texts import LOCALES, Texts


@pytest.fixture(params=LOCALES)
def t(request):
    """Both languages, because the readback speaks whichever the client picked."""
    return Texts(request.param)


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
def surfaces(t, haus, alltag):
    """Every composed surface that carries figures, both journeys."""
    szenarien = calc_e.szenarien(haus)
    bestand, fokus = szenarien[0], szenarien[1]
    foerderung = calc_e.foerderung(min(fokus.investition_eur, 30_000))
    return [
        ce.profil_surface(t, haus, []),
        ce.eignung_surface(t, haus),
        ce.szenarien_surface(t, haus, szenarien, empfohlen_id="waermepumpe"),
        ce.wirtschaftlichkeit_surface(t, haus, szenarien, fokus_id="waermepumpe"),
        ce.foerderung_surface(t, haus, fokus, foerderung),
        ce.stellschrauben_surface(t, haus, bestand, fokus),
        cm.profil_surface(t, alltag, []),
        cm.alltag_surface(t, alltag),
        cm.laden_surface(t, alltag),
        cm.fahrzeuge_surface(t, alltag),
        cm.kosten_surface(t, alltag),
        cm.stellschrauben_surface(t, alltag),
    ]


def tail(t: Texts, key: str, **fields: object) -> str:
    """The wording that follows the last filled data hole in a catalog entry.

    Lets an assertion say "it used the phrase for a live figure" without naming
    that phrase in either language. Holes not passed in stay as literal `{}`
    placeholders, so a caller can anchor on the middle of an entry.
    """
    filled = {name: "\x00" for name in fields}
    empty = {
        name: ""
        for name in _holes(t, key)
        if name not in filled
    }
    return t(key, **filled, **empty).split("\x00")[-1].strip()


def head(t: Texts, key: str, **fields: object) -> str:
    """The wording that precedes the first data hole."""
    filled = {name: "\x00" for name in fields}
    return t(key, **filled).split("\x00")[0].strip()


def _holes(t: Texts, key: str) -> list[str]:
    import string

    template = t.get(key, "") or t(key, **{})
    return [name for _, name, _, _ in string.Formatter().parse(template) if name]


class TestItDescribesWhatIsThere:
    def test_every_chart_and_table_is_mentioned(self, t, surfaces):
        table_word = head(t, "readback.table", titel=1, spalten=1).lower()

        for surface in surfaces:
            described = readback.describe(surface, t).lower()
            for component in surface.components:
                kind = component.get("component")
                if kind == "MetricChart":
                    # Named by its own type, not by any chart word: "line
                    # chart" and "bar chart" share a word in English, so a
                    # loose check would pass on a chart described as the
                    # wrong kind.
                    chart_type = str(component.get("chartType") or "bar")
                    assert t(f"readback.chart.{chart_type}").lower() in described, (
                        f"{surface.surface_id}: {chart_type}"
                    )
                if kind == "ComparisonTable":
                    assert table_word in described, surface.surface_id

    def test_a_chart_names_its_axis_and_every_line(self, t, haus):
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.wirtschaftlichkeit_surface(t, haus, szenarien, fokus_id="waermepumpe"), t
        )

        assert t("energie.jahr", jahr=20) in described
        for szenario in szenarien:
            assert t(szenario.label) in described, szenario.label

    def test_the_line_crossing_is_named_as_the_client_sees_it(self, t, haus):
        # The precise break-even comes from `calc.amortisation` in the same
        # tool result; this one has to stay an interval between plotted points
        # so the two can never disagree by a year in front of the client.
        described = readback.describe(
            ce.wirtschaftlichkeit_surface(
                t, haus, calc_e.szenarien(haus), fokus_id="waermepumpe"
            ),
            t,
        )

        assert head(t, "readback.crossing", vorher=1, nachher=1, fuehrend=1) in described

    def test_the_sliders_say_they_belong_to_the_client(self, t, haus):
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.stellschrauben_surface(t, haus, szenarien[0], szenarien[1]), t
        )
        theirs = tail(t, "readback.slider", label=1, bereich=1, stand=1)

        assert described.count(theirs) >= 2

    def test_a_bar_chart_says_which_category_is_tallest(self, t, haus):
        # Bars are read as a comparison between categories, so the height
        # alone leaves out the half the client is pointing at.
        described = readback.describe(ce.eignung_surface(t, haus), t)
        # The words between the peak value and the category it belongs to.
        highest = tail(t, "readback.series.bars", min=1, peak=1).split("\x00")[0]

        assert highest in described


class TestItInventsNothing:
    def test_no_number_appears_that_the_surface_does_not_contain(self, t, surfaces):
        for surface in surfaces:
            # Both sides through the same canonical form: a surface holds some
            # figures as raw JSON numbers and others as strings the composer
            # already set for this locale.
            present = _numbers(
                json.dumps([surface.components, surface.data], ensure_ascii=False),
                t.locale,
            )

            for number in _numbers(readback.describe(surface, t), t.locale):
                assert number in present, f"{surface.surface_id}: invented {number}"

    def test_a_live_figure_is_never_given_a_value(self, t, haus):
        # The what-if cards compute in the browser from wherever the client
        # left the slider, so any figure named here would be a guess.
        szenarien = calc_e.szenarien(haus)

        described = readback.describe(
            ce.stellschrauben_surface(t, haus, szenarien[0], szenarien[1]), t
        )

        assert tail(t, "readback.stat.live", titel=1) in described

    def test_an_unresolvable_binding_is_left_out_rather_than_guessed(self, t):
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

        assert "Ohne Daten" not in readback.describe(surface, t)


class TestItWritesNumbersTheWayTheLocaleDoes:
    def test_figures_use_the_locale_separators(self, t, surfaces):
        # German groups thousands with a point and writes decimals with a
        # comma; English the other way round. Either separator followed by
        # fewer than three digits is a decimal separator — and therefore wrong
        # if it is the one this locale groups with.
        wrong = r"\d\.\d{1,2}(?!\d)" if t.locale == "de" else r"\d,\d{1,2}(?!\d)"

        for surface in surfaces:
            described = readback.describe(surface, t)

            assert not re.search(wrong, described), f"{surface.surface_id}/{t.locale}"


class TestItStaysShortEnoughToCarry:
    def test_no_surface_overruns_the_ceiling(self, t, surfaces):
        # It rides along on every tool result in a live audio session.
        for surface in surfaces:
            assert len(readback.describe(surface, t)) <= readback.MAX_CHARS + 200

    def test_an_oversized_surface_is_cut_rather_than_sent_whole(self, t):
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

        described = readback.describe(surface, t)

        assert len(described) <= readback.MAX_CHARS + 200
        assert t("readback.truncated").strip() in described


class TestItReadsEachChartTheWayItIsDrawn:
    def test_a_flat_reference_line_is_not_described_as_a_range(self, t, alltag):
        # The winter range is drawn straight across the week. "258 km bis
        # 258 km, am höchsten (Mo)" is what a naive shape description says
        # about it, and it reads as broken.
        described = readback.describe(cm.alltag_surface(t, alltag), t)

        assert tail(t, "readback.series.flat", wert=1) in described
        assert not re.search(r"(\d[\d.,]* km)\D{1,8}\1", described)


def _numbers(text: str, locale: str) -> set[float]:
    """Every figure in a piece of text, as a plain number.

    Applies the locale's reading: the thousands separator groups three digits,
    the other one is the decimal point. That maps `18.200 €` in German and
    `€18,200` in English onto the same value as a raw JSON `18200`, which is
    what lets one function canonicalise both the readback and the surface it
    came from.
    """
    thousands, decimal = (".", ",") if locale == "de" else (",", ".")
    found: set[float] = set()
    for token in re.findall(r"\d[\d.,]*", text):
        plain = re.sub(rf"\{thousands}(?=\d{{3}}(?!\d))", "", token.rstrip(".,"))
        try:
            found.add(float(plain.replace(decimal, ".")))
        except ValueError:
            continue
    return found
