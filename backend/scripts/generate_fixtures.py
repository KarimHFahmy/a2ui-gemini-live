"""Captures a scripted run of both journeys as A2UI fixtures.

The output feeds `frontend/preview.html`, which renders every advisory surface
without a Live API session. That makes the catalog reviewable and
regression-testable offline, and gives the design work a fast loop.

    python backend/scripts/generate_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.journeys import JOURNEYS  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "fixtures.json"

#: A representative conversation per journey — the demo moments from the
#: briefing, with the same tool arguments the model would produce.
SCRIPTS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "energie": [
        (
            "profil_aktualisieren",
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
        ("waermepumpen_eignung_zeigen", {}),
        ("szenarien_vergleichen", {"empfohlen": "waermepumpe"}),
        ("wirtschaftlichkeit_zeigen", {"szenario": "waermepumpe"}),
        ("foerderung_und_fahrplan_zeigen", {"szenario": "waermepumpe"}),
        (
            "bedenken_adressieren",
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
            "naechsten_schritt_anbieten",
            {
                "empfehlung": (
                    "Eine Wärmepumpe passt gut zu Ihrem Haus. Ich würde sie ohne "
                    "große Vorarbeiten einbauen lassen und die Dachdämmung später "
                    "separat prüfen."
                ),
                "begruendung": [
                    "Ihre Heizkörper kommen mit 55 °C aus – das ist der entscheidende Punkt",
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
            "profil_aktualisieren",
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
        ("alltagstauglichkeit_zeigen", {}),
        ("ladeloesungen_vergleichen", {}),
        ("fahrzeuge_vorschlagen", {}),
        ("kosten_vergleichen", {}),
        (
            "bedenken_adressieren",
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
            "naechsten_schritt_anbieten",
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


def capture() -> dict[str, list[dict[str, Any]]]:
    fixtures: dict[str, list[dict[str, Any]]] = {}

    for journey_id, journey in JOURNEYS.items():
        state = journey.state_factory()
        messages: list[dict[str, Any]] = []
        seen: set[str] = set()

        for name, args in SCRIPTS[journey_id]:
            result = journey.handle(state, name, args)
            for surface in result.surfaces:
                messages.extend(surface.messages(exists=surface.surface_id in seen))
                seen.add(surface.surface_id)

        fixtures[journey_id] = messages

    return fixtures


def main() -> None:
    fixtures = capture()
    OUTPUT.write_text(
        json.dumps(fixtures, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for journey_id, messages in fixtures.items():
        print(f"{journey_id}: {len(messages)} A2UI messages")
    print(f"written to {OUTPUT}")


if __name__ == "__main__":
    main()
