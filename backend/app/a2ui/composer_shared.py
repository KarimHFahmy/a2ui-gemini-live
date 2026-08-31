"""Surfaces both journeys share: addressing a concern, and the handover."""

from __future__ import annotations

from typing import Literal, Sequence

from ..texts import Texts
from .builder import TONE_MARK, SurfaceBuilder, bind
from .surface import Surface

Journey = Literal["energie", "mobilitaet"]


def bedenken_surface(
    t: Texts,
    *,
    titel: str,
    einordnung: str,
    punkte: Sequence[dict[str, str]],
) -> Surface:
    """"Empathische Reaktion auf Bedenken, ohne Druck aufzubauen".

    A worry gets its own surface rather than being buried in a paragraph:
    named in the client's words, then answered point by point.
    """
    b = SurfaceBuilder("bedenken", t("bedenken.eyebrow"), t)

    punkt = b.card(
        b.column([b.text(bind("titel")), b.text(bind("text"), variant="body")])
    )

    b.root(
        b.column(
            [
                b.heading(t("bedenken.eyebrow"), titel),
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
    t: Texts,
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
        (t("handover.second.energie"), "zusammenfassung_senden")
        if journey == "energie"
        else (t("handover.second.mobilitaet"), "angebot_anfordern")
    )

    b = SurfaceBuilder("naechster_schritt", t("handover.eyebrow"), t)
    b.root(
        b.column(
            [
                b.heading(
                    t("handover.eyebrow"),
                    titel,
                    t("handover.subtitle"),
                ),
                b.card(
                    b.column(
                        [
                            b.text(t("handover.recommendation"), variant="h3"),
                            b.text(empfehlung),
                            b.row(
                                [
                                    b.bullets(begruendung, heading=t("handover.pro")),
                                    b.bullets(
                                        offene_punkte or [t("block.none_open")],
                                        heading=t("handover.open"),
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
                            b.text(t("handover.not_binding")),
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
                    [*t.list("handover.assumptions"), t("data.disclaimer")],
                    source=t(f"data.source.{journey}"),
                    as_of=t("data.as_of"),
                ),
            ]
        )
    )

    return b.finish({})
