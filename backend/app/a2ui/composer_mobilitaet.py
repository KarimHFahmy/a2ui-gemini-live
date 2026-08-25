"""Composes the Autoberater surfaces.

The order of the surfaces is the argument: does it fit your week, where do you
charge, which car, what does it cost. Charging comes before the vehicle because
it is the larger cost lever.
"""

from __future__ import annotations

from typing import Any

from ..domain import demo_data as dd
from ..domain import mobilitaet as calc
from .builder import SurfaceBuilder, bind, minus, money, number, over, plus, times
from .surface import Surface

_LADE_LABEL = {
    "wallbox_zuhause": "Wallbox zu Hause",
    "steckdose_zuhause": "Haushaltssteckdose",
    "arbeitsplatz": "Laden beim Arbeitgeber",
    "nur_oeffentlich": "Nur öffentlich",
}


def _euro(value: float) -> str:
    return f"{value:,.0f} €".replace(",", ".")


def _komma(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def profil_surface(profil: calc.Mobilitaetsprofil, offene_punkte: list[str]) -> Surface:
    """"Zusammenfassung des Verstandenen" for the mobility journey."""
    b = SurfaceBuilder("profil", "Ihr Alltag")

    fakt = b.column([b.text(bind("label"), variant="caption"), b.text(bind("wert"))])

    # Pinned for the whole session — see the note in composer_energie.
    inner = [
        b.text("Ihr Alltag", variant="caption"),
        b.text("Das habe ich verstanden", variant="h3"),
        b.repeat(fakt, "/fakten", direction="horizontal"),
    ]
    if offene_punkte:
        inner.append(b.bullets(offene_punkte, heading="Noch offen"))
    inner.append(
        b.text(
            "Korrigieren Sie mich jederzeit – ich rechne sofort neu.",
            variant="caption",
        )
    )

    b.root(b.card(b.column(inner)))

    fakten: list[dict[str, str]] = [
        {
            "label": "Täglich",
            "wert": f"{profil.taeglich_km:.0f} km an {profil.pendeltage_pro_woche} Tagen",
        },
        {
            "label": "Langstrecke",
            "wert": f"{profil.langstrecken_pro_monat}× im Monat, ~ {profil.langstrecke_km:.0f} km",
        },
        {"label": "Laden", "wert": _LADE_LABEL[profil.lademoeglichkeit]},
        {
            "label": "Im Jahr",
            "wert": f"~ {profil.jahresfahrleistung_km():,.0f} km".replace(",", "."),
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

    return b.finish({"fakten": fakten})


def alltag_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """"Ist ein E-Auto praktikabel für mich?" answered with their own week."""
    r = calc.reichweite(profil)
    woche = calc.wochenprofil(profil)
    ls = calc.langstrecke(profil)
    puffer = r["puffer_faktor_winter"]

    if puffer >= 3:
        tone, metric = "positive", f"{puffer:.0f}×"
        body = (
            f"Ihre {profil.taeglich_km:.0f} km am Tag sind selbst im Winter kein "
            f"Thema. Sie laden etwa {_ladehaeufigkeit(profil, r)}."
        )
    elif puffer >= 1.5:
        tone, metric = "neutral", f"{_komma(puffer, 1)}×"
        body = (
            f"Ihre Tagesstrecke passt, im Winter bleibt ein solider Puffer. "
            f"Sie laden etwa {_ladehaeufigkeit(profil, r)}."
        )
    else:
        tone, metric = "caution", f"{_komma(puffer, 1)}×"
        body = (
            "Im Winter wird es knapp – Sie müssten nahezu täglich laden. Eine "
            "größere Batterie oder eine verlässliche Lademöglichkeit ist hier wichtig."
        )

    b = SurfaceBuilder("alltag", "Alltagstauglichkeit")

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
                    "Alltagstauglichkeit",
                    "Ihre Woche mit einem E-Auto",
                    "Nicht der Katalogwert zählt, sondern die Reichweite an einem "
                    "kalten Januarmorgen.",
                ),
                b.row(
                    [
                        b.stat_card(
                            title="Puffer im Alltag",
                            metric=metric,
                            metric_label="Ihres Tagesbedarfs",
                            body=body,
                            tone=tone,
                            weight=1,
                        ),
                        b.stat_card(
                            title="Reichweite im Winter",
                            metric=f"{r['reichweite_winter_km']} km",
                            metric_label=f"{r['fahrzeug']}, {r['batterie_kwh']:.0f} kWh",
                            body=f"Bei Kälte steigt der Verbrauch auf "
                            f"{_komma(r['verbrauch_winter'], 1)} kWh/100 km. Im Sommer "
                            f"sind es {r['reichweite_sommer_km']} km.",
                            weight=1,
                        ),
                        b.stat_card(
                            title="Autobahn im Winter",
                            metric=f"{r['reichweite_autobahn_winter_km']} km",
                            metric_label=f"{_komma(r['verbrauch_autobahn_winter'], 1)} kWh/100 km",
                            body="Der ehrlichste Wert: kalt, bei Richtgeschwindigkeit. "
                            "Danach planen sich Langstrecken zuverlässig.",
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title="Ihre typische Woche",
                        subtitle="Die Linie ist die Winterreichweite. Solange die "
                        "Balken darunter bleiben, kommen Sie ohne Zwischenladen aus.",
                        chart_type="bar",
                        categories=bind("/tage"),
                        series=bind("/woche"),
                        unit="km",
                    )
                ),
                b.heading(
                    "Langstrecke",
                    f"Ihre {profil.langstrecke_km:.0f}-km-Fahrt konkret",
                    f"{ls['ladestopps']} Ladestopp(s), zusammen {ls['mehrzeit_min']} "
                    "Minuten mehr als mit einem Verbrenner."
                    if ls["ladestopps"]
                    else "Ohne Ladestopp erreichbar.",
                ),
                b.repeat(stopp, "/langstrecke"),
                b.assumptions(
                    calc.annahmen(profil), source=dd.QUELLE_MOBILITAET, as_of=dd.STAND
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


def _ladehaeufigkeit(profil: calc.Mobilitaetsprofil, r: dict[str, Any]) -> str:
    tage = r["reichweite_winter_km"] / max(profil.taeglich_km, 1.0)
    if tage >= 7:
        return "einmal pro Woche"
    if tage >= 3:
        return f"alle {int(tage)} Tage"
    return "alle zwei Tage"


def laden_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Where you charge decides the economics — shown before the car choice."""
    lade = calc.ladeoptionen(profil)
    optionen = lade["optionen"]
    aktuell = next(o for o in optionen if o["id"] == lade["aktuell_id"])
    beste = next(o for o in optionen if o["id"] == lade["beste_id"])
    ersparnis = lade["ersparnis_beste_eur_a"]

    if ersparnis > 200:
        hebel_body = (
            f"Der Wechsel von „{aktuell['label']}“ zu „{beste['label']}“ spart Ihnen "
            f"rund {_euro(ersparnis)} im Jahr – mehr als die meisten "
            "Fahrzeugentscheidungen ausmachen."
        )
        hebel_tone = "positive"
    else:
        hebel_body = (
            "Ihre Ladesituation ist bereits gut. Die Fahrzeugwahl ist bei Ihnen "
            "der größere Hebel."
        )
        hebel_tone = "neutral"

    b = SurfaceBuilder("laden", "Ladelösungen")
    b.root(
        b.column(
            [
                b.heading(
                    "Laden",
                    "Wo Sie laden, entscheidet über die Kosten",
                    "Zwischen der günstigsten und der teuersten Ladeart liegt bei "
                    "Ihrer Fahrleistung ein Vielfaches der Fahrzeugunterschiede.",
                ),
                b.stat_card(
                    title="Ihr größter Hebel",
                    metric=_euro(ersparnis) if ersparnis > 0 else "–",
                    metric_label="Ersparnis pro Jahr",
                    body=hebel_body,
                    tone=hebel_tone,
                ),
                b.card(
                    b.table(
                        title="Ladeoptionen im Vergleich",
                        columns=bind("/spalten"),
                        rows=bind("/zeilen"),
                        highlight=bind("/beste"),
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil)
                    + [f"Jahresenergiebedarf rund {lade['jahres_kwh']:,.0f} kWh".replace(",", ".")],
                    source=dd.QUELLE_MOBILITAET,
                    as_of=dd.STAND,
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
                    "label": "Mischpreis",
                    "werte": [f"{_komma(o['mischpreis_eur_kwh'])} €/kWh" for o in optionen],
                },
                {
                    "label": "Energiekosten pro Jahr",
                    "werte": [_euro(o["kosten_eur_a"]) for o in optionen],
                    "hervorheben": True,
                },
                {
                    "label": "Kosten je 100 km",
                    "werte": [f"{_komma(o['kosten_eur_100km'])} €" for o in optionen],
                },
                {
                    "label": "Einmalige Investition",
                    "werte": ["–" if o["investition_eur"] == 0 else _euro(o["investition_eur"]) for o in optionen],
                },
                {
                    "label": "Für Sie verfügbar",
                    "werte": ["ja" if o["verfuegbar"] else "nein" for o in optionen],
                },
            ],
        }
    )


def fahrzeuge_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Ranked classes with the trade-offs shown, not hidden.

    A single template rendered once per suggestion — adding a class is a data
    change, not a layout change.
    """
    vorschlaege = calc.fahrzeugvorschlaege(profil)
    b = SurfaceBuilder("fahrzeuge", "Fahrzeugvorschläge")

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
                    "Fahrzeugwahl",
                    "Diese Klassen passen zu Ihrem Alltag",
                    "Sortiert nach Passung zu Ihrem Profil, nicht nach Reichweite "
                    "oder Preis allein.",
                ),
                b.repeat(vorschlag, "/vorschlaege"),
                b.assumptions(
                    calc.annahmen(profil)
                    + [
                        "Passung berücksichtigt Winterreichweite, Ladestopps, Budget "
                        "und Ihre Fahrzeugklasse.",
                        "Generische Fahrzeugklassen statt konkreter Modelle – bewusst "
                        "herstellerneutral.",
                    ],
                    source=dd.QUELLE_MOBILITAET,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish(
        {
            "vorschlaege": [
                {
                    "titel": f"{index + 1}. {v['label']}",
                    "passung": f"Passung {v['score']}/100",
                    "kennzahlen": (
                        f"{v['batterie_kwh']:.0f} kWh · {v['reichweite_winter_km']} km im "
                        f"Winter · {v['ladestopps_langstrecke']} Ladestopp(s) · ab "
                        f"{v['leasing_eur_monat']:.0f} €/Monat"
                    ),
                    "pro": "**Dafür spricht**\n"
                    + "\n".join(f"- {item}" for item in v["pro"]),
                    "contra": "**Zu bedenken**\n"
                    + "\n".join(f"- {item}" for item in v["contra"]),
                }
                for index, v in enumerate(vorschlaege)
            ]
        }
    )


def kosten_surface(profil: calc.Mobilitaetsprofil) -> Surface:
    """Total cost of ownership, itemised so nothing hides in a total."""
    k = calc.kostenvergleich(profil)
    diff = k["differenz_eur"]
    guenstiger = diff > 0

    b = SurfaceBuilder("kosten", "Kostenvergleich")
    b.root(
        b.column(
            [
                b.heading(
                    "Kosten",
                    f"Über {k['haltedauer_jahre']} Jahre gerechnet",
                    "Alle Posten einzeln – Wertverlust, Energie, Wartung, "
                    "Versicherung, Steuer und THG-Quote.",
                ),
                b.row(
                    [
                        b.stat_card(
                            title="Elektro gegen Verbrenner",
                            metric=_euro(abs(diff)),
                            metric_label="Vorteil Elektro" if guenstiger else "Nachteil Elektro",
                            body=(
                                f"Das E-Auto ist bei Ihrem Profil insgesamt günstiger – "
                                f"das entspricht {abs(k['differenz_eur_monat'])} € im Monat."
                                if guenstiger
                                else (
                                    f"Mit Ihrer heutigen Ladesituation ist das E-Auto "
                                    f"insgesamt teurer – rund {abs(k['differenz_eur_monat'])} € "
                                    "im Monat. Mit einer eigenen Lademöglichkeit dreht "
                                    "sich das Bild."
                                )
                            ),
                            tone="positive" if guenstiger else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title="Energie je 100 km",
                            metric=f"{_komma(k['energie_elektro_eur_100km'])} €",
                            metric_label="elektrisch, je 100 km",
                            body=f"Strom {_komma(k['energie_elektro_eur_100km'])} € "
                            f"gegenüber Kraftstoff {_komma(k['energie_verbrenner_eur_100km'])} €.",
                            tone="positive"
                            if k["energie_elektro_eur_100km"] < k["energie_verbrenner_eur_100km"]
                            else "caution",
                            weight=1,
                        ),
                        b.stat_card(
                            title="CO₂ pro Jahr",
                            metric=f"− {_komma(k['co2_ersparnis_kg_a'] / 1000, 1)} t",
                            metric_label="gegenüber Verbrenner",
                            body="Gerechnet mit dem deutschen Strommix. Mit eigener "
                            "PV-Anlage oder Ökostromtarif fällt die Bilanz besser aus.",
                            tone="positive",
                            weight=1,
                        ),
                    ]
                ),
                b.card(
                    b.chart(
                        title="Kostenposten im Vergleich",
                        subtitle=f"Gesamtkosten über {k['haltedauer_jahre']} Jahre bei "
                        f"{k['jahres_km']:,.0f} km im Jahr.".replace(",", "."),
                        chart_type="groupedBar",
                        categories=bind("/kategorien"),
                        series=bind("/serien"),
                        unit="€",
                        value_format="currency",
                    )
                ),
                b.assumptions(
                    calc.annahmen(profil)
                    + [
                        f"Gesamtkosten Elektro {_euro(k['gesamt_elektro_eur'])}, "
                        f"Verbrenner {_euro(k['gesamt_verbrenner_eur'])}",
                        "Wertverlust auf Basis angenommener Restwerte nach vier Jahren.",
                    ],
                    source=dd.QUELLE_MOBILITAET,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish({"kategorien": k["kategorien"], "serien": k["serien"]})


def stellschrauben_surface(profil: calc.Mobilitaetsprofil) -> Surface:
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

    b = SurfaceBuilder("stellschrauben", "Was wäre wenn")
    b.root(
        b.column(
            [
                b.heading(
                    "Was wäre wenn",
                    "Ihre Strecke, Ihr Ladeort",
                    "Zwei Zahlen entscheiden über die Kosten, und bei beiden haben "
                    "wir bisher geschätzt. Stellen Sie ein, was wirklich zu Ihnen "
                    "passt – die Rechnung unten folgt sofort.",
                ),
                b.card(
                    b.column(
                        [
                            b.text("Ihre Einstellung", variant="h3"),
                            b.slider(
                                label="Kilometer an einem typischen Tag",
                                value_path="/wenn/taeglich_km",
                                minimum=werte["taeglich_km_min"],
                                maximum=werte["taeglich_km_max"],
                            ),
                            b.slider(
                                label="Anteil, den Sie zu Hause laden, in Prozent",
                                value_path="/wenn/anteil_zuhause",
                                minimum=0,
                                maximum=100,
                            ),
                            b.text(
                                f"Zu Hause rechne ich mit {_komma(werte['preis_zuhause_ct'] / 100)} "
                                f"€/kWh, unterwegs mit {_komma(werte['preis_unterwegs_ct'] / 100)} "
                                "€/kWh im Mix aus AC und Schnellladen.",
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
                            label="Kilometer im Jahr",
                            value=number(jahres_km),
                            hint="mit Langstrecken und Freizeit",
                        ),
                        b.live_stat(
                            label="Strom",
                            value=money(strom_eur),
                            hint="pro Jahr",
                        ),
                        b.live_stat(
                            label=f"{werte['kraftstoff'].capitalize()} zum Vergleich",
                            value=money(kraftstoff_eur),
                            hint="pro Jahr, gleiche Strecke",
                        ),
                        b.live_stat(
                            label="Unterschied",
                            value=money(over(minus(kraftstoff_eur, strom_eur), 12)),
                            hint="pro Monat, nur Energie",
                        ),
                    ]
                ),
                b.card(
                    b.column(
                        [
                            b.text("Sollen wir so weiterrechnen?", variant="h3"),
                            b.text(
                                "Übernehmen Sie Ihre Einstellung, gilt sie für die "
                                "ganze Beratung – Reichweite, Ladeoptionen und "
                                "Gesamtkosten."
                            ),
                            b.button(
                                "Mit diesen Werten weiterrechnen",
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
                        f"{werte['fahrzeug']}, {_komma(werte['verbrauch_kwh_100km'], 1)} "
                        f"kWh/100 km im Realbetrieb",
                        f"Verbrenner-Vergleich mit {_komma(werte['verbrauch_l_100km'], 1)} "
                        f"l/100 km {werte['kraftstoff']}",
                        f"Neben der Tagesstrecke rechne ich fest mit "
                        f"{werte['km_konstante']:,.0f} km im Jahr für Langstrecken "
                        f"und Freizeit.".replace(",", "."),
                        "Die Regler verändern nur Strecke und Ladeort – Verbrauch, "
                        "Preise und Fahrzeugklasse bleiben, wie berechnet.",
                        "Nur Energiekosten. Wertverlust, Wartung, Versicherung und "
                        "Steuer stehen im Kostenvergleich.",
                        dd.DISCLAIMER,
                    ],
                    source=dd.QUELLE_MOBILITAET,
                    as_of=dd.STAND,
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
