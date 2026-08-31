"""Composes the Energieberater surfaces.

One function per advisory tool. Nothing here talks to the model and nothing
invents a number — every figure comes out of :mod:`app.domain.energie`.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import energie as calc
from ..format_de import de
from .builder import SurfaceBuilder, bind, minus, money, over, plus, times
from .surface import Surface

_HEIZUNG_LABEL = {
    "gas": "Gasheizung",
    "oel": "Ölheizung",
    "fernwaerme": "Fernwärme",
    "nachtspeicher": "Nachtspeicherheizung",
    "waermepumpe": "Wärmepumpe",
}
_STAND_LABEL = {
    "unsaniert": "weitgehend unsaniert",
    "teilsaniert": "teilsaniert",
    "saniert": "gut saniert",
}


def _euro(value: float) -> str:
    return de(value, unit="€")


def profil_surface(profil: calc.Gebaeudeprofil, offene_punkte: list[str]) -> Surface:
    """"Zusammenfassung des Verstandenen" — the trust anchor of the session.

    The facts are a `repeat` over the data model rather than fixed components,
    so correcting the agent mid-sentence is a one-message data patch.
    """
    b = SurfaceBuilder("profil", "Ihre Situation")

    fakt = b.column(
        [
            b.text(bind("label"), variant="caption"),
            b.text(bind("wert")),
        ]
    )

    # This surface is pinned to the top of the stage for the whole session, so
    # everything lives inside one card. Bare text on the stage background would
    # have the scrolling conversation showing through it.
    inner = [
        b.text("Ihre Situation", variant="caption"),
        b.text("Das habe ich verstanden", variant="h3"),
        b.repeat(fakt, "/fakten", direction="horizontal"),
    ]
    if offene_punkte:
        inner.append(b.bullets(offene_punkte, heading="Noch offen"))
    inner.append(
        b.text(
            "Sagen Sie einfach, wenn etwas nicht stimmt – ich passe es an.",
            variant="caption",
        )
    )

    b.root(b.card(b.column(inner)))

    bedarf = calc.waermebedarf_kwh_a(profil)
    fakten: list[dict[str, str]] = [
        {"label": "Gebäude", "wert": f"Baujahr {profil.baujahr}, {profil.wohnflaeche_qm:.0f} m²"},
        {"label": "Heizung heute", "wert": _HEIZUNG_LABEL[profil.heizung]},
        {"label": "Zustand", "wert": _STAND_LABEL[profil.sanierungsstand]},
        {"label": "Haushalt", "wert": f"{profil.personen} Personen"},
        {
            "label": "Wärmebedarf",
            # Estimated values are marked so the client can correct them.
            "wert": ("~ " if profil.verbrauch_kwh_a is None else "")
            + de(bedarf, unit="kWh/Jahr"),
        },
    ]
    if profil.prioritaeten:
        fakten.append({"label": "Wichtig für Sie", "wert": ", ".join(profil.prioritaeten)})
    if profil.bedenken:
        fakten.append({"label": "Ihre Bedenken", "wert": ", ".join(profil.bedenken)})

    return b.finish({"fakten": fakten})


def eignung_surface(profil: calc.Gebaeudeprofil) -> Surface:
    """Answers the winter question with the physics, not with reassurance."""
    check = calc.eignung(profil)
    b = SurfaceBuilder("eignung", "Wärmepumpen-Check")

    monate = ["Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr"]
    anteile = [0.08, 0.14, 0.19, 0.21, 0.17, 0.13, 0.08]
    bedarf = check["waermebedarf_kwh_a"]
    heizlast = [round(bedarf * anteil) for anteil in anteile]
    # Only a very high flow temperature calls for a booster on the coldest days.
    stab_anteil = 0.10 if check["vorlauftemperatur_c"] >= 65 else 0.0

    serien: list[dict[str, Any]] = [
        {"label": "Wärmepumpe", "werte": [round(w * (1 - stab_anteil)) for w in heizlast]}
    ]
    if stab_anteil:
        serien.append(
            {"label": "Heizstab", "werte": [round(w * stab_anteil) for w in heizlast]}
        )

    b.root(
        b.column(
            [
                b.heading(
                    "Wärmepumpen-Check",
                    f"Ihr Haus ist {check['urteil']}",
                    "Entscheidend ist nicht die Außentemperatur, sondern wie warm "
                    "das Wasser in Ihren Heizkörpern sein muss.",
                ),
                b.row(
                    [
                        b.stat_card(
                            title="Nötige Vorlauftemperatur",
                            metric=f"{check['vorlauftemperatur_c']} °C",
                            metric_label="im Auslegungsfall",
                            body="Je niedriger, desto effizienter arbeitet die "
                            "Wärmepumpe. Unter 55 °C ist der Betrieb unkritisch.",
                            tone="positive" if check["vorlauftemperatur_c"] <= 55 else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title="Erwartete Jahresarbeitszahl",
                            metric=de(check["jaz"], decimals=1),
                            metric_label="JAZ",
                            body=f"Aus 1 kWh Strom werden {de(check['jaz'], decimals=1)} "
                            f"kWh Wärme – rund {de(check['strombedarf_kwh_a'])} kWh "
                            "Strom im Jahr.",
                            tone="positive" if check["jaz"] >= 3.5 else "neutral",
                            weight=1,
                        ),
                        b.stat_card(
                            title="Benötigte Heizleistung",
                            metric=de(check["heizlast_kw"], decimals=1, unit="kW"),
                            metric_label="Norm-Heizlast",
                            body="Danach wird die Wärmepumpe ausgelegt. Zu groß "
                            "dimensioniert taktet sie und verschleißt schneller.",
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title="So verteilt sich Ihre Heizlast über den Winter",
                        subtitle="Auch im Januar deckt die Wärmepumpe die Last"
                        + (" – an den kältesten Tagen mit Heizstab." if stab_anteil else " allein."),
                        chart_type="stackedBar",
                        categories=bind("/monate"),
                        series=bind("/last"),
                        unit="kWh",
                    )
                ),
                b.card(
                    b.bullets(check["massnahmen"], heading="Was die Effizienz noch verbessert")
                ),
                b.assumptions(
                    calc.annahmen(profil) + check["hinweise"],
                    source=dd.QUELLE_ENERGIE,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish({"monate": monate, "last": serien})


def szenarien_surface(
    profil: calc.Gebaeudeprofil,
    szenarien: list[calc.Szenario],
    *,
    empfohlen_id: str,
) -> Surface:
    """The options, seen two ways: pick one, then compare them all.

    The ChoicePicker and the table highlight share `/gewaehlt`, so choosing a
    scenario re-highlights the comparison immediately — client-side, with no
    round trip. The button is what tells the agent, and it reacts in speech.
    """
    b = SurfaceBuilder("szenarien", "Szenarienvergleich")

    komfort = {1: "gering", 2: "spürbar", 3: "gut", 4: "hoch", 5: "sehr hoch"}
    aufwand = {1: "keiner", 2: "gering", 3: "mittel", 4: "hoch", 5: "sehr hoch"}

    b.root(
        b.column(
            [
                b.heading(
                    "Ihre Wege",
                    "Drei Wege, ein Zuhause",
                    "Wählen Sie einen Weg – ich rechne ihn für Sie durch.",
                ),
                b.card(
                    b.column(
                        [
                            b.choice(
                                [
                                    (
                                        f"{s.label} · {'keine Investition' if s.eigenanteil_eur == 0 else _euro(s.eigenanteil_eur)}",
                                        s.id,
                                    )
                                    for s in szenarien
                                ],
                                "/gewaehlt",
                                label="Szenario",
                            ),
                            b.button(
                                "Diesen Weg durchrechnen",
                                event="szenario_gewaehlt",
                                context={"szenarioId": bind("/gewaehlt")},
                                variant="primary",
                            ),
                        ]
                    )
                ),
                b.card(
                    b.table(
                        title="Die Wege im direkten Vergleich",
                        columns=bind("/spalten"),
                        rows=bind("/zeilen"),
                        highlight=bind("/gewaehlt"),
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil), source=dd.QUELLE_ENERGIE, as_of=dd.STAND
                ),
            ]
        )
    )

    return b.finish(
        {
            # ChoicePicker binds a *list* of selected values; the table
            # highlight reads the same path and takes the first entry.
            "gewaehlt": [empfohlen_id],
            "spalten": [{"id": s.id, "label": s.label} for s in szenarien],
            "zeilen": [
                {
                    "label": "Investition",
                    "werte": ["–" if s.investition_eur == 0 else _euro(s.investition_eur) for s in szenarien],
                },
                {
                    "label": "Förderung",
                    "werte": ["–" if s.foerderung_eur == 0 else f"− {_euro(s.foerderung_eur)}" for s in szenarien],
                    "akzent": "positive",
                },
                {
                    "label": "Eigenanteil",
                    "werte": [_euro(s.eigenanteil_eur) for s in szenarien],
                    "hervorheben": True,
                },
                {
                    "label": "Energiekosten pro Jahr",
                    "werte": [_euro(s.energiekosten_eur_a) for s in szenarien],
                },
                {"label": "CO₂ pro Jahr", "werte": [de(s.co2_kg_a / 1000, decimals=1, unit="t") for s in szenarien]},
                {"label": "Komfort", "werte": [komfort[s.komfort_score] for s in szenarien]},
                {"label": "Aufwand für Sie", "werte": [aufwand[s.aufwand_score] for s in szenarien]},
            ],
        }
    )


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

    ersparnis = bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a
    gesamt = next(s["werte"][-1] for s in verlauf["serien"] if s["id"] == "bestand") - next(
        s["werte"][-1] for s in verlauf["serien"] if s["id"] == fokus.id
    )

    if amort["erreichbar"]:
        amort_metric = f"{amort['jahre']} Jahre"
        amort_body = (
            f"Nach rund {amort['jahre']} Jahren haben Sie die Mehrinvestition "
            "wieder drin. Ab dann sparen Sie jedes Jahr."
        )
        amort_tone = "positive" if amort["jahre"] <= 15 else "neutral"
    else:
        amort_metric = "–"
        amort_body = (
            "Über 40 Jahre gleicht sich die Mehrinvestition nicht aus. Dieser Weg "
            "lohnt sich für Sie eher über Komfort und CO₂ als über die Kosten."
        )
        amort_tone = "caution"

    b = SurfaceBuilder("wirtschaftlichkeit", "Wirtschaftlichkeit")
    b.root(
        b.column(
            [
                b.heading(
                    "Wirtschaftlichkeit",
                    f"„{fokus.label}“ über 20 Jahre gerechnet",
                    "Investition, Förderung und laufende Kosten zusammen betrachtet.",
                ),
                b.card(
                    b.chart(
                        title="Kumulierte Gesamtkosten",
                        subtitle="Wo sich die Linien kreuzen, liegt Ihr Break-even "
                        "gegenüber „weiter wie bisher“.",
                        chart_type="line",
                        categories=bind("/kategorien"),
                        series=bind("/serien"),
                        unit="€",
                        value_format="currency",
                    )
                ),
                b.row(
                    [
                        b.stat_card(
                            title="Break-even",
                            metric=amort_metric,
                            metric_label="bis zum Ausgleich",
                            body=amort_body,
                            tone=amort_tone,
                            weight=1,
                        ),
                        b.stat_card(
                            title="Laufende Kosten pro Jahr",
                            metric=f"− {_euro(ersparnis)}",
                            metric_label="pro Jahr",
                            body=f"Statt {_euro(bestand.betriebskosten_eur_a)} zahlen Sie "
                            f"{_euro(fokus.betriebskosten_eur_a)} – Energie und Wartung zusammen.",
                            tone="positive" if ersparnis > 0 else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title="Über 20 Jahre",
                            metric=_euro(gesamt),
                            metric_label="Vorteil gesamt",
                            body="Differenz gegenüber „weiter wie bisher“, inklusive "
                            "Investition, Förderung und angenommener Preissteigerung.",
                            tone="positive" if gesamt > 0 else "caution",
                            weight=1,
                        ),
                    ]
                ),
                b.assumptions(
                    calc.annahmen(profil), source=dd.QUELLE_ENERGIE, as_of=dd.STAND
                ),
            ]
        )
    )

    return b.finish({"kategorien": verlauf["kategorien"], "serien": verlauf["serien"]})


def foerderung_surface(
    profil: calc.Gebaeudeprofil,
    szenario: calc.Szenario,
    details: dict[str, Any],
) -> Surface:
    """Funding and the sequence of steps.

    The steps are a `repeat` over the data model: one template component
    renders the whole plan, and the order is data.
    """
    b = SurfaceBuilder("foerderung", "Förderung & Fahrplan")

    schritt = b.card(
        b.column(
            [
                b.row(
                    [
                        b.text(bind("titel"), weight=1),
                        b.text(bind("dauer"), variant="caption"),
                    ],
                    align="center",
                ),
                b.text(bind("detail"), variant="body"),
            ]
        )
    )

    bausteine = [f"{item['label']}: {item['satz']:.0%}" for item in details["bausteine"]]
    if details["gedeckelt"]:
        bausteine.append(
            f"Deckelung bei {dd.FOERDERUNG['max_satz']:.0%} "
            f"(rechnerisch {details['satz_ungedeckelt']:.0%})"
        )

    b.root(
        b.column(
            [
                b.heading(
                    "Förderung & Umsetzung",
                    "Was der Staat übernimmt – und in welcher Reihenfolge",
                    "Die Reihenfolge entscheidet: Wer zu früh beauftragt, verliert "
                    "den Zuschuss.",
                ),
                b.row(
                    [
                        b.stat_card(
                            title="Erwarteter Zuschuss",
                            metric=_euro(details["betrag_eur"]),
                            metric_label=f"{details['satz']:.0%} Förderquote",
                            body=f"Bezogen auf förderfähige Kosten von "
                            f"{_euro(details['foerderfaehige_kosten_eur'])}. Ihr Eigenanteil "
                            f"sinkt damit auf {_euro(szenario.eigenanteil_eur)}.",
                            tone="positive",
                            weight=1,
                        ),
                        b.card(
                            b.bullets(bausteine, heading="So setzt sich die Quote zusammen"),
                            weight=1,
                        ),
                    ]
                ),
                b.text("Ihr Weg in fünf Schritten", variant="h3"),
                b.repeat(schritt, "/schritte"),
                b.assumptions(
                    [
                        details["hinweis"],
                        "Antragstellung vor Vorhabenbeginn ist zwingend.",
                        "Boni sind an Nachweise gebunden (z. B. Einkommen, Austausch der Altanlage).",
                        dd.DISCLAIMER,
                    ],
                    source=dd.QUELLE_ENERGIE,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish(
        {
            "schritte": [
                {
                    "titel": "**1. Energieberatung und Angebot**",
                    "detail": "Fachbetrieb nimmt das Gebäude auf, prüft Heizlast und "
                    "Heizflächen und erstellt ein Angebot.",
                    "dauer": "2–4 Wochen",
                },
                {
                    "titel": "**2. Förderantrag stellen**",
                    "detail": "Antrag mit Liefer- und Leistungsvertrag einreichen. "
                    "**Wichtig:** vor Beginn der Arbeiten, sonst entfällt die Förderung.",
                    "dauer": "1–2 Wochen",
                },
                {
                    "titel": "**3. Förderzusage abwarten**",
                    "detail": "Erst nach der Zusage verbindlich beauftragen.",
                    "dauer": "2–6 Wochen",
                },
                {
                    "titel": "**4. Einbau**",
                    "detail": "Montage der Wärmepumpe, hydraulischer Abgleich und "
                    "Einregulierung der Heizkurve.",
                    "dauer": "2–5 Tage",
                },
                {
                    "titel": "**5. Nachweis und Auszahlung**",
                    "detail": "Fachunternehmererklärung einreichen, Zuschuss wird ausgezahlt.",
                    "dauer": "4–8 Wochen",
                },
            ]
        }
    )


def stellschrauben_surface(
    profil: calc.Gebaeudeprofil,
    bestand: calc.Szenario,
    fokus: calc.Szenario,
) -> Surface:
    """„Was wäre wenn?“ — die Beratung rechnet mit den Annahmen des Kunden.

    Die zwei Preise, an denen die ganze Wirtschaftlichkeit hängt, kennt niemand.
    Jede Beratung setzt hier eine Annahme, und genau daran scheitert das
    Vertrauen: „Ihr rechnet euch das schön.“ Also übergeben wir den Regler.

    Die Zahlen darunter rechnen im Browser mit, ohne Umweg über den Agenten —
    aus Koeffizienten, die :func:`app.domain.energie.stellschrauben` geliefert
    hat. Erst der Knopf macht die Annahme verbindlich für die ganze Beratung.
    """
    werte = calc.stellschrauben(profil, bestand, fokus)

    # Die Rechnung, wie sie im Browser steht. Jede Zeile liest die Regler und
    # rechnet neu, sobald sich einer bewegt.
    kosten_alt = plus(
        times(bind("/basis/eur_je_ct_alt"), bind("/wenn/preis_alt_ct")),
        bind("/basis/wartung_alt"),
    )
    kosten_neu = plus(
        times(bind("/basis/eur_je_ct_neu"), bind("/wenn/preis_strom_ct")),
        bind("/basis/wartung_neu"),
    )
    ersparnis = minus(kosten_alt, kosten_neu)

    b = SurfaceBuilder("stellschrauben", "Was wäre wenn")
    b.root(
        b.column(
            [
                b.heading(
                    "Was wäre wenn",
                    "Rechnen Sie mit Ihren eigenen Preisen",
                    "Niemand kennt die Energiepreise der nächsten zwanzig Jahre – "
                    "auch ich nicht. Stellen Sie ein, was Sie für realistisch "
                    "halten. Die Zahlen unten rechnen sofort mit.",
                ),
                b.card(
                    b.column(
                        [
                            b.text("Ihre Annahmen", variant="h3"),
                            b.slider(
                                label=f"{werte['traeger']}preis in Cent je kWh",
                                value_path="/wenn/preis_alt_ct",
                                minimum=werte["preis_alt_min_ct"],
                                maximum=werte["preis_alt_max_ct"],
                            ),
                            b.slider(
                                label="Strompreis für die Wärmepumpe in Cent je kWh",
                                value_path="/wenn/preis_strom_ct",
                                minimum=werte["preis_strom_min_ct"],
                                maximum=werte["preis_strom_max_ct"],
                            ),
                        ]
                    )
                ),
                b.row(
                    [
                        b.live_stat(
                            label=f"Heute mit {_HEIZUNG_LABEL[profil.heizung]}",
                            value=money(kosten_alt),
                            hint="pro Jahr, mit Wartung",
                        ),
                        b.live_stat(
                            label=f"Mit {fokus.label}",
                            value=money(kosten_neu),
                            hint="pro Jahr, mit Wartung",
                        ),
                        b.live_stat(
                            label="Unterschied",
                            value=money(over(ersparnis, 12)),
                            hint="pro Monat",
                        ),
                        b.live_stat(
                            label="Nach 20 Jahren",
                            value=money(
                                minus(times(ersparnis, 20), bind("/basis/eigenanteil_eur"))
                            ),
                            hint=f"nach Ihrem Eigenanteil von {_euro(werte['eigenanteil_eur'])}",
                        ),
                    ]
                ),
                b.card(
                    b.column(
                        [
                            b.text("Sollen wir so weiterrechnen?", variant="h3"),
                            b.text(
                                "Bisher rechne ich mit den Demo-Preisen. Übernehmen Sie "
                                "Ihre Einstellung, gilt sie für die ganze Beratung – "
                                "Vergleich, Wirtschaftlichkeit und Empfehlung."
                            ),
                            b.button(
                                "Mit diesen Preisen weiterrechnen",
                                event="annahmen_uebernehmen",
                                context={
                                    "preis_alt_ct": bind("/wenn/preis_alt_ct"),
                                    "preis_strom_ct": bind("/wenn/preis_strom_ct"),
                                },
                                variant="primary",
                            ),
                        ]
                    )
                ),
                b.assumptions(
                    [
                        f"Wärmebedarf {de(werte['bedarf_kwh_a'])} kWh/a",
                        f"Daraus {de(werte['kwh_alt'])} kWh {werte['traeger']} heute "
                        f"gegenüber {de(werte['kwh_neu'])} kWh Strom danach",
                        "Die Regler verändern nur die beiden Preise – Bedarf, "
                        "Jahresarbeitszahl und Investition bleiben, wie berechnet.",
                        "Preissteigerungen sind hier bewusst nicht enthalten: Sie "
                        "stellen den Preis ein, der über die Laufzeit im Mittel gelten soll.",
                        dd.DISCLAIMER,
                    ],
                    source=dd.QUELLE_ENERGIE,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish(
        {
            "wenn": {
                "preis_alt_ct": werte["preis_alt_ct"],
                "preis_strom_ct": werte["preis_strom_ct"],
            },
            "basis": {
                "eur_je_ct_alt": werte["eur_je_ct_alt"],
                "eur_je_ct_neu": werte["eur_je_ct_neu"],
                "wartung_alt": werte["wartung_alt"],
                "wartung_neu": werte["wartung_neu"],
                "eigenanteil_eur": werte["eigenanteil_eur"],
            },
        }
    )
