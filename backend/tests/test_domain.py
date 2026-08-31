"""The advisory arithmetic.

The point of computing these server-side is that the same situation always
produces the same advice. These lock in the relationships that carry the story
— not the exact numbers, which move with the demo data.
"""

from __future__ import annotations

import pytest

from app.texts import Texts
from app.domain import energie, mobilitaet


#: The domain calculates; only its labels and assumption lines are worded,
#: and those are covered per language in test_texts and test_readback.
TEXTS = Texts("de")


class TestWaermebedarf:
    def test_measured_consumption_beats_the_estimate(self):
        profil = energie.Gebaeudeprofil(wohnflaeche_qm=160, verbrauch_kwh_a=18000)
        assert energie.waermebedarf_kwh_a(profil) == 18000

    def test_older_and_less_renovated_means_more_demand(self):
        alt = energie.Gebaeudeprofil(baujahr=1970, sanierungsstand="unsaniert")
        neu = energie.Gebaeudeprofil(baujahr=2015, sanierungsstand="saniert")
        assert energie.waermebedarf_kwh_a(alt) > energie.waermebedarf_kwh_a(neu)


class TestEignung:
    def test_underfloor_heating_scores_better_than_old_radiators(self):
        gut = energie.Gebaeudeprofil(waermesystem="fussbodenheizung")
        schlecht = energie.Gebaeudeprofil(waermesystem="heizkoerper_klein_alt")

        assert energie.eignung(gut)["score"] > energie.eignung(schlecht)["score"]

    def test_lower_flow_temperature_gives_a_higher_seasonal_factor(self):
        assert energie.jaz(35) > energie.jaz(55) > energie.jaz(65)

    def test_flow_temperature_interpolates_between_the_known_points(self):
        assert energie.jaz(65) < energie.jaz(60) < energie.jaz(55)

    def test_electricity_demand_follows_from_heat_demand_and_jaz(self):
        profil = energie.Gebaeudeprofil(verbrauch_kwh_a=20000)
        check = energie.eignung(profil)
        assert check["strombedarf_kwh_a"] == pytest.approx(20000 / check["jaz"], rel=0.01)


class TestFoerderung:
    def test_bonuses_add_up_and_are_capped(self):
        result = energie.foerderung(
            40000,
            klimageschwindigkeitsbonus=True,
            einkommensbonus=True,
            effizienzbonus=True,
        )
        assert result["satz_ungedeckelt"] > result["satz"]
        assert result["satz"] == energie.dd.FOERDERUNG["max_satz"]

    def test_eligible_costs_are_capped(self):
        # Spending more than the ceiling must not increase the grant.
        klein = energie.foerderung(30000)
        gross = energie.foerderung(90000)
        assert klein["betrag_eur"] == gross["betrag_eur"]


class TestSzenarien:
    def test_every_scenario_is_cheaper_to_run_than_the_status_quo(self):
        profil = energie.Gebaeudeprofil(heizung="gas", verbrauch_kwh_a=22000)
        szenarien = energie.szenarien(profil)
        bestand = next(s for s in szenarien if s.id == "bestand")

        for szenario in szenarien:
            if szenario.id == "bestand":
                continue
            assert szenario.energiekosten_eur_a < bestand.energiekosten_eur_a
            assert szenario.co2_kg_a < bestand.co2_kg_a

    def test_own_share_is_investment_minus_grant(self):
        profil = energie.Gebaeudeprofil()
        for szenario in energie.szenarien(profil):
            assert szenario.eigenanteil_eur == pytest.approx(
                szenario.investition_eur - szenario.foerderung_eur
            )

    def test_cumulative_costs_only_grow(self):
        profil = energie.Gebaeudeprofil()
        verlauf = energie.kostenverlauf(energie.szenarien(profil), TEXTS)

        for serie in verlauf["serien"]:
            assert serie["werte"] == sorted(serie["werte"])

    def test_a_heat_pump_pays_back_within_the_horizon(self):
        profil = energie.Gebaeudeprofil(heizung="gas", verbrauch_kwh_a=22000)
        szenarien = energie.szenarien(profil)
        amort = energie.amortisation(
            next(s for s in szenarien if s.id == "bestand"),
            next(s for s in szenarien if s.id == "waermepumpe"),
        )
        assert amort["erreichbar"]
        assert 5 <= amort["jahre"] <= 25


