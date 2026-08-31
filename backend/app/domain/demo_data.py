"""Demo assumptions for the German market.

Every number in this module is a **plausible demo value**, not a quote and not
regulatory advice. The briefing asks for "plausible, klar gekennzeichnete
Beispieldaten" and for assumptions to be made visible, so each block carries a
label and an as-of date that is surfaced in the UI through the
``AssumptionNote`` component.

Update ``STAND`` and the values here to re-point the demo at current market
data; nothing else in the codebase hardcodes prices.
"""

from __future__ import annotations

from typing import Final

# The as-of date, the source labels and the disclaimer are words rather than
# figures, so they live in `app.texts` with the rest of the copy — see
# `data.as_of`, `data.source.*` and `data.disclaimer`.

# ---------------------------------------------------------------------------
# Energiepreise (Brutto, Endkunde)
# ---------------------------------------------------------------------------

#: Whole cents per kilowatt-hour, deliberately.
#:
#: These are the prices the client can take over from the advisory view and
#: adjust for themselves, and the A2UI `Slider` steps in ones — so a price that
#: is not a whole number of cents would put the thumb half a step away from the
#: figure the rest of the advice is built on. They are demo assumptions either
#: way; being round makes them both legible and adjustable.
STROM_HAUSHALT_EUR_KWH: Final = 0.35
STROM_WAERMEPUMPE_EUR_KWH: Final = 0.27
GAS_EUR_KWH: Final = 0.12
HEIZOEL_EUR_L: Final = 1.10
HEIZOEL_KWH_PRO_L: Final = 10.0
FERNWAERME_EUR_KWH: Final = 0.15
PV_EINSPEISUNG_EUR_KWH: Final = 0.079
PV_GESTEHUNG_EUR_KWH: Final = 0.11

#: Angenommene jährliche Preissteigerung für die 20-Jahres-Betrachtung.
PREISPFAD_STROM_P_A: Final = 0.02
PREISPFAD_GAS_P_A: Final = 0.045  # inkl. steigender CO2-Bepreisung
PREISPFAD_KRAFTSTOFF_P_A: Final = 0.035

# ---------------------------------------------------------------------------
# Kraftstoffe
# ---------------------------------------------------------------------------

BENZIN_EUR_L: Final = 1.78
DIESEL_EUR_L: Final = 1.68

LADEN_ZUHAUSE_EUR_KWH: Final = 0.30
LADEN_ARBEIT_EUR_KWH: Final = 0.15
LADEN_AC_OEFFENTLICH_EUR_KWH: Final = 0.55
LADEN_DC_SCHNELL_EUR_KWH: Final = 0.69

# ---------------------------------------------------------------------------
# Emissionsfaktoren (g CO2e)
# ---------------------------------------------------------------------------

CO2_STROMMIX_G_KWH: Final = 380.0
CO2_ERDGAS_G_KWH: Final = 201.0
CO2_HEIZOEL_G_KWH: Final = 266.0
CO2_FERNWAERME_G_KWH: Final = 160.0
CO2_BENZIN_G_L: Final = 2370.0
CO2_DIESEL_G_L: Final = 2650.0

# ---------------------------------------------------------------------------
# Gebäude: spezifischer Wärmebedarf in kWh/(m²·a)
# Baualtersklasse -> Sanierungsstand
# ---------------------------------------------------------------------------

WAERMEBEDARF_KWH_QM: Final = {
    "vor_1979": {"unsaniert": 220.0, "teilsaniert": 150.0, "saniert": 100.0},
    "1979_1994": {"unsaniert": 165.0, "teilsaniert": 120.0, "saniert": 85.0},
    "1995_2009": {"unsaniert": 110.0, "teilsaniert": 90.0, "saniert": 70.0},
    "ab_2010": {"unsaniert": 70.0, "teilsaniert": 60.0, "saniert": 45.0},
}

#: Erwartete Jahresarbeitszahl je nötiger Vorlauftemperatur (Luft/Wasser-WP).
JAZ_NACH_VORLAUF: Final = {35: 4.3, 45: 3.8, 55: 3.2, 65: 2.6}

#: Typische Vorlauftemperatur je Heizkörper-Situation.
VORLAUF_NACH_SYSTEM: Final = {
    "fussbodenheizung": 35,
    "flaechenheizkoerper_gross": 45,
    "heizkoerper_standard": 55,
    "heizkoerper_klein_alt": 65,
}

