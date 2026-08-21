"""Surfaces both journeys share: addressing a concern, and the handover."""

from __future__ import annotations

from typing import Any, Literal

from ..domain import demo_data as dd
from . import components as c
from .surface import Surface

Journey = Literal["energie", "mobilitaet"]


def bedenken_surface(
    *,
    titel: str,
    einordnung: str,
    punkte: list[dict[str, str]],
    tone: Literal["positive", "neutral", "caution"] = "neutral",
) -> Surface:
    """"Empathische Reaktion auf Bedenken, ohne Druck aufzubauen".

    A worry gets its own surface rather than being buried in a paragraph:
    named plainly, then answered point by point.
    """
    children = ["kopf", "einordnung"]
    components: list[dict[str, Any]] = [
        c.advisory_header(
            "kopf",
            eyebrow="Ihre Frage",
            title=titel,
            icon="question",
        ),
        c.insight_card(
            "einordnung",
            title="Kurz eingeordnet",
            body=einordnung,
            tone=tone,
            icon="info",
        ),
    ]

    for index, punkt in enumerate(punkte[:4]):
        comp_id = f"punkt_{index}"
        children.append(comp_id)
        components.append(
            c.insight_card(
                comp_id,
                title=punkt.get("titel", ""),
                body=punkt.get("text", ""),
                tone=punkt.get("tone", "neutral"),  # type: ignore[arg-type]
                icon=punkt.get("icon"),
            )
        )

    components.insert(0, c.column("root", children))

    return Surface(
        surface_id="bedenken",
        title="Ihre Frage",
        components=components,
        data={},
    )


def handover_surface(
    *,
    journey: Journey,
    titel: str,
    empfehlung: str,
    begruendung: list[str],
    offene_punkte: list[str],
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

    components = [
        c.column("root", ["kopf", "empfehlung", "cta", "hinweis"]),
        c.advisory_header(
            "kopf",
            eyebrow="Ihr nächster Schritt",
            title=titel,
            subtitle="Alles, was wir besprochen haben, in einer Übersicht.",
            icon="flag",
        ),
        c.recommendation(
            "empfehlung",
            title="Meine Empfehlung für Sie",
            summary=empfehlung,
            pros=c.bind("/begruendung"),
            cons=c.bind("/offen"),
        ),
        c.next_step_cta(
            "cta",
            title=schritt_label,
            body=(
                "Sie entscheiden, wie es weitergeht – nichts davon ist verbindlich."
            ),
            primary_label=schritt_label,
            primary_event=schritt_event,
            primary_context={"journey": journey},
            secondary_label=zweit_label,
            secondary_event=zweit_event,
            secondary_context={"journey": journey},
        ),
        c.assumption_note(
            "hinweis",
            title="Transparenz",
            assumptions=c.bind("/hinweise"),
            source=(
                dd.QUELLE_ENERGIE if journey == "energie" else dd.QUELLE_MOBILITAET
            ),
            as_of=dd.STAND,
        ),
    ]

    return Surface(
        surface_id="naechster_schritt",
        title="Ihr nächster Schritt",
        components=components,
        data={
            "begruendung": begruendung,
            "offen": offene_punkte or ["Keine offenen Punkte"],
            "hinweise": [
                "Diese Beratung ist unverbindlich und ersetzt kein Angebot.",
                "Ihre Angaben bleiben in dieser Sitzung und werden nicht gespeichert.",
                dd.DISCLAIMER,
            ],
        },
    )
