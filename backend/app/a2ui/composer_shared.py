"""Surfaces both journeys share: addressing a concern, and the handover."""

from __future__ import annotations

from typing import Any, Literal, Sequence

from ..domain import demo_data as dd
from .builder import TONE_MARK, SurfaceBuilder, bind
from .surface import Surface

Journey = Literal["energie", "mobilitaet"]


def bedenken_surface(
    *,
    titel: str,
    einordnung: str,
    punkte: Sequence[dict[str, str]],
) -> Surface:
    """"Empathische Reaktion auf Bedenken, ohne Druck aufzubauen".

    A worry gets its own surface rather than being buried in a paragraph:
    named in the client's words, then answered point by point.
    """
    b = SurfaceBuilder("bedenken", "Ihre Frage")

    punkt = b.card(
        b.column([b.text(bind("titel")), b.text(bind("text"), variant="body")])
    )

    b.root(
        b.column(
            [
                b.heading("Ihre Frage", titel),
                b.card(b.text(einordnung)),
                b.repeat(punkt, "/punkte"),
            ]
        )
    )

    return b.finish(
        {
            "punkte": [
                {
                    "titel": f"**{TONE_MARK.get(p.get('tone', 'neutral'), '→')} "
                    f"{p.get('titel', '')}**",
                    "text": p.get("text", ""),
                }
                for p in punkte[:4]
            ]
        }
    )


def handover_surface(
    *,
    journey: Journey,
    titel: str,
    empfehlung: str,
    begruendung: Sequence[str],
    offene_punkte: Sequence[str],
    schritt_label: str,
    schritt_event: str,
) -> Surface:
    """The handover: a readable summary plus one concrete next step.

    This is the artefact a human advisor or a digital process picks up, so the
    open points travel with it instead of getting lost between channels.
    """
    zweit_label, zweit_event = (
        ("Zusammenfassung per E-Mail", "zusammenfassung_senden")
        if journey == "energie"
        else ("Angebot anfordern", "angebot_anfordern")
    )

    b = SurfaceBuilder("naechster_schritt", "Ihr nächster Schritt")
    b.root(
        b.column(
            [
                b.heading(
                    "Ihr nächster Schritt",
                    titel,
                    "Alles, was wir besprochen haben, in einer Übersicht.",
                ),
                b.card(
                    b.column(
                        [
                            b.text("Meine Empfehlung für Sie", variant="h3"),
                            b.text(empfehlung),
                            b.row(
                                [
                                    b.bullets(begruendung, heading="Dafür spricht"),
                                    b.bullets(
                                        offene_punkte or ["Keine offenen Punkte"],
                                        heading="Noch zu klären",
                                    ),
                                ]
                            ),
                        ]
                    )
                ),
                b.card(
                    b.column(
                        [
                            b.text(schritt_label, variant="h3"),
                            b.text(
                                "Sie entscheiden, wie es weitergeht – nichts davon "
                                "ist verbindlich."
                            ),
                            b.row(
                                [
                                    b.button(
                                        schritt_label,
                                        event=schritt_event,
                                        context={"journey": journey},
                                        variant="primary",
                                    ),
                                    b.button(
                                        zweit_label,
                                        event=zweit_event,
                                        context={"journey": journey},
                                    ),
                                ],
                                align="center",
                            ),
                        ]
                    )
                ),
                b.assumptions(
                    [
                        "Diese Beratung ist unverbindlich und ersetzt kein Angebot.",
                        "Ihre Angaben bleiben in dieser Sitzung und werden nicht gespeichert.",
                        dd.DISCLAIMER,
                    ],
                    source=dd.QUELLE_ENERGIE if journey == "energie" else dd.QUELLE_MOBILITAET,
                    as_of=dd.STAND,
                ),
            ]
        )
    )

    return b.finish({})
