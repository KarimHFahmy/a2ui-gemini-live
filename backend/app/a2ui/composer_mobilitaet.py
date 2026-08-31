"""Composes the Autoberater surfaces.

The order of the surfaces is the argument: does it fit your week, where do you
charge, which car, what does it cost. Charging comes before the vehicle because
it is the larger cost lever.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import mobilitaet as calc
from ..texts import Texts
from .builder import SurfaceBuilder, bind, minus, money, number, over, plus, times
from .surface import Surface


def profil_surface(
    t: Texts, profil: calc.Mobilitaetsprofil, offene_punkte: list[str]
) -> Surface:
    """"Zusammenfassung des Verstandenen" for the mobility journey."""
    b = SurfaceBuilder("profil", t("mob.profil.eyebrow"), t)

    fakt = b.column([b.text(bind("label"), variant="caption"), b.text(bind("wert"))])

    # Pinned for the whole session — see the note in composer_energie.
    inner = [
        b.text(t("mob.profil.eyebrow"), variant="caption"),
        b.text(t("profil.title"), variant="h3"),
        b.repeat(fakt, "/fakten", direction="horizontal"),
    ]
    if offene_punkte:
        inner.append(b.bullets(offene_punkte, heading=t("block.still_open")))
    inner.append(
        b.text(t("mob.profil.correct_me"), variant="caption")
    )

    b.root(b.card(b.column(inner)))

    fakten: list[dict[str, str]] = [
        {
            "label": t("mob.profil.taeglich"),
            "wert": t(
                "mob.profil.taeglich_wert",
                km=t.num(profil.taeglich_km),
                tage=profil.pendeltage_pro_woche,
            ),
        },
        {
            "label": t("mob.profil.langstrecke"),
            "wert": t(
                "mob.profil.langstrecke_wert",
                mal=profil.langstrecken_pro_monat,
                km=t.num(profil.langstrecke_km),
            ),
        },
        {
            "label": t("mob.profil.laden"),
            "wert": t(f"mob.lade.{profil.lademoeglichkeit}"),
        },
        {
            "label": t("mob.profil.jahr"),
            "wert": "~ " + t.num(profil.jahresfahrleistung_km(), unit="km"),
        },
        {
            "label": t("mob.profil.wunsch"),
            "wert": dd.FAHRZEUG_KLASSEN[profil.fahrzeugklasse]["label"],
        },
    ]
    if profil.budget_eur_monat:
        fakten.append(
            {
                "label": t("mob.profil.budget"),
                "wert": t("mob.profil.budget_wert", budget=t.euro(profil.budget_eur_monat)),
            }
        )
    if profil.bedenken:
        fakten.append(
            {"label": t("mob.profil.bedenken"), "wert": ", ".join(profil.bedenken)}
        )

    return b.finish({"fakten": fakten})


def alltag_surface(t: Texts, profil: calc.Mobilitaetsprofil) -> Surface:
    """"Ist ein E-Auto praktikabel für mich?" answered with their own week."""
    r = calc.reichweite(profil)
    woche = calc.wochenprofil(profil, t)
    ls = calc.langstrecke(profil, t)
    puffer = r["puffer_faktor_winter"]

    if puffer >= 3:
        tone, metric = "positive", f"{t.num(puffer)}×"
        body = t(
            "mob.alltag.puffer_gut",
            km=t.num(profil.taeglich_km),
            laden=_ladehaeufigkeit(t, profil, r),
        )
    elif puffer >= 1.5:
        tone, metric = "neutral", f"{t.num(puffer, decimals=1)}×"
        body = t("mob.alltag.puffer_ok", laden=_ladehaeufigkeit(t, profil, r))
    else:
        tone, metric = "caution", f"{t.num(puffer, decimals=1)}×"
        body = t("mob.alltag.puffer_knapp")

    b = SurfaceBuilder("alltag", t("mob.alltag.eyebrow"), t)

    stopp = b.card(
        b.column(
            [
                b.row(
                    [b.text(bind("titel"), weight=1), b.text(bind("dauer"), variant="caption")],
                    align="center",
                ),
                b.text(bind("detail"), variant="body"),
            ]
        )
    )

    b.root(
        b.column(
            [
                b.heading(
                    t("mob.alltag.eyebrow"),
                    t("mob.alltag.title"),
                    t("mob.alltag.subtitle"),
                ),
                b.row(
                    [
                        b.stat_card(
                            title=t("mob.alltag.puffer"),
                            metric=metric,
                            metric_label=t("mob.alltag.puffer_label"),
                            body=body,
                            tone=tone,
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("mob.alltag.winter"),
                            metric=t.num(r["reichweite_winter_km"], unit="km"),
                            metric_label=t(
                                "mob.alltag.winter_label",
                                fahrzeug=r["fahrzeug"],
                                batterie=t.num(r["batterie_kwh"]),
                            ),
                            body=t(
                                "mob.alltag.winter_body",
                                verbrauch=t.num(r["verbrauch_winter"], decimals=1),
                                sommer=t.num(r["reichweite_sommer_km"]),
                            ),
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("mob.alltag.autobahn"),
                            metric=t.num(r["reichweite_autobahn_winter_km"], unit="km"),
                            metric_label=t(
                                "mob.alltag.autobahn_label",
                                verbrauch=t.num(r["verbrauch_autobahn_winter"], decimals=1),
                            ),
                            body=t("mob.alltag.autobahn_body"),
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title=t("mob.alltag.chart_title"),
                        subtitle=t("mob.alltag.chart_sub"),
                        chart_type="bar",
                        categories=bind("/tage"),
                        series=bind("/woche"),
                        unit="km",
                    )
                ),
                b.heading(
                    t("mob.ls.eyebrow"),
                    t("mob.ls.title", km=t.num(profil.langstrecke_km)),
                    t(
                        "mob.ls.subtitle",
                        stopps=ls["ladestopps"],
                        minuten=ls["mehrzeit_min"],
                    )
                    if ls["ladestopps"]
                    else t("mob.ls.ohne_stopp"),
                ),
                b.repeat(stopp, "/langstrecke"),
                b.assumptions(
                    calc.annahmen(profil, t), source=t("data.source.mobilitaet"), as_of=t("data.as_of")
                ),
            ]
        )
    )

    return b.finish(
        {
            "tage": woche["kategorien"],
            "woche": woche["serien"],
            "langstrecke": [
                {
                    "titel": f"**{schritt['titel']}**",
                    "detail": schritt["detail"],
                    "dauer": schritt["dauer"],
                }
                for schritt in ls["schritte"]
            ],
        }
    )


def _ladehaeufigkeit(t: Texts, profil: calc.Mobilitaetsprofil, r: dict[str, Any]) -> str:
    tage = r["reichweite_winter_km"] / max(profil.taeglich_km, 1.0)
    if tage >= 7:
        return t("mob.alltag.laden_woche")
    if tage >= 3:
        return t("mob.alltag.laden_tage", tage=int(tage))
    return t("mob.alltag.laden_zwei")


def laden_surface(t: Texts, profil: calc.Mobilitaetsprofil) -> Surface:
    """Where you charge decides the economics — shown before the car choice."""
    lade = calc.ladeoptionen(profil, t)
    optionen = lade["optionen"]
    aktuell = next(o for o in optionen if o["id"] == lade["aktuell_id"])
    beste = next(o for o in optionen if o["id"] == lade["beste_id"])
    ersparnis = lade["ersparnis_beste_eur_a"]

    if ersparnis > 200:
        hebel_body = t(
            "mob.laden.hebel_body",
            aktuell=aktuell["label"],
            beste=beste["label"],
            betrag=t.euro(ersparnis),
        )
        hebel_tone = "positive"
    else:
        hebel_body = t("mob.laden.hebel_schon_gut")
        hebel_tone = "neutral"

    b = SurfaceBuilder("laden", t("mob.laden.surface"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("mob.laden.eyebrow"),
                    t("mob.laden.title"),
                    t("mob.laden.subtitle"),
                ),
                b.stat_card(
                    title=t("mob.laden.hebel"),
                    metric=t.euro(ersparnis) if ersparnis > 0 else t("block.dash"),
                    metric_label=t("mob.laden.hebel_label"),
                    body=hebel_body,
                    tone=hebel_tone,
                ),
                b.card(
                    b.table(
                        title=t("mob.laden.table"),
                        columns=bind("/spalten"),
                        rows=bind("/zeilen"),
                        highlight=bind("/beste"),
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil, t)
                    + [t("mob.laden.bedarf", kwh=t.num(lade["jahres_kwh"]))],
                    source=t("data.source.mobilitaet"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish(
        {
            "beste": lade["beste_id"],
            "spalten": [{"id": o["id"], "label": o["label"]} for o in optionen],
            "zeilen": [
                {
                    "label": t("mob.laden.row.mischpreis"),
                    "werte": [
                        t.num(o["mischpreis_eur_kwh"], decimals=2) + " €/kWh"
                        for o in optionen
                    ],
                },
                {
                    "label": t("mob.laden.row.kosten_a"),
                    "werte": [t.euro(o["kosten_eur_a"]) for o in optionen],
                    "hervorheben": True,
                },
                {
                    "label": t("mob.laden.row.kosten_100"),
                    "werte": [t.euro(o["kosten_eur_100km"], decimals=2) for o in optionen],
                },
                {
                    "label": t("mob.laden.row.invest"),
                    "werte": [
                        t("block.dash") if o["investition_eur"] == 0 else t.euro(o["investition_eur"])
                        for o in optionen
                    ],
                },
                {
                    "label": t("mob.laden.row.verfuegbar"),
                    "werte": [
                        t("mob.ja") if o["verfuegbar"] else t("mob.nein") for o in optionen
                    ],
                },
            ],
        }
    )


def fahrzeuge_surface(t: Texts, profil: calc.Mobilitaetsprofil) -> Surface:
    """Ranked classes with the trade-offs shown, not hidden.

    A single template rendered once per suggestion — adding a class is a data
    change, not a layout change.
    """
    vorschlaege = calc.fahrzeugvorschlaege(profil, t)
    b = SurfaceBuilder("fahrzeuge", t("mob.fahrzeuge.surface"), t)

    vorschlag = b.card(
        b.column(
            [
                b.row(
                    [
                        b.text(bind("titel"), variant="h4", weight=1),
                        b.text(bind("passung"), variant="caption"),
                    ],
                    align="center",
                ),
                b.text(bind("kennzahlen"), variant="body"),
                b.row(
                    [
                        b.text(bind("pro"), weight=1),
                        b.text(bind("contra"), weight=1),
                    ]
                ),
            ]
        )
    )

    b.root(
        b.column(
            [
                b.heading(
                    t("mob.fahrzeuge.eyebrow"),
                    t("mob.fahrzeuge.title"),
                    t("mob.fahrzeuge.subtitle"),
                ),
                b.repeat(vorschlag, "/vorschlaege"),
                b.assumptions(
                    calc.annahmen(profil, t)
                    + t.list("mob.fahrzeuge.assumptions"),
                    source=t("data.source.mobilitaet"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish(
        {
            "vorschlaege": [
                {
                    "titel": f"{index + 1}. {v['label']}",
                    "passung": t("mob.fahrzeuge.passung", score=v["score"]),
                    "kennzahlen": t(
                        "mob.fahrzeuge.kennzahlen",
                        batterie=t.num(v["batterie_kwh"]),
                        winter=t.num(v["reichweite_winter_km"]),
                        stopps=v["ladestopps_langstrecke"],
                        rate=t.euro(v["leasing_eur_monat"]),
                    ),
                    "pro": t("mob.fahrzeuge.pro")
                    + "\n"
                    + "\n".join(f"- {item}" for item in v["pro"]),
                    "contra": t("mob.fahrzeuge.contra")
                    + "\n"
                    + "\n".join(f"- {item}" for item in v["contra"]),
                }
                for index, v in enumerate(vorschlaege)
            ]
        }
    )


def _energie_tone(elektro_eur_100km: float, verbrenner_eur_100km: float) -> str:
    """Whether the energy cost is genuinely an advantage, or just a wash.

    Two cents apart over 100 km is a tie, and a tie should not be coloured as a
    win — 11,37 € against 11,39 € is exactly the case this demo is built to be
    honest about. A tenth of the fuel cost is the smallest gap worth a claim.
    """
    if elektro_eur_100km > verbrenner_eur_100km:
        return "caution"
    if verbrenner_eur_100km - elektro_eur_100km >= verbrenner_eur_100km * 0.1:
        return "positive"
    return "neutral"


def kosten_surface(t: Texts, profil: calc.Mobilitaetsprofil) -> Surface:
    """Total cost of ownership, itemised so nothing hides in a total."""
    k = calc.kostenvergleich(profil, t)
    diff = k["differenz_eur"]
    guenstiger = diff > 0

    b = SurfaceBuilder("kosten", t("mob.kosten.surface"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("mob.kosten.eyebrow"),
                    t("mob.kosten.title", jahre=k["haltedauer_jahre"]),
                    t("mob.kosten.subtitle"),
                ),
                b.row(
                    [
                        b.stat_card(
                            title=t("mob.kosten.vergleich"),
                            metric=t.euro(abs(diff)),
                            metric_label=t(
                                "mob.kosten.vorteil" if guenstiger else "mob.kosten.nachteil"
                            ),
                            body=t(
                                "mob.kosten.guenstiger_body"
                                if guenstiger
                                else "mob.kosten.teurer_body",
                                monat=t.euro(abs(k["differenz_eur_monat"])),
                            ),
                            tone="positive" if guenstiger else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("mob.kosten.energie"),
                            metric=t.euro(k["energie_elektro_eur_100km"], decimals=2),
                            metric_label=t("mob.kosten.energie_label"),
                            body=t(
                                "mob.kosten.energie_body",
                                strom=t.euro(k["energie_elektro_eur_100km"], decimals=2),
                                sprit=t.euro(k["energie_verbrenner_eur_100km"], decimals=2),
                            ),
                            tone=_energie_tone(
                                k["energie_elektro_eur_100km"],
                                k["energie_verbrenner_eur_100km"],
                            ),
                            weight=1,
                        ),
                        b.stat_card(
                            title=t("mob.kosten.co2"),
                            metric="− "
                            + t.num(k["co2_ersparnis_kg_a"] / 1000, decimals=1, unit="t"),
                            metric_label=t("mob.kosten.co2_label"),
                            body=t("mob.kosten.co2_body"),
                            tone="positive",
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title=t("mob.kosten.chart_title"),
                        subtitle=t(
                            "mob.kosten.chart_sub",
                            jahre=k["haltedauer_jahre"],
                            km=t.num(k["jahres_km"]),
                        ),
                        chart_type="groupedBar",
                        categories=bind("/kategorien"),
                        series=bind("/serien"),
                        unit="€",
                        value_format="currency",
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil, t)
                    + t.list(
                        "mob.kosten.assumptions",
                        elektro=t.euro(k["gesamt_elektro_eur"]),
                        verbrenner=t.euro(k["gesamt_verbrenner_eur"]),
                    ),
                    source=t("data.source.mobilitaet"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish({"kategorien": k["kategorien"], "serien": k["serien"]})


def stellschrauben_surface(t: Texts, profil: calc.Mobilitaetsprofil) -> Surface:
    """„Was wäre wenn?“ — die zwei Zahlen, bei denen jeder Kunde schätzt.

    „So um die fünfzig Kilometer“ und „meistens zu Hause, manchmal unterwegs“
    sind die ehrlichen Antworten im Erstgespräch – und beide entscheiden über
    die Kosten. Statt sie festzuschreiben, gibt die Beratung die Regler heraus.

    Die Zahlen darunter rechnen im Browser mit, ohne Umweg über den Agenten —
    aus Koeffizienten, die :func:`app.domain.mobilitaet.stellschrauben`
    geliefert hat. Erst der Knopf macht die Einstellung für alles Weitere gültig.
    """
    werte = calc.stellschrauben(profil)

    # Die Rechnung, wie sie im Browser steht. Jede Zeile liest die Regler und
    # rechnet neu, sobald sich einer bewegt.
    jahres_km = plus(
        times(bind("/wenn/taeglich_km"), bind("/basis/tage_pro_jahr")),
        bind("/basis/km_konstante"),
    )
    preis_ct = plus(
        bind("/basis/preis_unterwegs_ct"),
        times(bind("/wenn/anteil_zuhause"), bind("/basis/delta_je_prozent")),
    )
    strom_eur = times(jahres_km, times(preis_ct, bind("/basis/strom_eur_je_km_je_ct")))
    kraftstoff_eur = times(jahres_km, bind("/basis/kraftstoff_eur_je_km"))

    b = SurfaceBuilder("stellschrauben", t("mob.wenn.surface"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("mob.wenn.surface"),
                    t("mob.wenn.title"),
                    t("mob.wenn.subtitle"),
                ),
                b.card(
                    b.column(
                        [
                            b.text(t("mob.wenn.einstellung"), variant="h3"),
                            b.slider(
                                label=t("mob.wenn.regler_km"),
                                value_path="/wenn/taeglich_km",
                                minimum=werte["taeglich_km_min"],
                                maximum=werte["taeglich_km_max"],
                            ),
                            b.slider(
                                label=t("mob.wenn.regler_zuhause"),
                                value_path="/wenn/anteil_zuhause",
                                minimum=0,
                                maximum=100,
                            ),
                            b.text(
                                t(
                                    "mob.wenn.preise",
                                    zuhause=t.num(werte["preis_zuhause_ct"] / 100, decimals=2),
                                    unterwegs=t.num(
                                        werte["preis_unterwegs_ct"] / 100, decimals=2
                                    ),
                                ),
                                variant="caption",
                            ),
                        ]
                    )
                ),
                b.row(
                    [
                        b.live_stat(
                            # Die Einheit steht im Label, damit die Zahl selbst
                            # dieselbe Rechnung bleibt, die auch die Kosten speist.
                            label=t("mob.wenn.km_jahr"),
                            value=number(jahres_km),
                            hint=t("mob.wenn.km_jahr_hint"),
                        ),
                        b.live_stat(
                            label=t("mob.wenn.strom"),
                            value=money(strom_eur),
                            hint=t("mob.wenn.pro_jahr"),
                        ),
                        b.live_stat(
                            label=t.upper_first(
                                t(
                                    "mob.wenn.kraftstoff",
                                    kraftstoff=t(f"mob.kraftstoff.{werte['kraftstoff']}"),
                                )
                            ),
                            value=money(kraftstoff_eur),
                            hint=t("mob.wenn.kraftstoff_hint"),
                        ),
                        b.live_stat(
                            label=t("mob.wenn.unterschied"),
                            value=money(over(minus(kraftstoff_eur, strom_eur), 12)),
                            hint=t("mob.wenn.unterschied_hint"),
                        ),
                    ]
                ),
                b.card(
                    b.column(
                        [
                            b.text(t("mob.wenn.uebernehmen_title"), variant="h3"),
                            b.text(t("mob.wenn.uebernehmen_body")),
                            b.button(
                                t("mob.wenn.uebernehmen_button"),
                                event="annahmen_uebernehmen",
                                context={
                                    "taeglich_km": bind("/wenn/taeglich_km"),
                                    "anteil_zuhause": bind("/wenn/anteil_zuhause"),
                                },
                                variant="primary",
                            ),
                        ]
                    )
                ),
                b.assumptions(
                    [
                        *t.list(
                            "mob.wenn.assumptions",
                            fahrzeug=werte["fahrzeug"],
                            verbrauch=t.num(werte["verbrauch_kwh_100km"], decimals=1),
                            liter=t.num(werte["verbrauch_l_100km"], decimals=1),
                            kraftstoff=t(f"mob.kraftstoff.{werte['kraftstoff']}"),
                            km=t.num(werte["km_konstante"]),
                        ),
                        t("data.disclaimer"),
                    ],
                    source=t("data.source.mobilitaet"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish(
        {
            "wenn": {
                "taeglich_km": werte["taeglich_km"],
                "anteil_zuhause": werte["anteil_zuhause"],
            },
            "basis": {
                "tage_pro_jahr": werte["tage_pro_jahr"],
                "km_konstante": werte["km_konstante"],
                "preis_unterwegs_ct": werte["preis_unterwegs_ct"],
                "delta_je_prozent": werte["delta_je_prozent"],
                "strom_eur_je_km_je_ct": werte["strom_eur_je_km_je_ct"],
                "kraftstoff_eur_je_km": werte["kraftstoff_eur_je_km"],
            },
        }
    )
