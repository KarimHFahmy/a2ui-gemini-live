"""Composes the Energieberater surfaces.

One function per advisory tool. Nothing here talks to the model and nothing
invents a number — every figure comes out of :mod:`app.domain.energie`.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import energie as calc
from ..texts import Texts
from .builder import SurfaceBuilder, bind, minus, money, over, plus, times
from .surface import Surface


def profil_surface(
    t: Texts, profil: calc.Gebaeudeprofil, offene_punkte: list[str]
) -> Surface:
    """"Zusammenfassung des Verstandenen" — the trust anchor of the session.

    The facts are a `repeat` over the data model rather than fixed components,
    so correcting the agent mid-sentence is a one-message data patch.
    """
    b = SurfaceBuilder("profil", t("profil.eyebrow"), t)

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
        b.text(t("profil.eyebrow"), variant="caption"),
        b.text(t("profil.title"), variant="h3"),
        b.repeat(fakt, "/fakten", direction="horizontal"),
    ]
    if offene_punkte:
        inner.append(b.bullets(offene_punkte, heading=t("block.still_open")))
    inner.append(
        b.text(t("profil.correct_me"), variant="caption")
    )

    b.root(b.card(b.column(inner)))

    bedarf = calc.waermebedarf_kwh_a(profil)
    fakten: list[dict[str, str]] = [
        {
            "label": t("energie.profil.gebaeude"),
            "wert": t(
                "energie.profil.gebaeude_wert",
                baujahr=profil.baujahr,
                flaeche=t.num(profil.wohnflaeche_qm),
            ),
        },
        {
            "label": t("energie.profil.heizung"),
            "wert": t(f"energie.heizung.{profil.heizung}"),
        },
        {
            "label": t("energie.profil.zustand"),
            "wert": t(f"energie.stand.{profil.sanierungsstand}"),
        },
        {
            "label": t("energie.profil.haushalt"),
            "wert": t("energie.profil.haushalt_wert", personen=profil.personen),
        },
        {
            "label": t("energie.profil.bedarf"),
            # Estimated values are marked so the client can correct them.
            "wert": ("~ " if profil.verbrauch_kwh_a is None else "")
            + t("energie.profil.bedarf_wert", bedarf=t.num(bedarf)),
        },
    ]
    if profil.prioritaeten:
        fakten.append(
            {"label": t("energie.profil.prioritaeten"), "wert": ", ".join(profil.prioritaeten)}
        )
    if profil.bedenken:
        fakten.append(
            {"label": t("energie.profil.bedenken"), "wert": ", ".join(profil.bedenken)}
        )

    return b.finish({"fakten": fakten})


def eignung_surface(t: Texts, profil: calc.Gebaeudeprofil) -> Surface:
    """Answers the winter question with the physics, not with reassurance."""
    check = calc.eignung(profil)
    b = SurfaceBuilder("eignung", t("energie.eignung.eyebrow"), t)

    monate = t.list("energie.monate")
    anteile = [0.08, 0.14, 0.19, 0.21, 0.17, 0.13, 0.08]
    bedarf = check["waermebedarf_kwh_a"]
    heizlast = [round(bedarf * anteil) for anteil in anteile]
    # Only a very high flow temperature calls for a booster on the coldest days.
    stab_anteil = 0.10 if check["vorlauftemperatur_c"] >= 65 else 0.0

    serien: list[dict[str, Any]] = [
        {
            "label": t("energie.eignung.serie_wp"),
            "werte": [round(w * (1 - stab_anteil)) for w in heizlast],
        }
    ]
    if stab_anteil:
        serien.append(
            {
                "label": t("energie.eignung.serie_heizstab"),
                "werte": [round(w * stab_anteil) for w in heizlast],
            }
        )

    b.root(
        b.column(
            [
                b.heading(
                    t("energie.eignung.eyebrow"),
                    t("energie.eignung.title", urteil=t(check["urteil"])),
                    t("energie.eignung.subtitle"),
                ),
                b.row(
                    [
                        b.stat_card(
                            title=t("energie.eignung.vorlauf"),
                            metric=f"{check['vorlauftemperatur_c']} °C",
                            metric_label=t("energie.eignung.vorlauf_label"),
                            body=t("energie.eignung.vorlauf_body"),
                            tone="positive" if check["vorlauftemperatur_c"] <= 55 else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("energie.eignung.jaz"),
                            metric=t.num(check["jaz"], decimals=1),
                            metric_label=t("energie.eignung.jaz_label"),
                            body=t(
                                "energie.eignung.jaz_body",
                                jaz=t.num(check["jaz"], decimals=1),
                                strom=t.num(check["strombedarf_kwh_a"]),
                            ),
                            tone="positive" if check["jaz"] >= 3.5 else "neutral",
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("energie.eignung.heizlast"),
                            metric=t.num(check["heizlast_kw"], decimals=1, unit="kW"),
                            metric_label=t("energie.eignung.heizlast_label"),
                            body=t("energie.eignung.heizlast_body"),
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title=t("energie.eignung.chart_title"),
                        subtitle=t(
                            "energie.eignung.chart_sub_stab"
                            if stab_anteil
                            else "energie.eignung.chart_sub_allein"
                        ),
                        chart_type="stackedBar",
                        categories=bind("/monate"),
                        series=bind("/last"),
                        unit="kWh",
                    )
                ),
                b.card(
                    b.bullets(
                        [t(key) for key in check["massnahmen"]],
                        heading=t("energie.eignung.massnahmen"),
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil, t) + [t(key) for key in check["hinweise"]],
                    source=t("data.source.energie"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish({"monate": monate, "last": serien})


def szenarien_surface(
    t: Texts,
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
    b = SurfaceBuilder("szenarien", t("energie.szenarien.eyebrow"), t)

    komfort = {n: t(f"energie.komfort.{n}") for n in range(1, 6)}
    aufwand = {n: t(f"energie.aufwand.{n}") for n in range(1, 6)}

    b.root(
        b.column(
            [
                b.heading(
                    t("energie.szenarien.eyebrow"),
                    t("energie.szenarien.title"),
                    t("energie.szenarien.subtitle"),
                ),
                b.card(
                    b.column(
                        [
                            b.choice(
                                [
                                    (
                                        f"{t(s.label)} · "
                                        + (
                                            t("energie.szenarien.keine_investition")
                                            if s.eigenanteil_eur == 0
                                            else t.euro(s.eigenanteil_eur)
                                        ),
                                        s.id,
                                    )
                                    for s in szenarien
                                ],
                                "/gewaehlt",
                                label=t("energie.szenarien.picker"),
                            ),
                            b.button(
                                t("energie.szenarien.button"),
                                event="szenario_gewaehlt",
                                context={"szenarioId": bind("/gewaehlt")},
                                variant="primary",
                            ),
                        ]
                    )
                ),
                b.card(
                    b.table(
                        title=t("energie.szenarien.table"),
                        columns=bind("/spalten"),
                        rows=bind("/zeilen"),
                        highlight=bind("/gewaehlt"),
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil, t), source=t("data.source.energie"), as_of=t("data.as_of")
                ),
            ]
        )
    )

    return b.finish(
        {
            # ChoicePicker binds a *list* of selected values; the table
            # highlight reads the same path and takes the first entry.
            "gewaehlt": [empfohlen_id],
            "spalten": [{"id": s.id, "label": t(s.label)} for s in szenarien],
            "zeilen": [
                {
                    "label": t("energie.szenarien.row.investition"),
                    "werte": [
                        t("block.dash") if s.investition_eur == 0 else t.euro(s.investition_eur)
                        for s in szenarien
                    ],
                },
                {
                    "label": t("energie.szenarien.row.foerderung"),
                    "werte": [
                        t("block.dash") if s.foerderung_eur == 0 else f"− {t.euro(s.foerderung_eur)}"
                        for s in szenarien
                    ],
                    "akzent": "positive",
                },
                {
                    "label": t("energie.szenarien.row.eigenanteil"),
                    "werte": [t.euro(s.eigenanteil_eur) for s in szenarien],
                    "hervorheben": True,
                },
                {
                    "label": t("energie.szenarien.row.energiekosten"),
                    "werte": [t.euro(s.energiekosten_eur_a) for s in szenarien],
                },
                {
                    "label": t("energie.szenarien.row.co2"),
                    "werte": [t.num(s.co2_kg_a / 1000, decimals=1, unit="t") for s in szenarien],
                },
                {
                    "label": t("energie.szenarien.row.komfort"),
                    "werte": [komfort[s.komfort_score] for s in szenarien],
                },
                {
                    "label": t("energie.szenarien.row.aufwand"),
                    "werte": [aufwand[s.aufwand_score] for s in szenarien],
                },
            ],
        }
    )


def wirtschaftlichkeit_surface(
    t: Texts,
    profil: calc.Gebaeudeprofil,
    szenarien: list[calc.Szenario],
    *,
    fokus_id: str,
) -> Surface:
    """The 20-year curve — where the decision actually flips."""
    verlauf = calc.kostenverlauf(szenarien, t)
    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next((s for s in szenarien if s.id == fokus_id), szenarien[1])
    amort = calc.amortisation(bestand, fokus)

    ersparnis = bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a
    gesamt = next(s["werte"][-1] for s in verlauf["serien"] if s["id"] == "bestand") - next(
        s["werte"][-1] for s in verlauf["serien"] if s["id"] == fokus.id
    )

    if amort["erreichbar"]:
        amort_metric = t("energie.wirtschaft.breakeven_jahre", jahre=amort["jahre"])
        amort_body = t("energie.wirtschaft.breakeven_body", jahre=amort["jahre"])
        amort_tone = "positive" if amort["jahre"] <= 15 else "neutral"
    else:
        amort_metric = t("block.dash")
        amort_body = t("energie.wirtschaft.breakeven_nie")
        amort_tone = "caution"

    b = SurfaceBuilder("wirtschaftlichkeit", t("energie.wirtschaft.eyebrow"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("energie.wirtschaft.eyebrow"),
                    t("energie.wirtschaft.title", szenario=t(fokus.label)),
                    t("energie.wirtschaft.subtitle"),
                ),
                b.card(
                    b.chart(
                        title=t("energie.wirtschaft.chart_title"),
                        subtitle=t("energie.wirtschaft.chart_sub"),
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
                            title=t("energie.wirtschaft.breakeven"),
                            metric=amort_metric,
                            metric_label=t("energie.wirtschaft.breakeven_label"),
                            body=amort_body,
                            tone=amort_tone,
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("energie.wirtschaft.laufend"),
                            metric=f"− {t.euro(ersparnis)}",
                            metric_label=t("energie.wirtschaft.laufend_label"),
                            body=t(
                                "energie.wirtschaft.laufend_body",
                                alt=t.euro(bestand.betriebskosten_eur_a),
                                neu=t.euro(fokus.betriebskosten_eur_a),
                            ),
                            tone="positive" if ersparnis > 0 else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("energie.wirtschaft.gesamt"),
                            metric=t.euro(gesamt),
                            metric_label=t("energie.wirtschaft.gesamt_label"),
                            body=t("energie.wirtschaft.gesamt_body"),
                            tone="positive" if gesamt > 0 else "caution",
                            weight=1,
                        ),
                    ]
                ),
                b.assumptions(
                    calc.annahmen(profil, t), source=t("data.source.energie"), as_of=t("data.as_of")
                ),
            ]
        )
    )

    return b.finish({"kategorien": verlauf["kategorien"], "serien": verlauf["serien"]})


def foerderung_surface(
    t: Texts,
    profil: calc.Gebaeudeprofil,
    szenario: calc.Szenario,
    details: dict[str, Any],
) -> Surface:
    """Funding and the sequence of steps.

    The steps are a `repeat` over the data model: one template component
    renders the whole plan, and the order is data.
    """
    b = SurfaceBuilder("foerderung", t("energie.foerderung.surface"), t)

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

    bausteine = [
        f"{t(item['label'])}: {t.pct(item['satz'])}" for item in details["bausteine"]
    ]
    if details["gedeckelt"]:
        bausteine.append(
            t(
                "energie.foerderung.deckel",
                max=t.pct(dd.FOERDERUNG["max_satz"]),
                roh=t.pct(details["satz_ungedeckelt"]),
            )
        )

    b.root(
        b.column(
            [
                b.heading(
                    t("energie.foerderung.eyebrow"),
                    t("energie.foerderung.title"),
                    t("energie.foerderung.subtitle"),
                ),
                b.row(
                    [
                        b.stat_card(
                            title=t("energie.foerderung.zuschuss"),
                            metric=t.euro(details["betrag_eur"]),
                            metric_label=t(
                                "energie.foerderung.quote", satz=t.pct(details["satz"])
                            ),
                            body=t(
                                "energie.foerderung.zuschuss_body",
                                kosten=t.euro(details["foerderfaehige_kosten_eur"]),
                                eigenanteil=t.euro(szenario.eigenanteil_eur),
                            ),
                            tone="positive",
                            weight=1,
                        ),
                        b.card(
                            b.bullets(bausteine, heading=t("energie.foerderung.bausteine")),
                            weight=1,
                        ),
                    ]
                ),
                b.text(t("energie.foerderung.plan"), variant="h3"),
                b.repeat(schritt, "/schritte"),
                b.assumptions(
                    [
                        t("data.foerderung.hinweis"),
                        *t.list("energie.foerderung.assumptions"),
                        t("data.disclaimer"),
                    ],
                    source=t("data.source.energie"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish(
        {
            # Title, detail and duration are one catalog entry split on `|`:
            # the three parts of a step belong together in a translation, and
            # three parallel lists is how they drift apart.
            "schritte": [
                dict(zip(("titel", "detail", "dauer"), schritt.split("|")))
                for schritt in t.list("energie.schritte")
            ]
        }
    )


def stellschrauben_surface(
    t: Texts,
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

    b = SurfaceBuilder("stellschrauben", t("energie.wenn.surface"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("energie.wenn.surface"),
                    t("energie.wenn.title"),
                    t("energie.wenn.subtitle"),
                ),
                b.card(
                    b.column(
                        [
                            b.text(t("energie.wenn.annahmen"), variant="h3"),
                            b.slider(
                                label=t.upper_first(
                                    t(
                                        "energie.wenn.regler_alt",
                                        traeger=t(f"energie.traeger.{werte['traeger']}"),
                                    )
                                ),
                                value_path="/wenn/preis_alt_ct",
                                minimum=werte["preis_alt_min_ct"],
                                maximum=werte["preis_alt_max_ct"],
                            ),
                            b.slider(
                                label=t("energie.wenn.regler_strom"),
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
                            label=t(
                                "energie.wenn.heute",
                                heizung=t(f"energie.heizung.{profil.heizung}"),
                            ),
                            value=money(kosten_alt),
                            hint=t("energie.wenn.pro_jahr_wartung"),
                        ),
                        b.live_stat(
                            label=t("energie.wenn.danach", szenario=t(fokus.label)),
                            value=money(kosten_neu),
                            hint=t("energie.wenn.pro_jahr_wartung"),
                        ),
                        b.live_stat(
                            label=t("energie.wenn.unterschied"),
                            value=money(over(ersparnis, 12)),
                            hint=t("energie.wenn.pro_monat"),
                        ),
                        b.live_stat(
                            label=t("energie.wenn.nach_20"),
                            value=money(
                                minus(times(ersparnis, 20), bind("/basis/eigenanteil_eur"))
                            ),
                            hint=t(
                                "energie.wenn.nach_eigenanteil",
                                eigenanteil=t.euro(werte["eigenanteil_eur"]),
                            ),
                        ),
                    ]
                ),
                b.card(
                    b.column(
                        [
                            b.text(t("energie.wenn.uebernehmen_title"), variant="h3"),
                            b.text(t("energie.wenn.uebernehmen_body")),
                            b.button(
                                t("energie.wenn.uebernehmen_button"),
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
                        *t.list(
                            "energie.wenn.assumptions",
                            bedarf=t.num(werte["bedarf_kwh_a"]),
                            alt=t.num(werte["kwh_alt"]),
                            neu=t.num(werte["kwh_neu"]),
                            traeger=t(f"energie.traeger.{werte['traeger']}"),
                        ),
                        t("data.disclaimer"),
                    ],
                    source=t("data.source.energie"),
                    as_of=t("data.as_of"),
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
