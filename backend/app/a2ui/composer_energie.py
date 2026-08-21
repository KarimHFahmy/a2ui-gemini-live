"""Composes the Energieberater surfaces from domain results.

One function per advisory tool. Each returns a fully formed
:class:`~app.a2ui.surface.Surface`; nothing here talks to the model and nothing
invents a number — everything comes out of :mod:`app.domain.energie`.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import energie as calc
from . import components as c
from .surface import Surface

# ---------------------------------------------------------------------------
# Surface: Verstandenes Profil
# ---------------------------------------------------------------------------


def profil_surface(profil: calc.Gebaeudeprofil, offene_punkte: list[str]) -> Surface:
    """"Zusammenfassung des Verstandenen" — the trust anchor of the session."""
    bedarf = calc.waermebedarf_kwh_a(profil)
    heizung_label = {
        "gas": "Gasheizung",
        "oel": "Ölheizung",
        "fernwaerme": "Fernwärme",
        "nachtspeicher": "Nachtspeicherheizung",
        "waermepumpe": "Wärmepumpe",
    }[profil.heizung]
    stand_label = {
        "unsaniert": "weitgehend unsaniert",
        "teilsaniert": "teilsaniert",
        "saniert": "gut saniert",
    }[profil.sanierungsstand]

    fakten = [
        {"label": "Gebäude", "wert": f"Baujahr {profil.baujahr}, {profil.wohnflaeche_qm:.0f} m²"},
        {"label": "Heizung heute", "wert": heizung_label},
        {"label": "Zustand", "wert": stand_label},
        {"label": "Haushalt", "wert": f"{profil.personen} Personen"},
        {
            "label": "Wärmebedarf",
            "wert": f"rund {bedarf:,.0f} kWh im Jahr".replace(",", "."),
            "geschaetzt": profil.verbrauch_kwh_a is None,
        },
    ]
    if profil.prioritaeten:
        fakten.append(
            {"label": "Wichtig für Sie", "wert": ", ".join(profil.prioritaeten)}
        )
    if profil.bedenken:
        fakten.append({"label": "Ihre Bedenken", "wert": ", ".join(profil.bedenken)})

    components = [
        c.column("root", ["kopf", "zusammenfassung"]),
        c.advisory_header(
            "kopf",
            eyebrow="Ihre Situation",
            title="Das habe ich verstanden",
            subtitle="Sagen Sie einfach, wenn etwas nicht stimmt – ich passe es an.",
            icon="home",
        ),
        c.profile_summary(
            "zusammenfassung",
            title="Ihr Zuhause",
            facts=c.bind("/fakten"),
            open_points=c.bind("/offen"),
            note="Geschätzte Werte sind gekennzeichnet und lassen sich im Gespräch korrigieren.",
        ),
    ]

    return Surface(
        surface_id="profil",
        title="Ihre Situation",
        components=components,
        data={"fakten": fakten, "offen": offene_punkte},
    )


# ---------------------------------------------------------------------------
# Surface: Wärmepumpen-Eignung
# ---------------------------------------------------------------------------


def eignung_surface(profil: calc.Gebaeudeprofil) -> Surface:
    """Answers the winter question with the physics, not with reassurance."""
    check = calc.eignung(profil)

    tone = (
        "positive"
        if check["score"] >= 75
        else "neutral" if check["score"] >= 50 else "caution"
    )

    monate = ["Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr"]
    # Verteilung des Jahreswärmebedarfs auf die Heizperiode.
    anteile = [0.08, 0.14, 0.19, 0.21, 0.17, 0.13, 0.08]
    bedarf = check["waermebedarf_kwh_a"]
    heizlast = [round(bedarf * a) for a in anteile]
    # Die Wärmepumpe deckt die Last; nur bei sehr hohem Vorlauf springt an den
    # kältesten Tagen ein Heizstab ein.
    heizstab_anteil = 0.10 if check["vorlauftemperatur_c"] >= 65 else 0.0
    wp_anteil = [round(w * (1 - heizstab_anteil)) for w in heizlast]
    stab_anteil = [round(w * heizstab_anteil) for w in heizlast]

    components = [
        c.column("root", ["kopf", "kennzahlen", "diagramm", "massnahmen", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Wärmepumpen-Check",
            title=f"Ihr Haus ist {check['urteil']}",
            subtitle=(
                "Entscheidend ist nicht die Außentemperatur, sondern wie warm "
                "das Wasser in Ihren Heizkörpern sein muss."
            ),
            icon="thermometer",
        ),
        c.row("kennzahlen", ["k_vorlauf", "k_jaz", "k_last"], align="stretch"),
        c.insight_card(
            "k_vorlauf",
            title="Nötige Vorlauftemperatur",
            body=(
                "Je niedriger, desto effizienter arbeitet die Wärmepumpe. "
                "Unter 55 °C ist der Betrieb unkritisch."
            ),
            metric=f"{check['vorlauftemperatur_c']} °C",
            metric_label="im Auslegungsfall",
            tone="positive" if check["vorlauftemperatur_c"] <= 55 else "caution",
            icon="thermometer",
            weight=1,
        ),
        c.insight_card(
            "k_jaz",
            title="Erwartete Jahresarbeitszahl",
            body=(
                f"Aus 1 kWh Strom werden im Jahresmittel {check['jaz']} kWh Wärme. "
                f"Das entspricht rund {check['strombedarf_kwh_a']:,.0f} kWh Strom im Jahr.".replace(
                    ",", "."
                )
            ),
            metric=f"{check['jaz']}",
            metric_label="JAZ",
            tone="positive" if check["jaz"] >= 3.5 else "neutral",
            icon="efficiency",
            weight=1,
        ),
        c.insight_card(
            "k_last",
            title="Benötigte Heizleistung",
            body=(
                "Danach wird die Wärmepumpe ausgelegt. Zu groß dimensioniert "
                "taktet sie und verschleißt schneller."
            ),
            metric=f"{check['heizlast_kw']} kW",
            metric_label="Norm-Heizlast",
            tone="neutral",
            icon="power",
            weight=1,
        ),
        c.metric_chart(
            "diagramm",
            title="So verteilt sich Ihre Heizlast über den Winter",
            subtitle=(
                "Auch im Januar deckt die Wärmepumpe die Last – "
                + (
                    "an den kältesten Tagen unterstützt ein Heizstab."
                    if heizstab_anteil
                    else "ohne Zusatzheizung."
                )
            ),
            chart_type="stackedBar",
            categories=c.bind("/monate"),
            series=c.bind("/last"),
            unit="kWh",
            value_format="number",
        ),
        c.insight_card(
            "massnahmen",
            title="Was die Effizienz noch verbessert",
            body="\n".join(f"- {m}" for m in check["massnahmen"]),
            tone="neutral",
            icon="tools",
        ),
        c.assumption_note(
            "annahmen",
            title="Annahmen dieser Einschätzung",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_ENERGIE,
            as_of=dd.STAND,
        ),
    ]

    serien = [{"label": "Wärmepumpe", "werte": wp_anteil}]
    if heizstab_anteil:
        serien.append({"label": "Heizstab", "werte": stab_anteil})

    return Surface(
        surface_id="eignung",
        title="Wärmepumpen-Check",
        components=components,
        data={
            "monate": monate,
            "last": serien,
            "annahmen": calc.annahmen(profil) + check["hinweise"],
        },
    )


# ---------------------------------------------------------------------------
# Surface: Szenarienvergleich
# ---------------------------------------------------------------------------


def szenarien_surface(
    profil: calc.Gebaeudeprofil,
    szenarien: list[calc.Szenario],
    *,
    empfohlen_id: str,
) -> Surface:
    """Baustein Szenario + Vergleich: the same options seen two ways."""
    komfort_label = {1: "gering", 2: "spürbar", 3: "gut", 4: "hoch", 5: "sehr hoch"}
    aufwand_label = {1: "keiner", 2: "gering", 3: "mittel", 4: "hoch", 5: "sehr hoch"}

    scenario_cards = [
        {
            "id": s.id,
            "label": s.label,
            "beschreibung": s.beschreibung,
            "kennzahl": (
                "keine Investition"
                if s.eigenanteil_eur == 0
                else f"{s.eigenanteil_eur:,.0f} €".replace(",", ".")
            ),
            "kennzahlLabel": "Eigenanteil nach Förderung",
            "empfohlen": s.id == empfohlen_id,
            "massnahmen": s.massnahmen,
        }
        for s in szenarien
    ]

    spalten = [{"id": s.id, "label": s.label} for s in szenarien]
    zeilen = [
        {
            "label": "Investition",
            "werte": [
                "–" if s.investition_eur == 0 else f"{s.investition_eur:,.0f} €".replace(",", ".")
                for s in szenarien
            ],
        },
        {
            "label": "Förderung",
            "werte": [
                "–" if s.foerderung_eur == 0 else f"− {s.foerderung_eur:,.0f} €".replace(",", ".")
                for s in szenarien
            ],
            "akzent": "positive",
        },
        {
            "label": "Eigenanteil",
            "werte": [f"{s.eigenanteil_eur:,.0f} €".replace(",", ".") for s in szenarien],
            "hervorheben": True,
        },
        {
            "label": "Energiekosten pro Jahr",
            "werte": [f"{s.energiekosten_eur_a:,.0f} €".replace(",", ".") for s in szenarien],
        },
        {
            "label": "CO₂ pro Jahr",
            "werte": [f"{s.co2_kg_a / 1000:.1f} t" for s in szenarien],
        },
        {
            "label": "Komfort",
            "werte": [komfort_label[s.komfort_score] for s in szenarien],
        },
        {
            "label": "Aufwand für Sie",
            "werte": [aufwand_label[s.aufwand_score] for s in szenarien],
        },
    ]

    components = [
        c.column("root", ["kopf", "auswahl", "tabelle", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Ihre Wege",
            title="Drei Wege, ein Zuhause",
            subtitle="Wählen Sie einen Weg aus – ich rechne ihn für Sie durch.",
            icon="compare",
        ),
        c.scenario_selector(
            "auswahl",
            scenarios=c.bind("/szenarien"),
            selected_path="/gewaehlt",
            event_name="szenario_gewaehlt",
        ),
        c.comparison_table(
            "tabelle",
            title="Die Wege im direkten Vergleich",
            columns=c.bind("/spalten"),
            rows=c.bind("/zeilen"),
            highlight=c.bind("/gewaehlt"),
        ),
        c.assumption_note(
            "annahmen",
            title="Annahmen dieses Vergleichs",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_ENERGIE,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="szenarien",
        title="Szenarienvergleich",
        components=components,
        data={
            "szenarien": scenario_cards,
            "spalten": spalten,
            "zeilen": zeilen,
            "gewaehlt": empfohlen_id,
            "annahmen": calc.annahmen(profil),
        },
    )


# ---------------------------------------------------------------------------
# Surface: Wirtschaftlichkeit
# ---------------------------------------------------------------------------


def wirtschaftlichkeit_surface(
    profil: calc.Gebaeudeprofil,
    szenarien: list[calc.Szenario],
    *,
    fokus_id: str,
) -> Surface:
    """The 20-year curve — where the decision actually flips."""
    verlauf = calc.kostenverlauf(szenarien)
    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next((s for s in szenarien if s.id == fokus_id), szenarien[1])
    amort = calc.amortisation(bestand, fokus)

    ersparnis_a = bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a
    gesamt_20 = next(
        (s["werte"][-1] for s in verlauf["serien"] if s["id"] == "bestand"), 0
    ) - next((s["werte"][-1] for s in verlauf["serien"] if s["id"] == fokus.id), 0)

    if amort["erreichbar"]:
        amort_text = (
            f"Nach rund {amort['jahre']} Jahren haben Sie die Mehrinvestition wieder drin. "
            "Ab dann sparen Sie jedes Jahr."
        )
        amort_metric = f"{amort['jahre']} Jahre"
    else:
        amort_text = (
            "Über 40 Jahre gerechnet gleicht sich die Mehrinvestition nicht aus. "
            "Dieser Weg lohnt sich für Sie eher über Komfort und CO₂ als über die Kosten."
        )
        amort_metric = "–"

    components = [
        c.column("root", ["kopf", "diagramm", "kennzahlen", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Wirtschaftlichkeit",
            title=f"„{fokus.label}“ über 20 Jahre gerechnet",
            subtitle="Investition, Förderung und laufende Kosten zusammen betrachtet.",
            icon="chart",
        ),
        c.metric_chart(
            "diagramm",
            title="Kumulierte Gesamtkosten",
            subtitle=(
                "Der Punkt, an dem sich die Linien kreuzen, ist Ihr "
                "Break-even gegenüber „weiter wie bisher“."
            ),
            chart_type="line",
            categories=c.bind("/kategorien"),
            series=c.bind("/serien"),
            unit="€",
            value_format="currency",
        ),
        c.row("kennzahlen", ["k_amort", "k_jahr", "k_gesamt"], align="stretch"),
        c.insight_card(
            "k_amort",
            title="Break-even",
            body=amort_text,
            metric=amort_metric,
            metric_label="bis zum Ausgleich",
            tone="positive" if amort["erreichbar"] and amort["jahre"] <= 15 else "neutral",
            icon="clock",
            weight=1,
        ),
        c.insight_card(
            "k_jahr",
            title="Laufende Kosten pro Jahr",
            body=(
                f"Statt {bestand.betriebskosten_eur_a:,.0f} € zahlen Sie "
                f"{fokus.betriebskosten_eur_a:,.0f} € – Energie und Wartung zusammen.".replace(
                    ",", "."
                )
            ),
            metric=f"− {ersparnis_a:,.0f} €".replace(",", "."),
            metric_label="pro Jahr",
            tone="positive" if ersparnis_a > 0 else "caution",
            icon="euro",
            weight=1,
        ),
        c.insight_card(
            "k_gesamt",
            title="Über 20 Jahre",
            body=(
                "Differenz gegenüber „weiter wie bisher“, inklusive Investition, "
                "Förderung und angenommener Preissteigerung."
            ),
            metric=f"{gesamt_20:,.0f} €".replace(",", "."),
            metric_label="Vorteil gesamt",
            tone="positive" if gesamt_20 > 0 else "caution",
            icon="trend",
            weight=1,
        ),
        c.assumption_note(
            "annahmen",
            title="Wie diese Kurve entsteht",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_ENERGIE,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="wirtschaftlichkeit",
        title="Wirtschaftlichkeit",
        components=components,
        data={
            "kategorien": verlauf["kategorien"],
            "serien": verlauf["serien"],
            "annahmen": calc.annahmen(profil),
        },
    )


# ---------------------------------------------------------------------------
# Surface: Förderung und Umsetzungsfahrplan
# ---------------------------------------------------------------------------


def foerderung_surface(
    profil: calc.Gebaeudeprofil,
    szenario: calc.Szenario,
    foerderdetails: dict[str, Any],
) -> Surface:
    """Funding and the sequence of steps — "Förder- und Umsetzungsorientierung"."""
    bausteine_text = "\n".join(
        f"- {b['label']}: {b['satz']:.0%}" for b in foerderdetails["bausteine"]
    )
    if foerderdetails["gedeckelt"]:
        bausteine_text += (
            f"\n- Deckelung bei {dd.FOERDERUNG['max_satz']:.0%} "
            f"(rechnerisch {foerderdetails['satz_ungedeckelt']:.0%})"
        )

    schritte = [
        {
            "titel": "Energieberatung und Angebot",
            "detail": (
                "Fachbetrieb nimmt das Gebäude auf, prüft Heizlast und "
                "Heizflächen und erstellt ein Angebot."
            ),
            "dauer": "2–4 Wochen",
            "status": "start",
        },
        {
            "titel": "Förderantrag stellen",
            "detail": (
                "Antrag mit Liefer- und Leistungsvertrag einreichen. "
                "Wichtig: vor Beginn der Arbeiten, sonst entfällt die Förderung."
            ),
            "dauer": "1–2 Wochen",
            "status": "wichtig",
        },
        {
            "titel": "Förderzusage abwarten",
            "detail": "Erst nach der Zusage verbindlich beauftragen.",
            "dauer": "2–6 Wochen",
            "status": "warten",
        },
        {
            "titel": "Einbau",
            "detail": (
                "Montage der Wärmepumpe, hydraulischer Abgleich und Einregulierung "
                "der Heizkurve."
            ),
            "dauer": "2–5 Tage",
            "status": "umsetzung",
        },
        {
            "titel": "Nachweis und Auszahlung",
            "detail": "Fachunternehmererklärung einreichen, Zuschuss wird ausgezahlt.",
            "dauer": "4–8 Wochen",
            "status": "ziel",
        },
    ]

    components = [
        c.column("root", ["kopf", "foerder_zeile", "fahrplan", "annahmen"]),
        c.advisory_header(
            "kopf",
            eyebrow="Förderung & Umsetzung",
            title="Was der Staat übernimmt – und in welcher Reihenfolge",
            subtitle=(
                "Die Reihenfolge entscheidet: Wer zu früh beauftragt, verliert den Zuschuss."
            ),
            icon="badge",
        ),
        c.row("foerder_zeile", ["f_betrag", "f_bausteine"], align="stretch"),
        c.insight_card(
            "f_betrag",
            title="Erwarteter Zuschuss",
            body=(
                f"Bezogen auf förderfähige Kosten von "
                f"{foerderdetails['foerderfaehige_kosten_eur']:,.0f} €. "
                f"Ihr Eigenanteil sinkt damit auf "
                f"{szenario.eigenanteil_eur:,.0f} €.".replace(",", ".")
            ),
            metric=f"{foerderdetails['betrag_eur']:,.0f} €".replace(",", "."),
            metric_label=f"{foerderdetails['satz']:.0%} Förderquote",
            tone="positive",
            icon="badge",
            weight=1,
        ),
        c.insight_card(
            "f_bausteine",
            title="So setzt sich die Quote zusammen",
            body=bausteine_text + f"\n\n_{foerderdetails['hinweis']}_",
            tone="neutral",
            icon="layers",
            weight=1,
        ),
        c.timeline(
            "fahrplan", title="Ihr Weg in fünf Schritten", steps=c.bind("/schritte")
        ),
        c.assumption_note(
            "annahmen",
            title="Hinweise zur Förderung",
            assumptions=c.bind("/annahmen"),
            source=dd.QUELLE_ENERGIE,
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="foerderung",
        title="Förderung & Fahrplan",
        components=components,
        data={
            "schritte": schritte,
            "annahmen": [
                foerderdetails["hinweis"],
                "Antragstellung vor Vorhabenbeginn ist zwingend.",
                "Boni sind an Nachweise gebunden (z. B. Einkommen, Austausch der Altanlage).",
                dd.DISCLAIMER,
            ],
        },
    )