class TestReichweite:
    def test_winter_range_is_below_summer_range(self):
        r = mobilitaet.reichweite(mobilitaet.Mobilitaetsprofil())
        assert (
            r["reichweite_autobahn_winter_km"]
            < r["reichweite_winter_km"]
            < r["reichweite_sommer_km"]
        )

    def test_a_short_commute_needs_no_daily_charging(self):
        profil = mobilitaet.Mobilitaetsprofil(taeglich_km=40)
        assert not mobilitaet.reichweite(profil)["taeglich_laden_noetig"]

    def test_a_very_long_commute_does(self):
        profil = mobilitaet.Mobilitaetsprofil(taeglich_km=300)
        assert mobilitaet.reichweite(profil)["taeglich_laden_noetig"]

    def test_a_trip_within_range_needs_no_stop(self):
        profil = mobilitaet.Mobilitaetsprofil(langstrecke_km=120)
        assert mobilitaet.langstrecke(profil, TEXTS)["ladestopps"] == 0

    def test_a_longer_trip_needs_more_stops(self):
        kurz = mobilitaet.langstrecke(mobilitaet.Mobilitaetsprofil(langstrecke_km=300), TEXTS)
        lang = mobilitaet.langstrecke(mobilitaet.Mobilitaetsprofil(langstrecke_km=900), TEXTS)
        assert lang["ladestopps"] > kurz["ladestopps"]


class TestLadenUndKosten:
    def test_home_charging_is_cheaper_than_public_charging(self):
        assert mobilitaet.ladepreis_eur_kwh(
            "wallbox_zuhause"
        ) < mobilitaet.ladepreis_eur_kwh("nur_oeffentlich")

    def test_the_charging_setup_decides_the_business_case(self):
        """The demo's core insight: where you charge, not which car you buy."""
        zuhause = mobilitaet.kostenvergleich(
            mobilitaet.Mobilitaetsprofil(lademoeglichkeit="wallbox_zuhause")
        , TEXTS)
        oeffentlich = mobilitaet.kostenvergleich(
            mobilitaet.Mobilitaetsprofil(lademoeglichkeit="nur_oeffentlich")
        , TEXTS)

        assert zuhause["differenz_eur"] > oeffentlich["differenz_eur"]
        assert zuhause["differenz_eur"] > 0

    def test_electric_saves_co2_against_the_grid_mix(self):
        result = mobilitaet.kostenvergleich(mobilitaet.Mobilitaetsprofil(), TEXTS)
        assert result["co2_ersparnis_kg_a"] > 0

    def test_the_cost_items_add_up_to_the_total(self):
        result = mobilitaet.kostenvergleich(mobilitaet.Mobilitaetsprofil(), TEXTS)
        elektro = next(s for s in result["serien"] if s["label"] == "Elektro")
        assert sum(elektro["werte"]) == pytest.approx(result["gesamt_elektro_eur"], abs=1)


class TestFahrzeugvorschlaege:
    def test_suggestions_come_back_ranked(self):
        vorschlaege = mobilitaet.fahrzeugvorschlaege(mobilitaet.Mobilitaetsprofil(), TEXTS)
        scores = [v["score"] for v in vorschlaege]
        assert scores == sorted(scores, reverse=True)

    def test_every_suggestion_names_a_trade_off(self):
        # Advice that only lists upsides is advertising, not advice.
        for v in mobilitaet.fahrzeugvorschlaege(mobilitaet.Mobilitaetsprofil(), TEXTS):
            assert v["contra"]
            assert v["pro"]

    def test_a_car_over_budget_is_ranked_lower(self):
        profil = mobilitaet.Mobilitaetsprofil(budget_eur_monat=360)
        vorschlaege = mobilitaet.fahrzeugvorschlaege(profil, TEXTS, anzahl=4)
        gefunden = {v["id"]: v["score"] for v in vorschlaege}
        assert gefunden["kompakt"] > gefunden["van"]
