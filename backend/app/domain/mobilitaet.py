"""E-Mobilitätsberatung: deterministische Berechnungen für die Demo.

Same principle as :mod:`energie` — the model contributes the client's real
mobility pattern, this module turns it into range, charging and cost figures.
The briefing's framing drives the output: the client should not have to
"understand" an EV, the advice should show how it fits their week.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from . import demo_data as dd

Lademoeglichkeit = Literal[
    "wallbox_zuhause", "steckdose_zuhause", "arbeitsplatz", "nur_oeffentlich"
]
Fahrzeugklasse = Literal["kompakt", "mittelklasse", "suv", "van"]


@dataclass
class Mobilitaetsprofil:
    """Was der Agent aus dem Gespräch verstanden hat."""

    taeglich_km: float = 55.0
    pendeltage_pro_woche: int = 5
    langstrecken_pro_monat: int = 2
    langstrecke_km: float = 450.0
    lademoeglichkeit: Lademoeglichkeit = "nur_oeffentlich"
    stellplatz_vorhanden: bool = True
    fahrzeugklasse: Fahrzeugklasse = "kompakt"
    haltedauer_jahre: int = 4
    budget_eur_monat: float | None = None
    aktueller_verbrauch_l_100km: float | None = None
    bedenken: list[str] = field(default_factory=list)
    prioritaeten: list[str] = field(default_factory=list)

    #: Der Anteil der Ladeenergie, den der Kunde selbst zu Hause veranschlagt,
    #: in Prozent. Solange er leer ist, gilt der Mix der Lademöglichkeit.
    anteil_zuhause_laden: float | None = None

    def jahresfahrleistung_km(self) -> float:
        pendel = self.taeglich_km * self.pendeltage_pro_woche * 46
        langstrecke = self.langstrecke_km * self.langstrecken_pro_monat * 12
        freizeit = 2500.0
        return round(pendel + langstrecke + freizeit)


# ---------------------------------------------------------------------------
# Reichweite und Alltagstauglichkeit
# ---------------------------------------------------------------------------


def reichweite(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Realistische Reichweiten statt WLTP-Katalogwerten.

    Three numbers matter to a sceptical German buyer: summer, winter, and
    winter on the Autobahn. The last one is where range anxiety actually lives.
    """
    fahrzeug = dd.FAHRZEUG_KLASSEN[profil.fahrzeugklasse]
    batterie = fahrzeug["batterie_kwh"]
    basis = fahrzeug["verbrauch_kwh_100km"]

    winter = basis * (1 + dd.WINTER_MEHRVERBRAUCH)
    autobahn_winter = basis * (1 + dd.WINTER_MEHRVERBRAUCH + dd.LANGSTRECKE_MEHRVERBRAUCH)

    def km(verbrauch: float, nutzbar: float = 0.92) -> int:
        return int(batterie * nutzbar / verbrauch * 100)

    sommer_km = km(basis)
    winter_km = km(winter)
    autobahn_km = km(autobahn_winter)

    tagesbedarf = profil.taeglich_km
    puffer_winter = winter_km / max(tagesbedarf, 1.0)

    return {
        "fahrzeug": fahrzeug["label"],
        "batterie_kwh": batterie,
        "verbrauch_sommer": round(basis, 1),
        "verbrauch_winter": round(winter, 1),
        "verbrauch_autobahn_winter": round(autobahn_winter, 1),
        "reichweite_sommer_km": sommer_km,
        "reichweite_winter_km": winter_km,
        "reichweite_autobahn_winter_km": autobahn_km,
        "tagesbedarf_km": tagesbedarf,
        "puffer_faktor_winter": round(puffer_winter, 1),
        "taeglich_laden_noetig": puffer_winter < 1.0,
    }


