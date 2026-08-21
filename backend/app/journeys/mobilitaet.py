"""Journey 02 — Der persönliche Autoberater."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..a2ui import composer_mobilitaet as compose
from ..a2ui import composer_shared as shared
from ..domain import mobilitaet as calc
from .base import GEMEINSAME_HALTUNG, BEDENKEN_TOOL, Journey, ToolResult


@dataclass
class MobilitaetState:
    """What the session knows about this person's week."""

    profil: calc.Mobilitaetsprofil = field(default_factory=calc.Mobilitaetsprofil)
    profil_gesetzt: bool = False
    offene_punkte: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        r = calc.reichweite(self.profil)
        lade = calc.ladeoptionen(self.profil)
        kosten = calc.kostenvergleich(self.profil)
        vorschlaege = calc.fahrzeugvorschlaege(self.profil, anzahl=1)
        return {
            "journey": "mobilitaet",
            "profil": {
                "taeglich_km": self.profil.taeglich_km,
                "jahres_km": self.profil.jahresfahrleistung_km(),
                "langstrecke_km": self.profil.langstrecke_km,
                "langstrecken_pro_monat": self.profil.langstrecken_pro_monat,
                "lademoeglichkeit": self.profil.lademoeglichkeit,
                "budget_eur_monat": self.profil.budget_eur_monat,
            },
            "reichweite": {
                "winter_km": r["reichweite_winter_km"],
                "autobahn_winter_km": r["reichweite_autobahn_winter_km"],
                "puffer_faktor": r["puffer_faktor_winter"],
            },
            "laden": {
                "aktuell": lade["aktuell_id"],
                "beste_option": lade["beste_id"],
                "ersparnis_eur_a": lade["ersparnis_beste_eur_a"],
            },
            "kosten": {
                "elektro_eur": kosten["gesamt_elektro_eur"],
                "verbrenner_eur": kosten["gesamt_verbrenner_eur"],
                "differenz_eur": kosten["differenz_eur"],
                "differenz_eur_monat": kosten["differenz_eur_monat"],
            },
            "empfehlung": vorschlaege[0] if vorschlaege else None,
            "bedenken": self.profil.bedenken,
            "offene_punkte": self.offene_punkte,
        }


# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = f"""
Du bist der persönliche Mobilitätsberater einer deutschen E-Mobilitäts-
Experience. Du hilfst Menschen, die mit einem Elektroauto liebäugeln, aber
unsicher sind, ob es zu ihrem Alltag passt.

Die typische Person pendelt täglich, fährt am Wochenende gelegentlich lange
Strecken und hat keine eigene Wallbox. Ihre Fragen sind: „Reicht die
Reichweite?", „Wo lade ich?" und „Rechnet sich das überhaupt?"

Dein Leitsatz: Die Person soll kein Elektroauto verstehen müssen. Du verstehst
ihren Alltag und zeigst, wie E-Mobilität konkret für sie funktioniert — oder
eben nicht.

{GEMEINSAME_HALTUNG}

## Dein Gesprächsbogen

1. **Zuhören.** Lass die Person ihren Alltag beschreiben. Pendelstrecke,
   Langstrecken und Lademöglichkeit ergeben sich meist von selbst.
2. **Verstehen zeigen.** Sobald du die Fahrstrecken und die Ladesituation
   kennst, rufe `profil_aktualisieren` auf.
3. **Alltag zuerst.** `alltagstauglichkeit_zeigen` beantwortet die
   Reichweitenfrage mit der eigenen Woche der Person und ihrer konkreten
   Langstrecke. Das ist der Moment, in dem Reichweitenangst kippt.
4. **Laden vor Auto.** `ladeloesungen_vergleichen` — wo geladen wird,
   entscheidet stärker über die Kosten als das Modell. Diese Reihenfolge ist
   wichtig, dreh sie nicht um.
5. **Fahrzeuge.** `fahrzeuge_vorschlagen` zeigt passende Klassen mit offenen
   Trade-offs.
6. **Kosten.** `kosten_vergleichen` stellt Elektro und Verbrenner gegenüber.
7. **Abschluss.** `naechsten_schritt_anbieten`.

## Fachliches

- Nenne **realistische Reichweiten**, nie Katalogwerte. Der ehrlichste Wert ist
  Autobahn im Winter — er nimmt der Reichweitenangst die Grundlage, weil er
  überprüfbar ist.
