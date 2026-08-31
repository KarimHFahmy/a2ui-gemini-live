"""Energieberatung: deterministische Berechnungen für die Demo.

The model never invents numbers. It extracts the client's situation from the
conversation and passes it here; every figure the client sees is computed by
this module from :mod:`demo_data`, so the same input always produces the same
advice and the assumptions can be shown alongside the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from . import demo_data as dd
from ..format_de import de

Heizung = Literal["gas", "oel", "fernwaerme", "nachtspeicher", "waermepumpe"]
Sanierungsstand = Literal["unsaniert", "teilsaniert", "saniert"]
Waermesystem = Literal[
    "fussbodenheizung",
    "flaechenheizkoerper_gross",
    "heizkoerper_standard",
    "heizkoerper_klein_alt",
]


@dataclass
class Gebaeudeprofil:
    """Was der Agent aus dem Gespräch verstanden hat."""

    baujahr: int = 1985
    wohnflaeche_qm: float = 150.0
    heizung: Heizung = "gas"
    sanierungsstand: Sanierungsstand = "teilsaniert"
    waermesystem: Waermesystem = "heizkoerper_standard"
    personen: int = 4
    verbrauch_kwh_a: float | None = None
    prioritaeten: list[str] = field(default_factory=list)
    bedenken: list[str] = field(default_factory=list)
    pv_vorhanden: bool = False

    #: Preisannahmen, die der Kunde selbst gesetzt hat, in Cent je Kilowattstunde.
    #: Solange sie leer sind, gelten die Demo-Werte aus :mod:`demo_data`.
    preis_alt_ct: float | None = None
    preis_strom_ct: float | None = None

    def baualtersklasse(self) -> str:
        if self.baujahr < 1979:
            return "vor_1979"
        if self.baujahr < 1995:
            return "1979_1994"
        if self.baujahr < 2010:
            return "1995_2009"
        return "ab_2010"


@dataclass
class Szenario:
    """Ein Sanierungspfad mit allen Kennzahlen für die Beratungsansicht."""

    id: str
    label: str
    beschreibung: str
    investition_eur: float
    foerderung_eur: float
    energiekosten_eur_a: float
    wartung_eur_a: float
    co2_kg_a: float
    komfort_score: int  # 1..5
    aufwand_score: int  # 1..5, 5 = viel Aufwand
    massnahmen: list[str] = field(default_factory=list)

    @property
    def eigenanteil_eur(self) -> float:
        return max(0.0, self.investition_eur - self.foerderung_eur)

    @property
    def betriebskosten_eur_a(self) -> float:
        return self.energiekosten_eur_a + self.wartung_eur_a


# ---------------------------------------------------------------------------
# Wärmebedarf und Wärmepumpen-Eignung
# ---------------------------------------------------------------------------


def waermebedarf_kwh_a(profil: Gebaeudeprofil) -> float:
    """Jährlicher Wärmebedarf.

    Ein gemessener Verbrauch schlägt die Schätzung — er ist die belastbarere
    Grundlage und der Kunde erkennt seine eigene Zahl wieder.
    """
    if profil.verbrauch_kwh_a:
        return float(profil.verbrauch_kwh_a)
    spezifisch = dd.WAERMEBEDARF_KWH_QM[profil.baualtersklasse()][profil.sanierungsstand]
    warmwasser = profil.personen * 800.0
    return round(spezifisch * profil.wohnflaeche_qm + warmwasser, 0)


def vorlauftemperatur(profil: Gebaeudeprofil) -> int:
    return dd.VORLAUF_NACH_SYSTEM[profil.waermesystem]


def jaz(vorlauf: int) -> float:
    """Jahresarbeitszahl, linear zwischen den Stützstellen interpoliert."""
    stuetzstellen = sorted(dd.JAZ_NACH_VORLAUF.items())
    if vorlauf <= stuetzstellen[0][0]:
        return stuetzstellen[0][1]
    if vorlauf >= stuetzstellen[-1][0]:
        return stuetzstellen[-1][1]
    for (t0, j0), (t1, j1) in zip(stuetzstellen, stuetzstellen[1:]):
        if t0 <= vorlauf <= t1:
            anteil = (vorlauf - t0) / (t1 - t0)
            return round(j0 + anteil * (j1 - j0), 2)
    return stuetzstellen[-1][1]


def eignung(profil: Gebaeudeprofil) -> dict[str, Any]:
    """Beantwortet die Kernsorge: "Reicht eine Wärmepumpe im Winter?"

    Returns the flow temperature, the resulting seasonal performance factor,
    a 0-100 suitability score and the concrete measures that would raise it.
    """
    vorlauf = vorlauftemperatur(profil)
    arbeitszahl = jaz(vorlauf)
    bedarf = waermebedarf_kwh_a(profil)
    spezifisch = bedarf / max(profil.wohnflaeche_qm, 1.0)

    score = 100.0
    hinweise: list[str] = []
    massnahmen: list[str] = []

    if vorlauf >= 65:
        score -= 35
        hinweise.append(
            "Die vorhandenen Heizkörper brauchen im Auslegungsfall eine hohe "
            "Vorlauftemperatur. Das drückt die Effizienz spürbar."
        )
        massnahmen.append("Austausch einzelner Heizkörper gegen Niedertemperatur-Modelle")
    elif vorlauf >= 55:
        score -= 15
        hinweise.append(
            "Mit Standard-Heizkörpern läuft die Wärmepumpe gut, aber nicht optimal."
        )
        massnahmen.append("Hydraulischer Abgleich und Heizkurve absenken")
    else:
        hinweise.append(
            "Das Wärmeverteilsystem passt sehr gut zu einer Wärmepumpe."
        )

    if spezifisch > 180:
        score -= 25
        hinweise.append(
            "Der spezifische Wärmebedarf ist hoch — die Gebäudehülle ist der "
            "größere Hebel als die Heiztechnik."
        )
        massnahmen.append("Dachdämmung oder Fenstertausch vorziehen")
    elif spezifisch > 130:
        score -= 10
        massnahmen.append("Dachbodendämmung als günstige Einstiegsmaßnahme prüfen")

    if profil.sanierungsstand == "unsaniert":
        score -= 10

    score = max(10.0, min(100.0, score))

    if score >= 75:
        urteil = "gut geeignet"
    elif score >= 50:
        urteil = "geeignet mit Vorbereitung"
    else:
        urteil = "erst nach Vorbereitung sinnvoll"

    # Auslegungsleistung: Norm-Heizlast grob aus dem Jahresbedarf.
    heizlast_kw = round(bedarf / 1800.0, 1)

    return {
        "vorlauftemperatur_c": vorlauf,
        "jaz": arbeitszahl,
        "waermebedarf_kwh_a": round(bedarf),
        "spezifisch_kwh_qm_a": round(spezifisch),
        "heizlast_kw": heizlast_kw,
        "score": round(score),
        "urteil": urteil,
        "hinweise": hinweise,
        "massnahmen": massnahmen or ["Keine Vorbereitung nötig"],
        "strombedarf_kwh_a": round(bedarf / arbeitszahl),
    }


# ---------------------------------------------------------------------------
# Förderung
# ---------------------------------------------------------------------------


def foerderung(
    investition_eur: float,
    *,
    klimageschwindigkeitsbonus: bool = True,
    einkommensbonus: bool = False,
    effizienzbonus: bool = False,
) -> dict[str, Any]:
    """Bildet die BEG-Heizungsförderung als Demo-Logik ab."""
    f = dd.FOERDERUNG
    bausteine: list[dict[str, Any]] = [
        {"label": "Grundförderung", "satz": f["grundfoerderung"]}
    ]
    satz = f["grundfoerderung"]

    if klimageschwindigkeitsbonus:
        satz += f["klimageschwindigkeitsbonus"]
        bausteine.append(
            {
                "label": "Klimageschwindigkeits-Bonus",
                "satz": f["klimageschwindigkeitsbonus"],
            }
        )
    if einkommensbonus:
        satz += f["einkommensbonus"]
        bausteine.append({"label": "Einkommens-Bonus", "satz": f["einkommensbonus"]})
    if effizienzbonus:
        satz += f["effizienzbonus"]
        bausteine.append({"label": "Effizienz-Bonus", "satz": f["effizienzbonus"]})

    effektiver_satz = min(satz, f["max_satz"])
    foerderfaehig = min(investition_eur, f["hoechstkosten_efh_eur"])
    betrag = round(foerderfaehig * effektiver_satz, -1)

    return {
        "satz": round(effektiver_satz, 2),
        "satz_ungedeckelt": round(satz, 2),
        "gedeckelt": satz > f["max_satz"],
        "foerderfaehige_kosten_eur": round(foerderfaehig),
        "betrag_eur": betrag,
        "bausteine": bausteine,
        "hinweis": f["hinweis"],
    }


# ---------------------------------------------------------------------------
# Szenarien
# ---------------------------------------------------------------------------


def _bestand_energietraeger(profil: Gebaeudeprofil) -> tuple[str, float, float]:
    """Bezeichnung, Preis je Kilowattstunde und Nutzungsgrad der Bestandsheizung.

    Getrennt vom Kostenaufruf, weil die beiden Zahlen zweimal gebraucht werden:
    einmal für die Kosten und einmal als Stellschraube, an der der Kunde selbst
    drehen kann.
    """
    traeger, preis, nutzungsgrad = {
        "gas": ("Erdgas", dd.GAS_EUR_KWH, 0.88),
        "oel": ("Heizöl", dd.HEIZOEL_EUR_L / dd.HEIZOEL_KWH_PRO_L, 0.85),
        "fernwaerme": ("Fernwärme", dd.FERNWAERME_EUR_KWH, 1.0),
        "nachtspeicher": ("Strom", dd.STROM_HAUSHALT_EUR_KWH, 1.0),
        "waermepumpe": ("Strom", dd.STROM_WAERMEPUMPE_EUR_KWH, 3.5),
    }[profil.heizung]
    if profil.preis_alt_ct is not None:
        preis = profil.preis_alt_ct / 100.0
    return traeger, preis, nutzungsgrad


def strompreis_eur_kwh(profil: Gebaeudeprofil) -> float:
    """Der Wärmepumpen-Strompreis — der des Kunden, sonst der Demo-Wert."""
    if profil.preis_strom_ct is not None:
        return profil.preis_strom_ct / 100.0
    return dd.STROM_WAERMEPUMPE_EUR_KWH


def _energiekosten_bestand(profil: Gebaeudeprofil, bedarf: float) -> float:
    _, preis, nutzungsgrad = _bestand_energietraeger(profil)
    return bedarf / nutzungsgrad * preis


def _co2_bestand(profil: Gebaeudeprofil, bedarf: float) -> float:
    faktor = {
        "gas": dd.CO2_ERDGAS_G_KWH / 0.88,
        "oel": dd.CO2_HEIZOEL_G_KWH / 0.85,
        "fernwaerme": dd.CO2_FERNWAERME_G_KWH,
        "nachtspeicher": dd.CO2_STROMMIX_G_KWH,
        "waermepumpe": dd.CO2_STROMMIX_G_KWH / 3.5,
    }[profil.heizung]
    return bedarf * faktor / 1000.0


def _wartung_bestand(profil: Gebaeudeprofil) -> float:
    return {
        "gas": dd.WARTUNG_EUR_A["gasheizung"],
        "oel": dd.WARTUNG_EUR_A["oelheizung"],
        "fernwaerme": dd.WARTUNG_EUR_A["fernwaerme"],
        "nachtspeicher": 60.0,
        "waermepumpe": dd.WARTUNG_EUR_A["waermepumpe"],
    }[profil.heizung]


def szenarien(
    profil: Gebaeudeprofil,
    *,
    einkommensbonus: bool = False,
) -> list[Szenario]:
    """Baut die Vergleichsszenarien für das konkrete Gebäude."""
    bedarf = waermebedarf_kwh_a(profil)
    check = eignung(profil)
    arbeitszahl = check["jaz"]
    strompreis = strompreis_eur_kwh(profil)

    ergebnis: list[Szenario] = [
        Szenario(
            id="bestand",
            label="Weiter wie bisher",
            beschreibung=(
                "Die vorhandene Heizung bleibt. Keine Investition, aber steigende "
                "Energiekosten und CO₂-Bepreisung."
            ),
            investition_eur=0.0,
            foerderung_eur=0.0,
            energiekosten_eur_a=round(_energiekosten_bestand(profil, bedarf)),
            wartung_eur_a=_wartung_bestand(profil),
            co2_kg_a=round(_co2_bestand(profil, bedarf)),
            komfort_score=3,
            aufwand_score=1,
            massnahmen=["Keine"],
        )
    ]

    # Wärmepumpe, ggf. mit vorbereitenden Maßnahmen am Verteilsystem.
    braucht_heizkoerper = check["vorlauftemperatur_c"] >= 65
    invest_wp = dd.INVEST_EUR["waermepumpe_luft"] + dd.INVEST_EUR["hydraulischer_abgleich"]
    massnahmen_wp = ["Luft/Wasser-Wärmepumpe", "Hydraulischer Abgleich"]
    if braucht_heizkoerper:
        invest_wp += dd.INVEST_EUR["heizkoerper_tausch"]
        massnahmen_wp.append("Tausch kritischer Heizkörper")

    foerd_wp = foerderung(invest_wp, einkommensbonus=einkommensbonus)
    strom_wp = bedarf / arbeitszahl
    ergebnis.append(
        Szenario(
            id="waermepumpe",
            label="Wärmepumpe",
            beschreibung=(
                "Heiztechnik tauschen, Gebäudehülle unverändert lassen. "
                "Der schnellste Weg raus aus dem fossilen Brennstoff."
            ),
            investition_eur=invest_wp,
            foerderung_eur=foerd_wp["betrag_eur"],
            energiekosten_eur_a=round(strom_wp * strompreis),
            wartung_eur_a=dd.WARTUNG_EUR_A["waermepumpe"],
            co2_kg_a=round(strom_wp * dd.CO2_STROMMIX_G_KWH / 1000.0),
            komfort_score=4,
            aufwand_score=3,
            massnahmen=massnahmen_wp,
        )
    )

    # Wärmepumpe plus Hülle: Bedarf sinkt, dadurch auch die nötige Vorlauftemperatur.
    huelle_faktor = 0.72 if profil.sanierungsstand != "saniert" else 0.88
    bedarf_huelle = bedarf * huelle_faktor
    jaz_huelle = jaz(max(35, check["vorlauftemperatur_c"] - 10))
    invest_huelle = (
        dd.INVEST_EUR["waermepumpe_luft"]
        + dd.INVEST_EUR["hydraulischer_abgleich"]
        + dd.INVEST_EUR["daemmung_dach"]
    )
    # Nur der Heizungsanteil ist über die Heizungsförderung förderfähig.
    foerd_huelle = foerderung(
        dd.INVEST_EUR["waermepumpe_luft"] + dd.INVEST_EUR["hydraulischer_abgleich"],
        einkommensbonus=einkommensbonus,
    )
    strom_huelle = bedarf_huelle / jaz_huelle
    ergebnis.append(
        Szenario(
            id="waermepumpe_huelle",
            label="Wärmepumpe + Dachdämmung",
            beschreibung=(
                "Erst den Bedarf senken, dann die Wärmepumpe kleiner auslegen. "
                "Höhere Investition, dafür dauerhaft niedrigste Betriebskosten."
            ),
            investition_eur=invest_huelle,
            foerderung_eur=foerd_huelle["betrag_eur"],
            energiekosten_eur_a=round(strom_huelle * strompreis),
            wartung_eur_a=dd.WARTUNG_EUR_A["waermepumpe"],
            co2_kg_a=round(strom_huelle * dd.CO2_STROMMIX_G_KWH / 1000.0),
            komfort_score=5,
            aufwand_score=5,
            massnahmen=[
                "Luft/Wasser-Wärmepumpe",
                "Dachdämmung",
                "Hydraulischer Abgleich",
            ],
        )
    )

    # Wärmepumpe plus PV und Speicher: ein Teil des Wärmestroms kommt vom Dach.
    if not profil.pv_vorhanden:
        invest_pv = invest_wp + dd.INVEST_EUR["pv_10kwp"] + dd.INVEST_EUR["speicher_8kwh"]
        foerd_pv = foerderung(invest_wp, einkommensbonus=einkommensbonus)
        eigenverbrauchsanteil = 0.35
        mischpreis = (
            eigenverbrauchsanteil * dd.PV_GESTEHUNG_EUR_KWH
            + (1 - eigenverbrauchsanteil) * strompreis
        )
        haushaltsstrom_ersparnis = 1400.0 * (
            dd.STROM_HAUSHALT_EUR_KWH - dd.PV_GESTEHUNG_EUR_KWH
        )
        ergebnis.append(
            Szenario(
                id="waermepumpe_pv",
                label="Wärmepumpe + PV & Speicher",
                beschreibung=(
                    "Wärme und Strom zusammen denken. Ein Teil des Wärmestroms "
                    "kommt vom eigenen Dach, das entkoppelt von Strompreisen."
                ),
                investition_eur=invest_pv,
                foerderung_eur=foerd_pv["betrag_eur"],
                energiekosten_eur_a=round(
                    strom_wp * mischpreis - haushaltsstrom_ersparnis
                ),
                wartung_eur_a=dd.WARTUNG_EUR_A["waermepumpe"] + 120.0,
                co2_kg_a=round(
                    strom_wp
                    * (1 - eigenverbrauchsanteil)
                    * dd.CO2_STROMMIX_G_KWH
                    / 1000.0
                ),
                komfort_score=5,
                aufwand_score=4,
                massnahmen=[
                    "Luft/Wasser-Wärmepumpe",
                    "PV-Anlage 10 kWp",
                    "Batteriespeicher 8 kWh",
                ],
            )
        )

    return ergebnis


def kostenverlauf(
    szenarien_liste: list[Szenario], *, jahre: int = 20
) -> dict[str, Any]:
    """Kumulierte Gesamtkosten über die Betrachtungsdauer.

    Investition abzüglich Förderung plus fortgeschriebene Betriebskosten. Das
    ist die Kurve, an der ein Kunde erkennt, wann sich eine Entscheidung dreht.
    """
    kategorien = [f"Jahr {j}" for j in range(0, jahre + 1, 5)]
    serien: list[dict[str, Any]] = []

    for szenario in szenarien_liste:
        werte: list[float] = []
        for jahr in range(0, jahre + 1, 5):
            kumuliert = szenario.eigenanteil_eur
            for j in range(jahr):
                steigerung = (
                    (1 + dd.PREISPFAD_GAS_P_A) ** j
                    if szenario.id == "bestand" and _ist_fossil(szenario)
                    else (1 + dd.PREISPFAD_STROM_P_A) ** j
                )
                kumuliert += szenario.betriebskosten_eur_a * steigerung
            werte.append(round(kumuliert, -1))
        serien.append({"label": szenario.label, "werte": werte, "id": szenario.id})

    return {"kategorien": kategorien, "serien": serien, "einheit": "€"}


def _ist_fossil(szenario: Szenario) -> bool:
    return szenario.id == "bestand"


def amortisation(basis: Szenario, alternative: Szenario) -> dict[str, Any]:
    """Ab wann ist die Alternative günstiger als der Bestand?"""
    mehrinvest = alternative.eigenanteil_eur - basis.eigenanteil_eur
    kumuliert_basis = 0.0
    kumuliert_alt = mehrinvest

    for jahr in range(1, 41):
        kumuliert_basis += basis.betriebskosten_eur_a * (
            (1 + dd.PREISPFAD_GAS_P_A) ** (jahr - 1)
        )
        kumuliert_alt += alternative.betriebskosten_eur_a * (
            (1 + dd.PREISPFAD_STROM_P_A) ** (jahr - 1)
        )
        if kumuliert_alt <= kumuliert_basis:
            return {"jahre": jahr, "erreichbar": True}

    return {"jahre": None, "erreichbar": False}


def annahmen(profil: Gebaeudeprofil) -> list[str]:
    """Die Annahmenliste, die unter jeder Zahl im UI steht.

    Sobald der Kunde eigene Preise gesetzt hat, stehen seine hier — sonst
    würde die sichtbare Annahme der gezeigten Zahl widersprechen.
    """
    traeger, preis_alt, _ = _bestand_energietraeger(profil)
    eigene = profil.preis_alt_ct is not None or profil.preis_strom_ct is not None
    return [
        f"Wärmebedarf {de(waermebedarf_kwh_a(profil))} kWh/a",
        f"Strompreis Wärmepumpe {de(strompreis_eur_kwh(profil), decimals=2)} €/kWh, "
        f"{traeger}preis {de(preis_alt, decimals=3)} €/kWh"
        + (" (Ihre eigenen Annahmen)" if eigene else ""),
        f"Preissteigerung Strom {dd.PREISPFAD_STROM_P_A:.0%} p. a., "
        f"fossil {dd.PREISPFAD_GAS_P_A:.1%} p. a.",
        f"Jahresarbeitszahl {de(jaz(vorlauftemperatur(profil)), decimals=1)} bei "
        f"{vorlauftemperatur(profil)} °C Vorlauf",
        "Betrachtungsdauer 20 Jahre, Förderung nach BEG-Demo-Logik",
        dd.DISCLAIMER,
    ]


# ---------------------------------------------------------------------------
# Stellschrauben
# ---------------------------------------------------------------------------


def stellschrauben(
    profil: Gebaeudeprofil,
    bestand: Szenario,
    fokus: Szenario,
) -> dict[str, Any]:
    """Die Koeffizienten hinter „Was wäre wenn?“.

    Die Wirtschaftlichkeit einer Wärmepumpe hängt an genau zwei Zahlen, die
    niemand kennt: dem künftigen Strompreis und dem künftigen Preis des heutigen
    Brennstoffs. Statt eine Annahme zu setzen und zu verteidigen, gibt diese
    Funktion die Rechnung selbst heraus — als Faktoren, mit denen der Browser
    live nachrechnet, während der Kunde am Regler zieht:

        Heizkosten heute  = eur_je_ct_alt × Preis_alt_ct + wartung_alt
        Heizkosten danach = eur_je_ct_neu × Preis_strom_ct + wartung_neu

    Beide Zeilen sind exakt dieselbe Arithmetik, mit der :func:`szenarien` die
    Ausgangswerte gerechnet hat. Der Regler kann deshalb keine Zahl erzeugen,
    die der Backend nicht auch geliefert hätte.
    """
    bedarf = waermebedarf_kwh_a(profil)
    traeger, preis_alt, nutzungsgrad = _bestand_energietraeger(profil)

    # Der Wärmestrom des Zielszenarios, zurückgerechnet aus seinen Kosten:
    # so bleibt ein PV-Eigenverbrauchsanteil enthalten, ohne ihn hier erneut
    # modellieren zu müssen.
    kwh_alt = bedarf / nutzungsgrad
    kwh_neu = fokus.energiekosten_eur_a / strompreis_eur_kwh(profil)

    return {
        "traeger": traeger,
        "fokus_label": fokus.label,
        # Startwerte der Regler, in ganzen Cent je Kilowattstunde: der
        # A2UI-Slider springt in Einerschritten, also müssen die Preise, mit
        # denen die übrige Beratung rechnet, auf dem Raster liegen.
        "preis_alt_ct": round(preis_alt * 100),
        "preis_strom_ct": round(strompreis_eur_kwh(profil) * 100),
        # Reglergrenzen, bewusst weit genug für ein ehrliches „rechnet sich nicht“.
        "preis_alt_min_ct": max(2, int(preis_alt * 100 * 0.5)),
        "preis_alt_max_ct": int(preis_alt * 100 * 2.5) + 1,
        "preis_strom_min_ct": 15,
        "preis_strom_max_ct": 55,
        # Ein Cent Preisänderung kostet so viele Euro im Jahr.
        "eur_je_ct_alt": round(kwh_alt / 100.0, 3),
        "eur_je_ct_neu": round(kwh_neu / 100.0, 3),
        "wartung_alt": bestand.wartung_eur_a,
        "wartung_neu": fokus.wartung_eur_a,
        "eigenanteil_eur": round(fokus.eigenanteil_eur),
        "bedarf_kwh_a": round(bedarf),
        "kwh_alt": round(kwh_alt),
        "kwh_neu": round(kwh_neu),
    }
