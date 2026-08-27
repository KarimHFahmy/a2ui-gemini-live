"""Captures a scripted run of both journeys as A2UI fixtures.

The output feeds `frontend/preview.html`, which renders every advisory surface
without a Live API session. That makes the catalog reviewable and
regression-testable offline, and gives the design work a fast loop.

    python backend/scripts/generate_fixtures.py
    python backend/scripts/generate_fixtures.py --happy

The default run is the *credible* one: it is what the catalog check renders, and
the mobility journey deliberately lands on "das rechnet sich für Sie heute
nicht". `--happy` captures the favourable profiles from `docs/demo-script.md`
instead, for clicking through the good version of the demo without spending a
voice session. Do not commit the `--happy` output — the check expects the
default.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google.adk.events import EventActions  # noqa: E402
from google.adk.tools import ToolContext  # noqa: E402

from app.journeys import all_journeys, energie, mobilitaet  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "fixtures.json"


class CaptureContext:
    """A minimal stand-in for ADK's ToolContext.

    Tools touch exactly two things — session state and `render_ui_widget` — so
    capturing fixtures needs neither a runner nor a model. Borrowing the real
    method means these payloads are byte-for-byte what a live session produces.
    """

    def __init__(self) -> None:
        self.state: dict[str, Any] = {}
        self._event_actions = EventActions()

    render_ui_widget = ToolContext.render_ui_widget

    def drain(self) -> list[dict[str, Any]]:
        """Returns the A2UI messages pushed since the last call."""
        widgets = self._event_actions.render_ui_widgets or []
        self._event_actions = EventActions()
        return [message for widget in widgets for message in widget.payload["messages"]]


Script = list[tuple[Callable[..., Any], dict[str, Any]]]

#: A representative conversation per journey — the demo moments from the
#: briefing, with the tool arguments a model would produce.
SCRIPTS: dict[str, Script] = {
    "energie": [
        (
            energie.profil_aktualisieren,
            {
                "baujahr": 1985,
                "wohnflaeche_qm": 160,
                "heizung": "gas",
                "sanierungsstand": "teilsaniert",
                "waermesystem": "heizkoerper_standard",
                "personen": 4,
                "prioritaeten": ["Wirtschaftlichkeit", "Unabhängigkeit"],
                "bedenken": ["Reicht die Wärmepumpe im Winter?"],
                "offene_punkte": ["Genauer Gasverbrauch der letzten Jahre"],
            },
        ),
        (energie.waermepumpen_eignung_zeigen, {}),
        (energie.szenarien_vergleichen, {"empfohlen": "waermepumpe"}),
        (energie.wirtschaftlichkeit_zeigen, {"szenario": "waermepumpe"}),
        (energie.foerderung_und_fahrplan_zeigen, {"szenario": "waermepumpe"}),
        (energie.stellschrauben_zeigen, {}),
        (
            energie.bedenken_adressieren,
            {
                "titel": "Reicht die Wärmepumpe im Winter?",
                "einordnung": (
                    "Das ist die häufigste Sorge – und sie hat einen wahren Kern. "
                    "Entscheidend ist aber nicht die Außentemperatur, sondern wie "
                    "warm das Wasser in Ihren Heizkörpern sein muss."
                ),
                "punkte": [
                    {
                        "titel": "Ihre Vorlauftemperatur ist unkritisch",
                        "text": (
                            "Ihre Heizkörper brauchen im Auslegungsfall rund "
                            "**55 °C**. Damit läuft eine Wärmepumpe zuverlässig, "
                            "auch bei Frost."
                        ),
                        "tone": "positive",
                    },
                    {
                        "titel": "Kein Heizstab nötig",
                        "text": (
                            "Bei dieser Auslegung deckt die Wärmepumpe die Last "
                            "auch im Januar allein."
                        ),
                        "tone": "positive",
                    },
                    {
                        "titel": "Was Sie trotzdem tun sollten",
                        "text": (
                            "Ein hydraulischer Abgleich sorgt dafür, dass jeder "
                            "Raum die Wärme bekommt, die er braucht."
                        ),
                        "tone": "neutral",
                    },
                ],
            },
        ),
        (
            energie.naechsten_schritt_anbieten,
            {
                "empfehlung": (
                    "Eine Wärmepumpe passt gut zu Ihrem Haus. Ich würde sie ohne "
                    "große Vorarbeiten einbauen lassen und die Dachdämmung später "
                    "separat prüfen."
                ),
                "begruendung": [
                    "Ihre Heizkörper kommen mit 55 °C aus – der entscheidende Punkt",
                    "Nach rund 12 Jahren sind Sie gegenüber der Gasheizung im Plus",
                    "Die Förderung senkt Ihren Eigenanteil deutlich",
                ],
                "offene_punkte": [
                    "Tatsächlicher Gasverbrauch der letzten drei Jahre",
                    "Aufstellort für das Außengerät",
                ],
                "schritt": "vor_ort_check",
            },
        ),
    ],
    "mobilitaet": [
        (
            mobilitaet.profil_aktualisieren,
            {
                "taeglich_km": 55,
                "pendeltage_pro_woche": 5,
                "langstrecken_pro_monat": 3,
                "langstrecke_km": 450,
                "lademoeglichkeit": "nur_oeffentlich",
                "stellplatz_vorhanden": True,
                "fahrzeugklasse": "kompakt",
                "budget_eur_monat": 450,
                "bedenken": ["Keine Wallbox", "Reichweite auf der Langstrecke"],
                "offene_punkte": ["Lademöglichkeit beim Arbeitgeber"],
            },
        ),
        (mobilitaet.alltagstauglichkeit_zeigen, {}),
        (mobilitaet.ladeloesungen_vergleichen, {}),
        (mobilitaet.fahrzeuge_vorschlagen, {}),
        (mobilitaet.kosten_vergleichen, {}),
        (mobilitaet.stellschrauben_zeigen, {}),
        (
            mobilitaet.bedenken_adressieren,
            {
                "titel": "Ist ein E-Auto ohne eigene Wallbox praktikabel?",
                "einordnung": (
                    "Ehrliche Antwort: praktikabel ja, wirtschaftlich derzeit "
                    "nicht. Ihre Strecken sind kein Problem – der Ladepreis ist es."
                ),
                "punkte": [
                    {
                        "titel": "Der Alltag passt",
                        "text": (
                            "258 km Winterreichweite gegen 55 km am Tag: Sie laden "
                            "etwa alle vier Tage."
                        ),
                        "tone": "positive",
                    },
                    {
                        "titel": "Der Preis passt noch nicht",
                        "text": (
                            "Nur öffentlich zu laden kostet rund **11,37 € je "
                            "100 km** – etwa so viel wie Benzin."
                        ),
                        "tone": "caution",
                    },
                    {
                        "titel": "Der Hebel",
                        "text": (
                            "Schon eine Lademöglichkeit beim Arbeitgeber halbiert "
                            "diesen Wert."
                        ),
                        "tone": "positive",
                    },
                ],
            },
        ),
        (
            mobilitaet.naechsten_schritt_anbieten,
            {
                "empfehlung": (
                    "Klären Sie zuerst die Ladefrage, nicht die Fahrzeugfrage. Mit "
                    "einer Lademöglichkeit zu Hause oder beim Arbeitgeber wird der "
                    "Umstieg für Sie deutlich günstiger als Ihr heutiges Auto."
                ),
                "begruendung": [
                    "Ihre Strecken sind für ein E-Auto völlig unkritisch",
                    "Der Ladeort entscheidet über rund 1.800 € im Jahr",
                    "Eine Kompaktklasse deckt Ihr Profil vollständig ab",
                ],
                "offene_punkte": [
                    "Wallbox am Stellplatz technisch möglich?",
                    "Lädt Ihr Arbeitgeber Mitarbeitende?",
                ],
                "schritt": "ladecheck",
            },
        ),
    ],
}


#: The same two journeys run on the profiles that make every number come out
#: well — see "The happy path" in `docs/demo-script.md`, which quotes the
#: figures these produce. A large, older, gas-heated house with generously
#: sized radiators, and an 80-km commuter with a wallbox.
HAPPY_SCRIPTS: dict[str, Script] = {
    "energie": [
        (
            energie.profil_aktualisieren,
            {
                "baujahr": 1985,
                "wohnflaeche_qm": 200,
                "heizung": "gas",
                "sanierungsstand": "teilsaniert",
                "waermesystem": "flaechenheizkoerper_gross",
                "personen": 4,
                "prioritaeten": ["Wirtschaftlichkeit", "Unabhängigkeit"],
                "offene_punkte": ["Genauer Gasverbrauch der letzten Jahre"],
            },
        ),
        (energie.waermepumpen_eignung_zeigen, {}),
        (energie.szenarien_vergleichen, {"empfohlen": "waermepumpe"}),
        (energie.wirtschaftlichkeit_zeigen, {"szenario": "waermepumpe"}),
        (energie.stellschrauben_zeigen, {}),
        (energie.foerderung_und_fahrplan_zeigen, {"szenario": "waermepumpe"}),
        (
            energie.naechsten_schritt_anbieten,
            {
                "empfehlung": (
                    "Ihr Haus ist ein guter Fall für eine Wärmepumpe – die großen "
                    "Heizkörper sind der Grund. Ich würde sie ohne Vorarbeiten "
                    "einbauen lassen."
                ),
                "begruendung": [
                    "45 °C Vorlauf reichen Ihnen – damit läuft eine Wärmepumpe effizient",
                    "Rund 1.700 € weniger Betriebskosten im Jahr",
                    "Nach neun Jahren sind Sie gegenüber der Gasheizung im Plus",
                ],
                "offene_punkte": ["Aufstellort für das Außengerät"],
                "schritt": "vor_ort_check",
            },
        ),
    ],
    "mobilitaet": [
        (
            mobilitaet.profil_aktualisieren,
            {
                "taeglich_km": 80,
                "pendeltage_pro_woche": 5,
                "langstrecken_pro_monat": 2,
                "langstrecke_km": 350,
                "lademoeglichkeit": "wallbox_zuhause",
                "stellplatz_vorhanden": True,
                "fahrzeugklasse": "kompakt",
                "haltedauer_jahre": 6,
                "prioritaeten": ["Verlässlichkeit im Alltag"],
            },
        ),
        (mobilitaet.alltagstauglichkeit_zeigen, {}),
        (mobilitaet.ladeloesungen_vergleichen, {}),
        (mobilitaet.fahrzeuge_vorschlagen, {}),
        (mobilitaet.kosten_vergleichen, {}),
        (mobilitaet.stellschrauben_zeigen, {}),
        (
            mobilitaet.naechsten_schritt_anbieten,
            {
                "empfehlung": (
                    "Ein E-Auto passt zu Ihnen. Ihre Wallbox macht den Unterschied: "
                    "die Energie kostet Sie gut die Hälfte dessen, was Sie heute "
                    "tanken."
                ),
                "begruendung": [
                    "258 km Winterreichweite gegen 80 km am Tag – reichlich Puffer",
                    "6,53 € statt 11,39 € je 100 km",
                    "Über sechs Jahre rund 3.700 € günstiger als der Verbrenner",
                ],
                "offene_punkte": ["Wunschmodell und Liefertermin"],
                "schritt": "probefahrt",
            },
        ),
    ],
}


def capture(scripts: dict[str, Script]) -> dict[str, dict[str, Any]]:
    """One entry per journey: its arc, its topics, and the A2UI stream.

    The metadata travels with the fixtures so the preview and the session check
    render the same shell a live session does — otherwise the one screen used
    for design review would be the one screen missing the progress indicator.
    """
    meta = {
        journey.id: {
            "steps": [
                {"surfaceId": surface_id, "label": label}
                for surface_id, label in journey.steps
            ],
            "topics": journey.topics,
        }
        for journey in all_journeys()
    }
    fixtures: dict[str, dict[str, Any]] = {}

    for journey_id, script in scripts.items():
        context = CaptureContext()
        messages: list[dict[str, Any]] = []

        for tool, args in script:
            tool(tool_context=context, **args)  # type: ignore[arg-type]
            messages.extend(context.drain())

        fixtures[journey_id] = {**meta[journey_id], "messages": messages}

    return fixtures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--happy",
        action="store_true",
        help="capture the favourable profiles instead (do not commit the result)",
    )
    args = parser.parse_args()

    fixtures = capture(HAPPY_SCRIPTS if args.happy else SCRIPTS)
    OUTPUT.write_text(
        json.dumps(fixtures, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for journey_id, captured in fixtures.items():
        print(f"{journey_id}: {len(captured['messages'])} A2UI messages")
    print(f"written to {OUTPUT}")


if __name__ == "__main__":
    main()