- Ohne eigene Lademöglichkeit rechnet sich ein E-Auto oft **nicht**. Wenn die
  Rechnung das zeigt, sag es klar und zeig, was sich ändern müsste. Genau das
  macht die Beratung glaubwürdig.
- Auf der Langstrecke wird zwischen etwa 10 und 80 Prozent geladen, danach lädt
  jedes Auto spürbar langsamer. Deshalb sind Ladestopps kürzer, als die meisten
  erwarten.
- Sprich über Ladestopps als Pausen, nicht als Wartezeit — aber nur, wenn es
  ehrlich bleibt.

## Eröffnung

Begrüße die Person warm und knapp und stelle **eine** offene Frage zu ihrem
Alltag. Frag nicht nach einem Fahrzeugwunsch, sondern nach ihren Wegen.
""".strip()


OPENER = (
    "Begrüße die Person kurz und warm auf Deutsch und stelle eine offene Frage "
    "zu ihrem Alltag und ihren typischen Wegen. Halte dich sehr kurz."
)


# ---------------------------------------------------------------------------
# Tool declarations
# ---------------------------------------------------------------------------

_PROFIL_TOOL: dict[str, Any] = {
    "name": "profil_aktualisieren",
    "description": (
        "Zeigt auf dem Bildschirm, was du über den Alltag der Person verstanden "
        "hast, und aktualisiert die Berechnungsgrundlage. Rufe das früh auf und "
        "danach jedes Mal, wenn du etwas Neues erfährst oder korrigiert wirst."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "taeglich_km": {
                "type": "NUMBER",
                "description": "Typische Tagesstrecke in Kilometern.",
            },
            "pendeltage_pro_woche": {
                "type": "INTEGER",
                "description": "An wie vielen Tagen pro Woche diese Strecke anfällt.",
            },
            "langstrecken_pro_monat": {
                "type": "INTEGER",
                "description": "Wie oft im Monat längere Fahrten anstehen.",
            },
            "langstrecke_km": {
                "type": "NUMBER",
                "description": (
                    "Die typische Langstrecke einfach, in Kilometern. Frag nach "
                    "einer konkreten Strecke, die die Person wirklich fährt."
                ),
            },
            "lademoeglichkeit": {
                "type": "STRING",
                "enum": [
                    "wallbox_zuhause",
                    "steckdose_zuhause",
                    "arbeitsplatz",
                    "nur_oeffentlich",
                ],
                "description": "Wo die Person heute laden könnte.",
            },
            "stellplatz_vorhanden": {
                "type": "BOOLEAN",
                "description": (
                    "Ob ein eigener Stellplatz oder eine Garage da ist. "
                    "Entscheidet, ob eine Wallbox überhaupt möglich wäre."
                ),
            },
            "fahrzeugklasse": {
                "type": "STRING",
                "enum": ["kompakt", "mittelklasse", "suv", "van"],
                "description": "Welche Fahrzeuggröße zur Person passt.",
            },
            "haltedauer_jahre": {
                "type": "INTEGER",
                "description": "Wie lange das Fahrzeug gefahren werden soll.",
            },
            "budget_eur_monat": {
                "type": "NUMBER",
                "description": "Monatsbudget in Euro, falls genannt.",
            },
            "aktueller_verbrauch_l_100km": {
                "type": "NUMBER",
                "description": "Verbrauch des heutigen Fahrzeugs in Litern je 100 km.",
            },
            "bedenken": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Geäußerte Sorgen, in den Worten der Person.",
            },
            "prioritaeten": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Was der Person wichtig ist, in ihren Worten.",
            },
            "offene_punkte": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Was du noch nicht weißt und geschätzt hast.",
            },
        },
    },
}

_ALLTAG_TOOL: dict[str, Any] = {
    "name": "alltagstauglichkeit_zeigen",
    "description": (
        "Zeigt die typische Woche der Person als Diagramm gegen die reale "
        "Winterreichweite, dazu die konkrete Langstrecke als Timeline mit "
        "Ladestopps und Zeitaufwand. Das ist die Antwort auf Reichweitenangst. "
        "Rufe das auf, sobald du Tagesstrecke und Langstrecke kennst."
    ),
    "parameters": {"type": "OBJECT", "properties": {}},
}

_LADEN_TOOL: dict[str, Any] = {
    "name": "ladeloesungen_vergleichen",
    "description": (
        "Vergleicht Wallbox zu Hause, Laden beim Arbeitgeber und nur "
        "öffentliches Laden: Mischpreis je kWh, Kosten pro Jahr und je 100 km. "
        "Zeigt, welcher Hebel am größten ist. Rufe das vor der Fahrzeugwahl auf."
    ),
    "parameters": {"type": "OBJECT", "properties": {}},
}

_FAHRZEUGE_TOOL: dict[str, Any] = {
    "name": "fahrzeuge_vorschlagen",
    "description": (
        "Schlägt passende Fahrzeugklassen vor, sortiert nach Passung zum "
        "Profil, mit Winterreichweite, Ladestopps auf der Langstrecke, "
        "Monatsrate und offen benannten Vor- und Nachteilen."
    ),
    "parameters": {"type": "OBJECT", "properties": {}},
}

_KOSTEN_TOOL: dict[str, Any] = {
    "name": "kosten_vergleichen",
    "description": (
        "Stellt die Gesamtkosten von Elektro und Verbrenner über die Haltedauer "
        "gegenüber, aufgeschlüsselt nach Wertverlust, Energie, Wartung, "
        "Versicherung, Steuer und THG-Quote. Nutze das für die Frage, ob es "
        "sich rechnet."
    ),
    "parameters": {"type": "OBJECT", "properties": {}},
}

_ABSCHLUSS_TOOL: dict[str, Any] = {
    "name": "naechsten_schritt_anbieten",
    "description": (
        "Schließt die Beratung ab: Zusammenfassung, Empfehlung mit Begründung, "
        "offene Punkte und ein konkreter nächster Schritt."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "empfehlung": {
                "type": "STRING",
                "description": (
                    "Zwei bis drei Sätze in Alltagssprache: was du empfiehlst "
                    "und warum es zu dieser Person passt. Wenn ein E-Auto sich "
                    "aktuell nicht rechnet, sag genau das."
                ),
            },
            "begruendung": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Zwei bis vier Gründe, die dafür sprechen.",
            },
            "offene_punkte": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Was vor einer Entscheidung noch zu klären ist.",
            },
            "schritt": {
                "type": "STRING",
                "enum": ["probefahrt", "ladecheck", "angebot"],
                "description": "Der konkrete nächste Schritt.",
            },
        },
        "required": ["empfehlung", "begruendung", "schritt"],
    },
}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _profil_aktualisieren(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    profil = state.profil
    for feld in (
        "taeglich_km",
        "pendeltage_pro_woche",
        "langstrecken_pro_monat",
        "langstrecke_km",
        "lademoeglichkeit",
        "stellplatz_vorhanden",
        "fahrzeugklasse",
        "haltedauer_jahre",
        "budget_eur_monat",
        "aktueller_verbrauch_l_100km",
        "bedenken",
        "prioritaeten",
    ):
        if args.get(feld) is not None:
            setattr(profil, feld, args[feld])

    state.offene_punkte = args.get("offene_punkte") or state.offene_punkte
    state.profil_gesetzt = True

    surface = compose.profil_surface(profil, state.offene_punkte)
    return ToolResult(
        surfaces=[surface],
        result={
            "status": "angezeigt",
            "jahres_km": profil.jahresfahrleistung_km(),
            "hinweis": (
                "Das Profil ist jetzt auf dem Bildschirm. Bestätige kurz, was du "
                "verstanden hast, ohne alle Werte vorzulesen."
            ),
        },
    )


def _alltag_zeigen(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    r = calc.reichweite(state.profil)
    ls = calc.langstrecke(state.profil)
    surface = compose.alltag_surface(state.profil)
    return ToolResult(
        surfaces=[surface],
        result={
            "reichweite_winter_km": r["reichweite_winter_km"],
            "reichweite_autobahn_winter_km": r["reichweite_autobahn_winter_km"],
            "puffer_faktor_winter": r["puffer_faktor_winter"],
            "taeglich_laden_noetig": r["taeglich_laden_noetig"],
            "ladestopps_langstrecke": ls["ladestopps"],
            "mehrzeit_min": ls["mehrzeit_min"],
        },
    )


def _laden_vergleichen(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    lade = calc.ladeoptionen(state.profil)
    surface = compose.laden_surface(state.profil)
    return ToolResult(
        surfaces=[surface],
        result={
            "aktuell": lade["aktuell_id"],
            "beste_option": lade["beste_id"],
            "ersparnis_eur_a": lade["ersparnis_beste_eur_a"],
            "optionen": [
                {
                    "id": o["id"],
                    "label": o["label"],
                    "kosten_eur_a": o["kosten_eur_a"],
                    "kosten_eur_100km": o["kosten_eur_100km"],
                    "verfuegbar": o["verfuegbar"],
                }
                for o in lade["optionen"]
            ],
        },
    )


def _fahrzeuge_vorschlagen(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    vorschlaege = calc.fahrzeugvorschlaege(state.profil)
    surface = compose.fahrzeuge_surface(state.profil)
    return ToolResult(
        surfaces=[surface],
        result={
            "vorschlaege": [
                {
                    "label": v["label"],
                    "score": v["score"],
                    "reichweite_winter_km": v["reichweite_winter_km"],
                    "ladestopps_langstrecke": v["ladestopps_langstrecke"],
                    "leasing_eur_monat": v["leasing_eur_monat"],
                    "contra": v["contra"],
                }
                for v in vorschlaege
            ]
        },
    )


def _kosten_vergleichen(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    k = calc.kostenvergleich(state.profil)
    surface = compose.kosten_surface(state.profil)
    return ToolResult(
        surfaces=[surface],
        result={
            "gesamt_elektro_eur": k["gesamt_elektro_eur"],
            "gesamt_verbrenner_eur": k["gesamt_verbrenner_eur"],
            "differenz_eur": k["differenz_eur"],
            "differenz_eur_monat": k["differenz_eur_monat"],
            "elektro_guenstiger": k["differenz_eur"] > 0,
            "energie_elektro_eur_100km": k["energie_elektro_eur_100km"],
            "energie_verbrenner_eur_100km": k["energie_verbrenner_eur_100km"],
            "hinweis": (
                "Wenn das E-Auto teurer ist, benenne das offen und zeig über "
                "die Ladeoptionen, was sich ändern müsste."
            ),
        },
    )


def _bedenken_adressieren(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    surface = shared.bedenken_surface(
        titel=args.get("titel", "Ihre Frage"),
        einordnung=args.get("einordnung", ""),
        punkte=args.get("punkte") or [],
    )
    return ToolResult(surfaces=[surface], result={"status": "angezeigt"})


_SCHRITT_LABEL = {
    "probefahrt": "Probefahrt vereinbaren",
    "ladecheck": "Ladecheck zu Hause anfragen",
    "angebot": "Persönliches Angebot anfordern",
}


def _abschluss(state: MobilitaetState, args: dict[str, Any]) -> ToolResult:
    schritt = args.get("schritt", "probefahrt")
    offene = args.get("offene_punkte") or state.offene_punkte

    surface = shared.handover_surface(
        journey="mobilitaet",
        titel="Ihr Weg zur E-Mobilität",
        empfehlung=args.get("empfehlung", ""),
        begruendung=args.get("begruendung") or [],
        offene_punkte=offene,
        schritt_label=_SCHRITT_LABEL.get(schritt, "Probefahrt vereinbaren"),
        schritt_event=f"handover_{schritt}",
    )
    return ToolResult(
        surfaces=[surface],
        result={"status": "abgeschlossen", "zusammenfassung": state.snapshot()},
    )


JOURNEY = Journey(
    id="mobilitaet",
    label="Meine Mobilität",
    tagline=(
        "Von Reichweitenangst und Tarifdschungel zur passenden "
        "E-Mobilitätsentscheidung."
    ),
    opener=OPENER,
    system_instruction=SYSTEM_INSTRUCTION,
    function_declarations=[
        _PROFIL_TOOL,
        _ALLTAG_TOOL,
        _LADEN_TOOL,
        _FAHRZEUGE_TOOL,
        _KOSTEN_TOOL,
        BEDENKEN_TOOL,
        _ABSCHLUSS_TOOL,
    ],
    handlers={
        "profil_aktualisieren": _profil_aktualisieren,
        "alltagstauglichkeit_zeigen": _alltag_zeigen,
        "ladeloesungen_vergleichen": _laden_vergleichen,
        "fahrzeuge_vorschlagen": _fahrzeuge_vorschlagen,
        "kosten_vergleichen": _kosten_vergleichen,
        "bedenken_adressieren": _bedenken_adressieren,
        "naechsten_schritt_anbieten": _abschluss,
    },
    state_factory=MobilitaetState,
)
