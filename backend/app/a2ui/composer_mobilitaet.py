"""Composes the Autoberater surfaces from domain results.

The order of the surfaces is the argument: first "does it fit your week",
then "where do you charge", then "which car", then "what does it cost".
Charging comes before the vehicle because it is the larger cost lever.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import mobilitaet as calc
from . import components as c
from .surface import Surface

_LADE_LABEL = {
    "wallbox_zuhause": "Wallbox zu Hause",
    "steckdose_zuhause": "Haushaltssteckdose",
    "arbeitsplatz": "Laden beim Arbeitgeber",
    "nur_oeffentlich": "Nur öffentlich",
}


# ---------------------------------------------------------------------------
# Surface: Verstandenes Profil
# ---------------------------------------------------------------------------


def profil_surface(profil: calc.Mobilitaetsprofil, offene_punkte: list[str]) -> Surface:
    """"Zusammenfassung des Verstandenen" for the mobility journey."""
    fakten = [
        {
            "label": "Täglich",
            "wert": f"{profil.taeglich_km:.0f} km an {profil.pendeltage_pro_woche} Tagen",
        },
        {
            "label": "Langstrecke",
            "wert": (
                f"{profil.langstrecken_pro_monat}× im Monat, rund "
                f"{profil.langstrecke_km:.0f} km"
            ),
        },
        {"label": "Laden", "wert": _LADE_LABEL[profil.lademoeglichkeit]},
        {
            "label": "Im Jahr",
            "wert": f"rund {profil.jahresfahrleistung_km():,.0f} km".replace(",", "."),
            "geschaetzt": True,
        },
        {
            "label": "Fahrzeugwunsch",
            "wert": dd.FAHRZEUG_KLASSEN[profil.fahrzeugklasse]["label"],
        },
    ]
    if profil.budget_eur_monat:
        fakten.append(
            {"label": "Budget", "wert": f"bis {profil.budget_eur_monat:.0f} € im Monat"}
        )
    if profil.bedenken:
        fakten.append({"label": "Ihre Bedenken", "wert": ", ".join(profil.bedenken)})

    components = [
        c.column("root", ["kopf", "zusammenfassung"]),
        c.advisory_header(
            "kopf",
            eyebrow="Ihr Alltag",
            title="Das habe ich verstanden",
            subtitle="Korrigieren Sie mich jederzeit – ich rechne sofort neu.",
            icon="route",
        ),
        c.profile_summary(
            "zusammenfassung",
            title="Ihr Mobilitätsprofil",
            facts=c.bind("/fakten"),
            open_points=c.bind("/offen"),
            note="Geschätzte Werte sind gekennzeichnet und lassen sich im Gespräch korrigieren.",
        ),
    ]

    return Surface(
        surface_id="profil",
        title="Ihr Alltag",
        components=components,
        data={"fakten": fakten, "offen": offene_punkte},
    )


# ---------------------------------------------------------------------------
# Surface: Alltagstauglichkeit
# ---------------------------------------------------------------------------


def alltag_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """"Ist ein E-Auto praktikabel für mich?" answered with their own week."""
    r = calc.reichweite(profil)
    woche = calc.wochenprofil(profil)
    ls = calc.langstrecke(profil)

    puffer = r["puffer_faktor_winter"]
    if puffer >= 3:
        alltag_tone, alltag_metric = "positive", f"{puffer:.0f}×"
        alltag_body = (
            f"Ihre {profil.taeglich_km:.0f} km am Tag sind selbst im Winter kein Thema. "
            f"Sie laden etwa {_ladehaeufigkeit(profil, r)}."
        )
    elif puffer >= 1.5:
        alltag_tone, alltag_metric = "neutral", f"{puffer:.1f}×"
        alltag_body = (
            f"Ihre Tagesstrecke passt, im Winter bleibt ein solider Puffer. "
            f"Sie laden etwa {_ladehaeufigkeit(profil, r)}."
        )
    else:
        alltag_tone, alltag_metric = "caution", f"{puffer:.1f}×"
        alltag_body = (
            "Im Winter wird es knapp – Sie müssten nahezu täglich laden. "
            "Eine größere Batterie oder eine verlässliche Lademöglichkeit ist hier wichtig."
        )

    components = [
        c.column("root", ["kopf", "kennzahlen", "woche", "langstrecke_kopf", "langstrecke", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Alltagstauglichkeit",
            title="Ihre Woche mit einem E-Auto",
            subtitle=(
                "Nicht der Katalogwert zählt, sondern die Reichweite an einem "
                "kalten Januarmorgen."
            ),
            icon="route",
        ),
        c.row("kennzahlen", ["k_alltag", "k_winter", "k_autobahn"], align="stretch"),
        c.insight_card(
            "k_alltag",
            title="Puffer im Alltag",
            body=alltag_body,
            metric=alltag_metric,
            metric_label="Ihres Tagesbedarfs",
            tone=alltag_tone,
            icon="check",
            weight=1,
        ),
        c.insight_card(
            "k_winter",
            title="Reichweite im Winter",
            body=(
                f"Bei Kälte steigt der Verbrauch auf {r['verbrauch_winter']} kWh/100 km. "
                f"Im Sommer sind es {r['reichweite_sommer_km']} km."
            ),
            metric=f"{r['reichweite_winter_km']} km",
            metric_label=f"{r['fahrzeug']}, {r['batterie_kwh']:.0f} kWh",
            tone="neutral",
            icon="snow",
            weight=1,
        ),
        c.insight_card(
            "k_autobahn",
            title="Autobahn im Winter",
            body=(
                "Der ehrlichste Wert: kalt, bei Richtgeschwindigkeit. "
                "Danach planen sich Langstrecken zuverlässig."
            ),
            metric=f"{r['reichweite_autobahn_winter_km']} km",
            metric_label=f"{r['verbrauch_autobahn_winter']} kWh/100 km",
            tone="neutral",
            icon="highway",
            weight=1,
        ),
        c.metric_chart(
            "woche",
            title="Ihre typische Woche",
            subtitle=(
                "Die Linie ist die Winterreichweite. Solange die Balken darunter "
                "bleiben, kommen Sie ohne Zwischenladen aus."
            ),
            chart_type="bar",
            categories=c.bind("/tage"),
            series=c.bind("/woche"),
            unit="km",
            value_format="number",
        ),
        c.advisory_header(
            "langstrecke_kopf",
            eyebrow="Langstrecke",
            title=f"Ihre {profil.langstrecke_km:.0f}-km-Fahrt konkret",
            subtitle=(
                f"{ls['ladestopps']} Ladestopp(s), zusammen "
                f"{ls['mehrzeit_min']} Minuten mehr als mit einem Verbrenner."
                if ls["ladestopps"]
                else "Ohne Ladestopp erreichbar."
            ),
            icon="highway",
        ),
        c.timeline("langstrecke", steps=c.bind("/langstrecke")),
        c.assumption_note(
            "annahmen",
            title="Annahmen dieser Rechnung",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_MOBILITAET,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="alltag",
        title="Alltagstauglichkeit",
        components=components,
        data={
            "tage": woche["kategorien"],
            "woche": woche["serien"],
            "langstrecke": ls["schritte"],
            "annahmen": calc.annahmen(profil),
        },
    )


def _ladehaeufigkeit(profil: calc.Mobilitaetsprofil, r: dict[str, Any]) -> str:
    tage = r["reichweite_winter_km"] / max(profil.taeglich_km, 1.0)
    if tage >= 7:
        return "einmal pro Woche"
    if tage >= 3:
        return f"alle {int(tage)} Tage"
    return "alle zwei Tage"


# ---------------------------------------------------------------------------
# Surface: Ladelösungen
# ---------------------------------------------------------------------------


def laden_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Where you charge decides the economics — shown before the car choice."""
    lade = calc.ladeoptionen(profil)
    optionen = lade["optionen"]
    aktuell = next(o for o in optionen if o["id"] == lade["aktuell_id"])
    beste = next(o for o in optionen if o["id"] == lade["beste_id"])

    spalten = [{"id": o["id"], "label": o["label"]} for o in optionen]
    zeilen = [
        {
            "label": "Mischpreis",
            "werte": [f"{o['mischpreis_eur_kwh']:.2f} €/kWh".replace(".", ",") for o in optionen],
        },
        {
            "label": "Energiekosten pro Jahr",
            "werte": [f"{o['kosten_eur_a']:,.0f} €".replace(",", ".") for o in optionen],
            "hervorheben": True,
        },
        {
            "label": "Kosten je 100 km",
            "werte": [f"{o['kosten_eur_100km']:.2f} €".replace(".", ",") for o in optionen],
        },
        {
            "label": "Einmalige Investition",
            "werte": [
                "–" if o["investition_eur"] == 0 else f"{o['investition_eur']:,.0f} €".replace(",", ".")
                for o in optionen
            ],
        },
        {
            "label": "Für Sie verfügbar",
            "werte": ["ja" if o["verfuegbar"] else "nein" for o in optionen],
        },
    ]

    ersparnis = lade["ersparnis_beste_eur_a"]
    if ersparnis > 200:
        hebel_body = (
            f"Der Wechsel von „{aktuell['label']}“ zu „{beste['label']}“ spart Ihnen "
            f"rund {ersparnis:,.0f} € im Jahr – mehr als die meisten Fahrzeugentscheidungen ausmachen.".replace(
                ",", "."
            )
        )
        hebel_tone = "positive"
    else:
        hebel_body = (
            "Ihre Ladesituation ist bereits gut. Die Fahrzeugwahl ist bei Ihnen "
            "der größere Hebel."
        )
        hebel_tone = "neutral"

    components = [
        c.column("root", ["kopf", "hebel", "tabelle", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Laden",
            title="Wo Sie laden, entscheidet über die Kosten",
            subtitle=(
                "Zwischen der günstigsten und der teuersten Ladeart liegt bei "
                "Ihrer Fahrleistung ein Vielfaches der Fahrzeugunterschiede."
            ),
            icon="plug",
        ),
        c.insight_card(
            "hebel",
            title="Ihr größter Hebel",
            body=hebel_body,
            metric=(
                f"{ersparnis:,.0f} €".replace(",", ".") if ersparnis > 0 else "–"
            ),
            metric_label="Ersparnis pro Jahr",
            tone=hebel_tone,
            icon="plug",
        ),
        c.comparison_table(
            "tabelle",
            title="Ladeoptionen im Vergleich",
            columns=c.bind("/spalten"),
            rows=c.bind("/zeilen"),
            highlight=c.bind("/beste"),
        ),
        c.assumption_note(
            "annahmen",
            title="Annahmen dieses Vergleichs",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_MOBILITAET,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="laden",
        title="Ladelösungen",
        components=components,
        data={
            "spalten": spalten,
            "zeilen": zeilen,
            "beste": lade["beste_id"],
            "annahmen": calc.annahmen(profil)
            + [
                f"Jahresenergiebedarf rund {lade['jahres_kwh']:,.0f} kWh".replace(",", "."),
            ],
        },
    )


# ---------------------------------------------------------------------------
# Surface: Fahrzeugvorschläge
# ---------------------------------------------------------------------------


def fahrzeuge_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Ranked classes with the trade-offs shown, not hidden."""
    vorschlaege = calc.fahrzeugvorschlaege(profil)

    children = ["kopf"]
    components: list[dict[str, Any]] = []
    data: dict[str, Any] = {}

    for index, v in enumerate(vorschlaege):
        comp_id = f"vorschlag_{index}"
        children.append(comp_id)
        data[f"pro_{index}"] = v["pro"]
        data[f"contra_{index}"] = v["contra"]
        components.append(
            c.recommendation(
                comp_id,
                rank=index + 1,
                title=v["label"],
                summary=(
                    f"{v['batterie_kwh']:.0f} kWh Batterie · {v['reichweite_winter_km']} km "
                    f"im Winter · {v['ladestopps_langstrecke']} Ladestopp(s) auf Ihrer "
                    f"Langstrecke · ab {v['leasing_eur_monat']:.0f} € im Monat"
                ),
                fit_score=v["score"],
                fit_label="Passung zu Ihrem Profil",
                pros=c.bind(f"/pro_{index}"),
                cons=c.bind(f"/contra_{index}"),
            )
        )

    children.append("annahmen")
    components.insert(
        0,
        c.advisory_header(
            "kopf",
            eyebrow="Fahrzeugwahl",
            title="Diese Klassen passen zu Ihrem Alltag",
            subtitle=(
                "Sortiert nach Passung zu Ihrem Profil, nicht nach Reichweite "
                "oder Preis allein."
            ),
            icon="car",
        ),
    )
    components.append(
        c.assumption_note(
            "annahmen",
            title="Wie die Passung berechnet wird",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_MOBILITAET,
            as_of=dd.STAND,
        )
    )
    components.insert(0, c.column("root", children))

    data["annahmen"] = calc.annahmen(profil) + [
        "Passung berücksichtigt Winterreichweite, Ladestopps, Budget und Ihre Fahrzeugklasse.",
        "Generische Fahrzeugklassen statt konkreter Modelle – bewusst herstellerneutral.",
    ]

    return Surface(
        surface_id="fahrzeuge",
        title="Fahrzeugvorschläge",
        components=components,
        data=data,
    )


# ---------------------------------------------------------------------------
# Surface: Kostenvergleich
# ---------------------------------------------------------------------------


def kosten_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Total cost of ownership, itemised so nothing hides in a total."""
    k = calc.kostenvergleich(profil)
    diff = k["differenz_eur"]
    guenstiger = diff > 0

    components = [
        c.column("root", ["kopf", "kennzahlen", "diagramm", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Kosten",
            title=f"Über {k['haltedauer_jahre']} Jahre gerechnet",
            subtitle=(
                "Alle Posten einzeln – Wertverlust, Energie, Wartung, "
                "Versicherung, Steuer und THG-Quote."
            ),
            icon="euro",
        ),
        c.row("kennzahlen", ["k_diff", "k_energie", "k_co2"], align="stretch"),
        c.insight_card(
            "k_diff",
            title="Elektro gegen Verbrenner",
            body=(
                (
                    f"Das E-Auto ist bei Ihrem Profil insgesamt günstiger – "
                    f"das entspricht {abs(k['differenz_eur_monat'])} € im Monat."
                )
                if guenstiger
                else (
                    f"Mit Ihrer heutigen Ladesituation ist das E-Auto insgesamt "
                    f"teurer – rund {abs(k['differenz_eur_monat'])} € im Monat. "
                    "Mit einer eigenen Lademöglichkeit dreht sich das Bild."
                )
            ),
            metric=f"{abs(diff):,.0f} €".replace(",", "."),
            metric_label="Vorteil Elektro" if guenstiger else "Nachteil Elektro",
            tone="positive" if guenstiger else "caution",
            icon="euro",
            weight=1,
        ),
        c.insight_card(
            "k_energie",
            title="Energie je 100 km",
            body=(
                f"Strom {k['energie_elektro_eur_100km']:.2f} € gegenüber "
                f"Kraftstoff {k['energie_verbrenner_eur_100km']:.2f} €.".replace(".", ",")
            ),
            metric=f"{k['energie_elektro_eur_100km']:.2f} €".replace(".", ","),
            metric_label="elektrisch, je 100 km",
            tone="positive"
            if k["energie_elektro_eur_100km"] < k["energie_verbrenner_eur_100km"]
            else "caution",
            icon="plug",
            weight=1,
        ),
        c.insight_card(
            "k_co2",
            title="CO₂ pro Jahr",
            body=(
                "Gerechnet mit dem deutschen Strommix. Mit eigener PV-Anlage "
                "oder Ökostromtarif fällt die Bilanz deutlich besser aus."
            ),
            metric=f"− {k['co2_ersparnis_kg_a'] / 1000:.1f} t",
            metric_label="gegenüber Verbrenner",
            tone="positive",
            icon="leaf",
            weight=1,
        ),
        c.metric_chart(
            "diagramm",
            title="Kostenposten im Vergleich",
            subtitle=(
                f"Gesamtkosten über {k['haltedauer_jahre']} Jahre bei "
                f"{k['jahres_km']:,.0f} km im Jahr.".replace(",", ".")
            ),
            chart_type="groupedBar",
            categories=c.bind("/kategorien"),
            series=c.bind("/serien"),
            unit="€",
            value_format="currency",
        ),
        c.assumption_note(
            "annahmen",
            title="Annahmen dieser Rechnung",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_MOBILITAET,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="kosten",
        title="Kostenvergleich",
        components=components,
        data={
            "kategorien": k["kategorien"],
            "serien": k["serien"],
            "annahmen": calc.annahmen(profil)
            + [
                f"Gesamtkosten Elektro {k['gesamt_elektro_eur']:,.0f} €, "
                f"Verbrenner {k['gesamt_verbrenner_eur']:,.0f} €".replace(",", "."),
                "Wertverlust auf Basis angenommener Restwerte nach vier Jahren.",
            ],
        },
    )