def wochenprofil(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Die typische Woche als Diagramm — Fahrbedarf gegen Winterreichweite.

    Seeing five commuting days sit well under the winter range does more to
    answer "ist das praktikabel?" than any spec sheet.
    """
    r = reichweite(profil)
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    pendeltage = min(profil.pendeltage_pro_woche, 5)

    fahrbedarf: list[float] = []
    for index, _ in enumerate(tage):
        if index < pendeltage:
            fahrbedarf.append(round(profil.taeglich_km, 0))
        elif index < 5:
            fahrbedarf.append(0.0)
        elif index == 5:
            fahrbedarf.append(round(profil.taeglich_km * 0.8, 0))
        else:
            fahrbedarf.append(round(profil.taeglich_km * 0.4, 0))

    return {
        "kategorien": tage,
        "serien": [
            {"label": "Fahrbedarf", "werte": fahrbedarf},
            {
                "label": "Reichweite im Winter",
                "werte": [r["reichweite_winter_km"]] * len(tage),
            },
        ],
        "einheit": "km",
        "maximaler_tag_km": max(fahrbedarf),
        "wochenstrecke_km": round(sum(fahrbedarf)),
    }


def langstrecke(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Die ausgewählte Langstrecke als Timeline mit echten Ladestopps."""
    r = reichweite(profil)
    fahrzeug = dd.FAHRZEUG_KLASSEN[profil.fahrzeugklasse]
    strecke = profil.langstrecke_km

    # Nutzbares Fenster 10–80 % SoC, danach lädt jedes Auto spürbar langsamer.
    reichweite_pro_ladung = r["reichweite_autobahn_winter_km"] * dd.LADEFENSTER_ANTEIL
    stopps = max(0, int((strecke - r["reichweite_autobahn_winter_km"] * 0.9) // reichweite_pro_ladung) + 1)
    if strecke <= r["reichweite_autobahn_winter_km"] * 0.9:
        stopps = 0

    nachgeladen_kwh = fahrzeug["batterie_kwh"] * dd.LADEFENSTER_ANTEIL
    # Durchschnittsleistung über die Ladekurve liegt deutlich unter der Spitze.
    mittlere_leistung = fahrzeug["ladeleistung_dc_kw"] * 0.62
    ladedauer_min = int(nachgeladen_kwh / mittlere_leistung * 60)

    fahrzeit_min = int(strecke / 115 * 60)
    schritte: list[dict[str, Any]] = [
        {
            "titel": "Start mit 100 %",
            "detail": f"Vollgeladen zu Hause losgefahren – {r['reichweite_autobahn_winter_km']} km Autobahnreichweite im Winter.",
            "dauer": "0 min",
            "status": "start",
        }
    ]
    for i in range(stopps):
        schritte.append(
            {
                "titel": f"Ladestopp {i + 1}",
                "detail": (
                    f"{int(nachgeladen_kwh)} kWh in {ladedauer_min} Minuten "
                    f"bei rund {int(mittlere_leistung)} kW – Zeit für Kaffee und Pause."
                ),
                "dauer": f"{ladedauer_min} min",
                "status": "laden",
            }
        )
    schritte.append(
        {
            "titel": "Ankunft",
            "detail": (
                f"{int(strecke)} km gesamt, reine Fahrzeit rund "
                f"{fahrzeit_min // 60} h {fahrzeit_min % 60} min."
            ),
            "dauer": f"{(fahrzeit_min + stopps * ladedauer_min) // 60} h "
            f"{(fahrzeit_min + stopps * ladedauer_min) % 60} min gesamt",
            "status": "ziel",
        }
    )

    return {
        "strecke_km": strecke,
        "ladestopps": stopps,
        "ladedauer_min": ladedauer_min if stopps else 0,
        "mehrzeit_min": stopps * ladedauer_min,
        "gesamtdauer_min": fahrzeit_min + stopps * ladedauer_min,
        "schritte": schritte,
    }


# ---------------------------------------------------------------------------
# Laden
# ---------------------------------------------------------------------------

#: Wie sich die Ladeenergie je Lademöglichkeit auf die Quellen verteilt.
_LADEMIX: dict[str, dict[str, float]] = {
    "wallbox_zuhause": {"zuhause": 0.80, "arbeit": 0.05, "ac": 0.05, "dc": 0.10},
    "steckdose_zuhause": {"zuhause": 0.50, "arbeit": 0.10, "ac": 0.20, "dc": 0.20},
    "arbeitsplatz": {"zuhause": 0.05, "arbeit": 0.65, "ac": 0.15, "dc": 0.15},
    "nur_oeffentlich": {"zuhause": 0.0, "arbeit": 0.0, "ac": 0.65, "dc": 0.35},
}

_PREIS_JE_QUELLE: dict[str, float] = {
    "zuhause": dd.LADEN_ZUHAUSE_EUR_KWH,
    "arbeit": dd.LADEN_ARBEIT_EUR_KWH,
    "ac": dd.LADEN_AC_OEFFENTLICH_EUR_KWH,
    "dc": dd.LADEN_DC_SCHNELL_EUR_KWH,
}

_QUELLE_LABEL: dict[str, str] = {
    "zuhause": "Zuhause",
    "arbeit": "Arbeitgeber",
    "ac": "Öffentlich AC",
    "dc": "Schnellladen DC",
}


def ladepreis_eur_kwh(lademoeglichkeit: str) -> float:
    mix = _LADEMIX[lademoeglichkeit]
    return sum(anteil * _PREIS_JE_QUELLE[quelle] for quelle, anteil in mix.items())


def mischpreis_eur_kwh(profil: Mobilitaetsprofil) -> float:
    """Der Strompreis, mit dem für dieses Profil gerechnet wird.

    Der Ladeort ist der größte Kostenhebel und zugleich das, was im Gespräch am
    unschärfsten bleibt („meistens zu Hause, manchmal unterwegs“). Hat der Kunde
    selbst eine Quote gesetzt, gilt seine — der Mix der Lademöglichkeit ist nur
    die Ausgangsschätzung.
    """
    if profil.anteil_zuhause_laden is None:
        return ladepreis_eur_kwh(profil.lademoeglichkeit)
    anteil = max(0.0, min(1.0, profil.anteil_zuhause_laden / 100.0))
    return (
        anteil * dd.LADEN_ZUHAUSE_EUR_KWH
        + (1 - anteil) * ladepreis_eur_kwh("nur_oeffentlich")
    )


def ladeoptionen(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Vergleicht die realistischen Ladeszenarien für dieses Profil.

    The single biggest cost lever for a German EV buyer is where they charge,
    not which car they buy — so this comparison comes before the vehicle.
    """
    r = reichweite(profil)
    jahres_km = profil.jahresfahrleistung_km()
    # Realverbrauch als Mischung aus Sommer, Winter und Autobahnanteil.
    verbrauch = r["verbrauch_sommer"] * 1.15
    jahres_kwh = jahres_km * verbrauch / 100.0

    optionen: list[dict[str, Any]] = []
    for schluessel, label, invest, verfuegbar in (
        (
            "wallbox_zuhause",
            "Wallbox zu Hause",
            dd.WALLBOX_INVEST_EUR,
            profil.stellplatz_vorhanden,
        ),
        ("arbeitsplatz", "Laden beim Arbeitgeber", 0.0, True),
        ("nur_oeffentlich", "Nur öffentlich laden", 0.0, True),
    ):
        preis = ladepreis_eur_kwh(schluessel)
        kosten_a = jahres_kwh * preis
        optionen.append(
            {
                "id": schluessel,
                "label": label,
                "verfuegbar": verfuegbar,
                "mischpreis_eur_kwh": round(preis, 3),
                "kosten_eur_a": round(kosten_a),
                "kosten_eur_100km": round(kosten_a / jahres_km * 100, 2),
                "investition_eur": invest,
                "mix": [
                    {"label": _QUELLE_LABEL[q], "anteil": a}
                    for q, a in _LADEMIX[schluessel].items()
                    if a > 0
                ],
            }
        )

    aktuell = next(o for o in optionen if o["id"] == profil.lademoeglichkeit) if profil.lademoeglichkeit in _LADEMIX else optionen[-1]
    beste = min((o for o in optionen if o["verfuegbar"]), key=lambda o: o["kosten_eur_a"])

    return {
        "jahres_kwh": round(jahres_kwh),
        "jahres_km": jahres_km,
        "optionen": optionen,
        "aktuell_id": aktuell["id"],
        "beste_id": beste["id"],
        "ersparnis_beste_eur_a": round(aktuell["kosten_eur_a"] - beste["kosten_eur_a"]),
    }


# ---------------------------------------------------------------------------
# Kosten
# ---------------------------------------------------------------------------


def kostenvergleich(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Gesamtkosten E-Auto gegen Verbrenner über die Haltedauer."""
    fahrzeug = dd.FAHRZEUG_KLASSEN[profil.fahrzeugklasse]
    referenz = dd.VERBRENNER_REFERENZ[profil.fahrzeugklasse]
    jahre = profil.haltedauer_jahre
    jahres_km = profil.jahresfahrleistung_km()
    r = reichweite(profil)

    # --- Elektro ---
    verbrauch_kwh_100 = r["verbrauch_sommer"] * 1.15
    strompreis = mischpreis_eur_kwh(profil)
    energie_e = jahres_km * verbrauch_kwh_100 / 100.0 * strompreis
    wertverlust_e = fahrzeug["preis_eur"] * (1 - fahrzeug["restwert_4j"]) * (jahre / 4)
    wallbox = (
        dd.WALLBOX_INVEST_EUR
        if profil.lademoeglichkeit == "wallbox_zuhause" and profil.stellplatz_vorhanden
        else 0.0
    )

    # --- Verbrenner ---
    verbrauch_l_100 = profil.aktueller_verbrauch_l_100km or referenz["verbrauch_l_100km"]
    kraftstoffpreis = (
        dd.BENZIN_EUR_L if referenz["kraftstoff"] == "benzin" else dd.DIESEL_EUR_L
    )
    energie_v = jahres_km * verbrauch_l_100 / 100.0 * kraftstoffpreis
    wertverlust_v = referenz["preis_eur"] * 0.52 * (jahre / 4)

    def summe(posten: list[tuple[str, float]]) -> float:
        return sum(wert for _, wert in posten)

    posten_e: list[tuple[str, float]] = [
        ("Wertverlust", round(wertverlust_e)),
        ("Energie", round(energie_e * jahre)),
        ("Wartung", round(dd.WARTUNG_EUR_A_FAHRZEUG["elektro"] * jahre)),
        ("Versicherung", round(dd.VERSICHERUNG_EUR_A["elektro"] * jahre)),
        ("Kfz-Steuer", round(dd.KFZ_STEUER_EUR_A["elektro"] * jahre)),
        ("Wallbox", round(wallbox)),
        ("THG-Quote", -round(dd.THG_QUOTE_EUR_A * jahre)),
    ]
    posten_v: list[tuple[str, float]] = [
        ("Wertverlust", round(wertverlust_v)),
        ("Energie", round(energie_v * jahre)),
        ("Wartung", round(dd.WARTUNG_EUR_A_FAHRZEUG["verbrenner"] * jahre)),
        ("Versicherung", round(dd.VERSICHERUNG_EUR_A["verbrenner"] * jahre)),
        ("Kfz-Steuer", round(dd.KFZ_STEUER_EUR_A["verbrenner"] * jahre)),
        ("Wallbox", 0.0),
        ("THG-Quote", 0.0),
    ]

    gesamt_e = summe(posten_e)
    gesamt_v = summe(posten_v)

    return {
        "haltedauer_jahre": jahre,
        "jahres_km": jahres_km,
        "kategorien": [label for label, _ in posten_e],
        "serien": [
            {"label": "Elektro", "werte": [wert for _, wert in posten_e]},
            {"label": "Verbrenner", "werte": [wert for _, wert in posten_v]},
        ],
        "gesamt_elektro_eur": round(gesamt_e),
        "gesamt_verbrenner_eur": round(gesamt_v),
        "differenz_eur": round(gesamt_v - gesamt_e),
        "differenz_eur_monat": round((gesamt_v - gesamt_e) / (jahre * 12)),
        "energie_elektro_eur_100km": round(
            verbrauch_kwh_100 / 100.0 * strompreis * 100, 2
        ),
        "energie_verbrenner_eur_100km": round(
            verbrauch_l_100 / 100.0 * kraftstoffpreis * 100, 2
        ),
        "co2_ersparnis_kg_a": round(
            (
                jahres_km * verbrauch_l_100 / 100.0 * dd.CO2_BENZIN_G_L
                - jahres_km
                * verbrauch_kwh_100
                / 100.0
                * dd.CO2_STROMMIX_G_KWH
            )
            / 1000.0
        ),
    }


def fahrzeugvorschlaege(profil: Mobilitaetsprofil, *, anzahl: int = 3) -> list[dict[str, Any]]:
    """Rangfolge passender Fahrzeugklassen mit offen gezeigten Trade-offs."""
    vorschlaege: list[dict[str, Any]] = []

    for klasse, daten in dd.FAHRZEUG_KLASSEN.items():
        kandidat = Mobilitaetsprofil(**{**profil.__dict__, "fahrzeugklasse": klasse})
        r = reichweite(kandidat)
        ls = langstrecke(kandidat)
        kosten = kostenvergleich(kandidat)

        score = 60.0
        pro: list[str] = []
        contra: list[str] = []

        puffer = r["puffer_faktor_winter"]
        if puffer >= 3:
            score += 20
            pro.append(
                f"{r['reichweite_winter_km']} km Winterreichweite – "
                f"{puffer:.0f}× Ihr täglicher Bedarf"
            )
        elif puffer >= 1.5:
            score += 10
            pro.append(f"{r['reichweite_winter_km']} km im Winter reichen für Ihre Pendelstrecke")
        else:
            score -= 20
            contra.append("Im Winter müssten Sie fast täglich laden")

        if ls["ladestopps"] <= 1:
            score += 12
            pro.append(
                f"Ihre {int(profil.langstrecke_km)}-km-Strecke mit "
                f"{ls['ladestopps']} Ladestopp"
            )
        else:
            score -= 6
            contra.append(f"{ls['ladestopps']} Ladestopps auf der Langstrecke")

        if profil.budget_eur_monat:
            monatlich = daten["leasing_eur_monat"]
            if monatlich <= profil.budget_eur_monat:
                score += 12
                pro.append(f"Liegt mit {monatlich:.0f} €/Monat in Ihrem Budget")
            else:
                score -= 18
                contra.append(
                    f"{monatlich:.0f} €/Monat liegen über Ihrem Budget von "
                    f"{profil.budget_eur_monat:.0f} €"
                )

        if kosten["differenz_eur"] > 0:
            pro.append(
                f"Über {profil.haltedauer_jahre} Jahre rund "
                f"{kosten['differenz_eur']:,.0f} € günstiger als ein vergleichbarer Verbrenner".replace(
                    ",", "."
                )
            )
        else:
            contra.append("Teurer als ein vergleichbarer Verbrenner")

        if klasse == profil.fahrzeugklasse:
            score += 8
            pro.append("Entspricht Ihrer gewünschten Fahrzeugklasse")

        vorschlaege.append(
            {
                "id": klasse,
                "label": daten["label"],
                "batterie_kwh": daten["batterie_kwh"],
                "reichweite_winter_km": r["reichweite_winter_km"],
                "ladestopps_langstrecke": ls["ladestopps"],
                "leasing_eur_monat": daten["leasing_eur_monat"],
                "preis_eur": daten["preis_eur"],
                "score": max(5, min(100, round(score))),
                "pro": pro,
                "contra": contra or ["Keine relevanten Einschränkungen für Ihr Profil"],
            }
        )

    vorschlaege.sort(key=lambda v: v["score"], reverse=True)
    return vorschlaege[:anzahl]


def annahmen(profil: Mobilitaetsprofil) -> list[str]:
    """Die Annahmenliste, die unter jeder Zahl im UI steht.

    Sobald der Kunde selbst eine Ladequote gesetzt hat, steht seine hier — sonst
    würde die sichtbare Annahme der gezeigten Zahl widersprechen.
    """
    preis = mischpreis_eur_kwh(profil)
    herkunft = (
        f"{profil.anteil_zuhause_laden:.0f} % zu Hause, von Ihnen gesetzt"
        if profil.anteil_zuhause_laden is not None
        else f"Mix für „{profil.lademoeglichkeit}“"
    )
    return [
        f"Jahresfahrleistung {profil.jahresfahrleistung_km():,.0f} km".replace(",", "."),
        f"Mischladepreis {preis:.2f} €/kWh ({herkunft})",
        f"Winter-Mehrverbrauch {dd.WINTER_MEHRVERBRAUCH:.0%}, "
        f"Autobahn-Mehrverbrauch {dd.LANGSTRECKE_MEHRVERBRAUCH:.0%}",
        f"Ladefenster 10–80 % SoC, Haltedauer {profil.haltedauer_jahre} Jahre",
        f"Kraftstoff Benzin {dd.BENZIN_EUR_L:.2f} €/l, Diesel {dd.DIESEL_EUR_L:.2f} €/l",
        dd.DISCLAIMER,
    ]


# ---------------------------------------------------------------------------
# Stellschrauben
# ---------------------------------------------------------------------------


def stellschrauben(profil: Mobilitaetsprofil) -> dict[str, Any]:
    """Die Koeffizienten hinter „Was wäre wenn?“.

    Zwei Zahlen entscheiden über die Energiekosten eines E-Autos, und beide sind
    im Erstgespräch grobe Schätzungen: die tatsächliche Tagesstrecke und der
    Anteil, den man zu Hause lädt. Statt sie festzuschreiben, gibt diese
    Funktion die Rechnung als Faktoren heraus, mit denen der Browser live
    nachrechnet, während der Kunde am Regler zieht:

        Jahres-km     = km_je_tag × tage_pro_jahr + km_konstante
        Strompreis_ct = preis_unterwegs_ct + Anteil_zuhause × delta_je_prozent
        Strom  je Jahr = Jahres-km × Strompreis_ct × strom_eur_je_km_je_ct
        Sprit  je Jahr = Jahres-km × kraftstoff_eur_je_km

    Es ist dieselbe Arithmetik wie in :func:`kostenvergleich`, nur nach den zwei
    unsicheren Größen aufgelöst.
    """
    r = reichweite(profil)
    referenz = dd.VERBRENNER_REFERENZ[profil.fahrzeugklasse]

    verbrauch_kwh_100 = r["verbrauch_sommer"] * 1.15
    verbrauch_l_100 = profil.aktueller_verbrauch_l_100km or referenz["verbrauch_l_100km"]
    kraftstoffpreis = (
        dd.BENZIN_EUR_L if referenz["kraftstoff"] == "benzin" else dd.DIESEL_EUR_L
    )

    preis_zuhause_ct = dd.LADEN_ZUHAUSE_EUR_KWH * 100
    preis_unterwegs_ct = ladepreis_eur_kwh("nur_oeffentlich") * 100
    anteil_zuhause = (
        profil.anteil_zuhause_laden
        if profil.anteil_zuhause_laden is not None
        else _LADEMIX[profil.lademoeglichkeit]["zuhause"] * 100
    )

    # Alles außer der Tagesstrecke bleibt beim Ziehen konstant: Langstrecken
    # und Freizeitkilometer, genau wie in `jahresfahrleistung_km`.
    km_konstante = profil.langstrecke_km * profil.langstrecken_pro_monat * 12 + 2500.0

    return {
        "fahrzeug": r["fahrzeug"],
        "kraftstoff": referenz["kraftstoff"],
        # Startwerte der Regler.
        "taeglich_km": round(profil.taeglich_km),
        "anteil_zuhause": round(anteil_zuhause),
        "taeglich_km_min": 5,
        "taeglich_km_max": max(150, int(profil.taeglich_km * 2)),
        # Fahrleistung.
        "tage_pro_jahr": profil.pendeltage_pro_woche * 46,
        "km_konstante": round(km_konstante),
        # Ladepreis als Gerade über den Anteil, den man zu Hause lädt.
        "preis_zuhause_ct": round(preis_zuhause_ct, 1),
        "preis_unterwegs_ct": round(preis_unterwegs_ct, 1),
        "delta_je_prozent": round((preis_zuhause_ct - preis_unterwegs_ct) / 100.0, 4),
        # Ein Kilometer bei einem Cent je Kilowattstunde kostet so viel Euro.
        "strom_eur_je_km_je_ct": round(verbrauch_kwh_100 / 10000.0, 6),
        "kraftstoff_eur_je_km": round(verbrauch_l_100 / 100.0 * kraftstoffpreis, 4),
        "verbrauch_kwh_100km": round(verbrauch_kwh_100, 1),
        "verbrauch_l_100km": round(verbrauch_l_100, 1),
    }
