"""Tone has to survive the trip to the browser.

The advice is allowed to say uncomfortable things — "das E-Auto ist bei Ihrem
Profil teurer" — and the design has to be able to show that. For a long time it
could not: `stat_card` encoded tone as an ASCII glyph glued onto the heading
text, so the strongest signal on screen, colour, said "positive" on every card.
The figure for how much *more* an EV costs was painted the same brand green as
the CO2 saving next to it.

These pin tone to the wire, and pin the two figures that made the bug visible.
"""

from __future__ import annotations

import pytest

from app.a2ui import composer_energie, composer_mobilitaet
from app.a2ui.builder import SurfaceBuilder
from app.texts import Texts
from app.domain import energie, mobilitaet


#: These tests are about tone, bindings and arithmetic, none of which is
#: language-specific; the bilingual coverage is in test_readback and test_texts.
TEXTS = Texts("de")


def stat_cards(surface) -> list[dict]:
    return [c for c in surface.components if c.get("component") == "StatCard"]


def card_titled(surface, needle: str) -> dict:
    for card in stat_cards(surface):
        if isinstance(card.get("title"), str) and needle in card["title"]:
            return card
    raise AssertionError(
        f"no stat card titled like {needle!r}; have "
        f"{[c.get('title') for c in stat_cards(surface)]}"
    )


class TestToneReachesTheWire:
    def test_a_stat_card_carries_its_tone_as_a_property(self):
        b = SurfaceBuilder("x", "x", TEXTS)
        b.root(
            b.stat_card(
                title="Teurer",
                metric="1.907 EUR",
                body="Das kostet Sie mehr.",
                tone="caution",
            )
        )
        card = stat_cards(b.finish())[0]

        assert card["tone"] == "caution"
        # And nowhere else: a glyph inside the title would put the tone back
        # into a Markdown string where no stylesheet can reach it.
        assert card["title"] == "Teurer"

    def test_the_body_stays_a_child_so_it_keeps_its_markdown(self):
        b = SurfaceBuilder("x", "x", TEXTS)
        b.root(b.stat_card(title="T", body="**fett**", tone="neutral"))
        surface = b.finish()

        card = stat_cards(surface)[0]
        body = next(c for c in surface.components if c["id"] == card["child"])
        assert body["component"] == "Text"
        assert body["text"] == "**fett**"

    def test_a_card_without_a_metric_still_renders(self):
        b = SurfaceBuilder("x", "x", TEXTS)
        b.root(b.stat_card(title="Nur Text", body="Kein Wert."))
        card = stat_cards(b.finish())[0]

        assert "metric" not in card
        assert card["tone"] == "neutral"


class TestToneMatchesTheAdvice:
    def test_the_expensive_case_is_marked_as_a_downside(self):
        """The demo's most important moment: an honest "no".

        Without a wallbox the EV is the more expensive choice, and the card
        saying so must not be able to look like good news.
        """
        profil = mobilitaet.Mobilitaetsprofil()
        kosten = mobilitaet.kostenvergleich(profil, TEXTS)
        assert kosten["differenz_eur"] < 0, "the demo profile is meant to be unfavourable"

        surface = composer_mobilitaet.kosten_surface(TEXTS, profil)
        assert card_titled(surface, "Elektro gegen Verbrenner")["tone"] == "caution"

    def test_the_favourable_case_is_marked_as_an_advantage(self):
        profil = mobilitaet.Mobilitaetsprofil(
            taeglich_km=80, lademoeglichkeit="wallbox_zuhause", haltedauer_jahre=6
        )
        kosten = mobilitaet.kostenvergleich(profil, TEXTS)
        assert kosten["differenz_eur"] > 0

        surface = composer_mobilitaet.kosten_surface(TEXTS, profil)
        assert card_titled(surface, "Elektro gegen Verbrenner")["tone"] == "positive"

    def test_a_house_that_needs_hot_radiators_is_flagged(self):
        profil = energie.Gebaeudeprofil(waermesystem="heizkoerper_klein_alt")
        surface = composer_energie.eignung_surface(TEXTS, profil)
        assert card_titled(surface, "Vorlauftemperatur")["tone"] == "caution"

    def test_a_house_that_does_not_is_not(self):
        profil = energie.Gebaeudeprofil(waermesystem="fussbodenheizung")
        surface = composer_energie.eignung_surface(TEXTS, profil)
        assert card_titled(surface, "Vorlauftemperatur")["tone"] == "positive"


class TestToneIsNotOverclaimed:
    """A tie is not a win, and colour should not say otherwise."""

    def test_a_two_cent_gap_is_a_wash(self):
        assert composer_mobilitaet._energie_tone(11.37, 11.39) == "neutral"

    def test_a_real_gap_is_an_advantage(self):
        assert composer_mobilitaet._energie_tone(6.53, 11.39) == "positive"

    def test_being_more_expensive_is_a_downside(self):
        assert composer_mobilitaet._energie_tone(12.50, 11.39) == "caution"

    def test_the_default_profile_does_not_claim_an_energy_win(self):
        """The demo case: 11,37 € against 11,39 € is a tie, not a saving."""
        surface = composer_mobilitaet.kosten_surface(TEXTS, mobilitaet.Mobilitaetsprofil())
        assert card_titled(surface, "Energie je 100 km")["tone"] == "neutral"


class TestEveryToneIsUsedSomewhere:
    @pytest.mark.parametrize("journey_surface", ["kosten", "stellschrauben"])
    def test_tone_is_always_one_of_the_three(self, journey_surface):
        profil = mobilitaet.Mobilitaetsprofil()
        surface = (
            composer_mobilitaet.kosten_surface(TEXTS, profil)
            if journey_surface == "kosten"
            else composer_mobilitaet.stellschrauben_surface(TEXTS, profil)
        )
        for card in stat_cards(surface):
            assert card["tone"] in {"positive", "neutral", "caution"}

    def test_what_if_figures_make_no_claim(self):
        """They move as the client drags, so a fixed tone would be a lie."""
        surface = composer_mobilitaet.stellschrauben_surface(TEXTS, 
            mobilitaet.Mobilitaetsprofil()
        )
        assert {c["tone"] for c in stat_cards(surface)} == {"neutral"}