# ---------------------------------------------------------------------------
# Investitionen (schlüsselfertig, inkl. Montage)
# ---------------------------------------------------------------------------

INVEST_EUR: Final = {
    "waermepumpe_luft": 32000.0,
    "waermepumpe_sole": 45000.0,
    "gasheizung_neu": 12000.0,
    "heizkoerper_tausch": 6500.0,
    "daemmung_dach": 22000.0,
    "fenster_tausch": 19000.0,
    "hydraulischer_abgleich": 1200.0,
    "pv_10kwp": 15500.0,
    "speicher_8kwh": 7000.0,
    "wallbox_11kw": 1900.0,
}

#: Förderlogik der Bundesförderung für effiziente Gebäude (Heizungstausch),
#: als Demo-Abbildung. Prozentsätze werden addiert und bei MAX gedeckelt.
FOERDERUNG: Final = {
    "grundfoerderung": 0.30,
    "klimageschwindigkeitsbonus": 0.20,
    "einkommensbonus": 0.30,
    "effizienzbonus": 0.05,
    "max_satz": 0.70,
    "hoechstkosten_efh_eur": 30000.0,
}

WARTUNG_EUR_A: Final = {
    "waermepumpe": 260.0,
    "gasheizung": 220.0,
    "oelheizung": 300.0,
    "fernwaerme": 120.0,
}

# ---------------------------------------------------------------------------
# Fahrzeuge (Demo-Katalog, generische Klassen statt realer Modelle)
# ---------------------------------------------------------------------------

FAHRZEUG_KLASSEN: Final = {
    "kompakt": {
        "label": "Kompaktklasse",
        "batterie_kwh": 58.0,
        "verbrauch_kwh_100km": 16.5,
        "ladeleistung_dc_kw": 130.0,
        "preis_eur": 39500.0,
        "leasing_eur_monat": 359.0,
        "restwert_4j": 0.48,
    },
    "mittelklasse": {
        "label": "Mittelklasse / Limousine",
        "batterie_kwh": 77.0,
        "verbrauch_kwh_100km": 18.5,
        "ladeleistung_dc_kw": 175.0,
        "preis_eur": 52900.0,
        "leasing_eur_monat": 489.0,
        "restwert_4j": 0.46,
    },
    "suv": {
        "label": "SUV / Kombi",
        "batterie_kwh": 84.0,
        "verbrauch_kwh_100km": 21.0,
        "ladeleistung_dc_kw": 150.0,
        "preis_eur": 58500.0,
        "leasing_eur_monat": 549.0,
        "restwert_4j": 0.45,
    },
    "van": {
        "label": "Van / Familienfahrzeug",
        "batterie_kwh": 90.0,
        "verbrauch_kwh_100km": 23.0,
        "ladeleistung_dc_kw": 140.0,
        "preis_eur": 62000.0,
        "leasing_eur_monat": 599.0,
        "restwert_4j": 0.43,
    },
}

VERBRENNER_REFERENZ: Final = {
    "kompakt": {"verbrauch_l_100km": 6.4, "preis_eur": 31500.0, "kraftstoff": "benzin"},
    "mittelklasse": {
        "verbrauch_l_100km": 6.9,
        "preis_eur": 45500.0,
        "kraftstoff": "diesel",
    },
    "suv": {"verbrauch_l_100km": 7.8, "preis_eur": 48500.0, "kraftstoff": "diesel"},
    "van": {"verbrauch_l_100km": 8.2, "preis_eur": 51000.0, "kraftstoff": "diesel"},
}

#: Winterzuschlag auf den Realverbrauch eines E-Autos (Heizung, kalte Batterie).
WINTER_MEHRVERBRAUCH: Final = 0.25
#: Autobahn-Mehrverbrauch bei Langstrecke mit Richtgeschwindigkeit.
LANGSTRECKE_MEHRVERBRAUCH: Final = 0.30
#: Nutzbares Ladefenster auf der Langstrecke (10 % -> 80 % SoC).
LADEFENSTER_ANTEIL: Final = 0.70

WARTUNG_EUR_A_FAHRZEUG: Final = {"elektro": 380.0, "verbrenner": 720.0}
VERSICHERUNG_EUR_A: Final = {"elektro": 780.0, "verbrenner": 720.0}
KFZ_STEUER_EUR_A: Final = {"elektro": 0.0, "verbrenner": 190.0}
THG_QUOTE_EUR_A: Final = 85.0

WALLBOX_INVEST_EUR: Final = INVEST_EUR["wallbox_11kw"]
