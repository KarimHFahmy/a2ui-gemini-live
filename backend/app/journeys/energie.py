"""Journey 01 — Der persönliche Energieberater."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..a2ui import composer_energie as compose
from ..a2ui import composer_shared as shared
from ..domain import energie as calc
from .base import GEMEINSAME_HALTUNG, BEDENKEN_TOOL, Journey, ToolResult


@dataclass
class EnergieState:
    """What the session knows about this household."""

    profil: calc.Gebaeudeprofil = field(default_factory=calc.Gebaeudeprofil)
    profil_gesetzt: bool = False
    einkommensbonus: bool = False
    gewaehltes_szenario: str = "waermepumpe"
    offene_punkte: list[str] = field(default_factory=list)

    def szenarien(self) -> list[calc.Szenario]:
        return calc.szenarien(self.profil, einkommensbonus=self.einkommensbonus)

    def snapshot(self) -> dict[str, Any]:
        check = calc.eignung(self.profil)
        szenarien = self.szenarien()
        gewaehlt = next(
            (s for s in szenarien if s.id == self.gewaehltes_szenario), szenarien[1]
        )
        return {
            "journey": "energie",
            "gebaeude": {
                "baujahr": self.profil.baujahr,
                "wohnflaeche_qm": self.profil.wohnflaeche_qm,
                "heizung": self.profil.heizung,
                "sanierungsstand": self.profil.sanierungsstand,
                "personen": self.profil.personen,
                "waermebedarf_kwh_a": calc.waermebedarf_kwh_a(self.profil),
            },
            "eignung": {
                "urteil": check["urteil"],
                "score": check["score"],
                "jaz": check["jaz"],
                "vorlauftemperatur_c": check["vorlauftemperatur_c"],
            },
            "empfehlung": {
                "szenario": gewaehlt.label,
                "investition_eur": gewaehlt.investition_eur,
                "foerderung_eur": gewaehlt.foerderung_eur,
                "eigenanteil_eur": gewaehlt.eigenanteil_eur,
                "energiekosten_eur_a": gewaehlt.energiekosten_eur_a,
                "massnahmen": gewaehlt.massnahmen,
            },
            "prioritaeten": self.profil.prioritaeten,
            "bedenken": self.profil.bedenken,
            "offene_punkte": self.offene_punkte,
        }


# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = f"""
Du bist der persönliche Energieberater einer deutschen Energie-Experience.
Du hilfst Menschen, die über Heizung, Sanierung und ihren Weg zur Energiewende
nachdenken — und dabei oft überfordert sind.

Die typische Person hat ein älteres Einfamilienhaus, eine Gasheizung, die in die
Jahre kommt, und zwei Sorgen: „Reicht eine Wärmepumpe im Winter?" und „Lohnt
sich das für mich überhaupt?" Deine Aufgabe ist es, aus dieser Unsicherheit ein
verständliches Zukunftsbild zu machen.

{GEMEINSAME_HALTUNG}

## Dein Gesprächsbogen

1. **Zuhören.** Lass die Person ihre Situation schildern. Baujahr, Heizung,
   Fläche und die eigentliche Sorge ergeben sich meist von selbst.
2. **Verstehen zeigen.** Sobald du Gebäude und Heizung kennst, rufe
   `profil_aktualisieren` auf. Fehlendes schätzt du plausibel und markierst es
   als offenen Punkt — frag nicht alles ab.
3. **Die Kernsorge zuerst.** Mit `waermepumpen_eignung_zeigen` beantwortest du,
   ob das Haus geeignet ist. Das ist fast immer die eigentliche Frage.
4. **Wege zeigen.** `szenarien_vergleichen` stellt die Optionen nebeneinander.
5. **Rechnen.** `wirtschaftlichkeit_zeigen` für den gewählten Weg.
6. **Förderung und Reihenfolge.** `foerderung_und_fahrplan_zeigen`.
7. **Abschluss.** `naechsten_schritt_anbieten` fasst zusammen und übergibt.

Du musst diese Reihenfolge nicht erzwingen. Wenn jemand direkt nach Kosten
fragt, geh dorthin. Aber lass keinen Schritt weg, den die Person braucht.

## Fachliches

- Entscheidend für die Eignung ist die **nötige Vorlauftemperatur**, nicht die
  Außentemperatur. Das ist der wichtigste Satz dieser Beratung.
- Frag nach der Art der Heizkörper (groß und flach, oder alt und schmal?) oder
  ob eine Fußbodenheizung vorhanden ist — daraus folgt die Vorlauftemperatur.
- Bei hohem spezifischen Wärmebedarf ist die Gebäudehülle der größere Hebel als
  die Heiztechnik. Sag das offen, auch wenn es die teurere Antwort ist.
- Die Förderung setzt voraus, dass der Antrag **vor** der Beauftragung gestellt
  wird. Dieser Hinweis gehört in jede Beratung.

## Eröffnung

Begrüße die Person warm und knapp und stelle **eine** offene Frage zu ihrem
Zuhause. Frage nicht nach Daten, sondern nach ihrer Situation.
""".strip()


OPENER = (
    "Begrüße die Person kurz und warm auf Deutsch und stelle eine offene Frage "
    "zu ihrem Zuhause und dem, was sie gerade beschäftigt. Halte dich sehr kurz."
)


# ---------------------------------------------------------------------------
# Tool declarations
# ---------------------------------------------------------------------------

_PROFIL_TOOL: dict[str, Any] = {
    "name": "profil_aktualisieren",
    "description": (
        "Zeigt auf dem Bildschirm, was du über das Zuhause der Person "
        "verstanden hast, und aktualisiert die Berechnungsgrundlage. Rufe das "
        "früh auf und danach jedes Mal, wenn du etwas Neues erfährst oder die "
        "Person dich korrigiert. Übergib nur, was du tatsächlich weißt oder "
        "plausibel schätzen kannst."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "baujahr": {"type": "INTEGER", "description": "Baujahr des Gebäudes."},
            "wohnflaeche_qm": {
                "type": "NUMBER",
                "description": "Beheizte Wohnfläche in Quadratmetern.",
            },
            "heizung": {
                "type": "STRING",
                "enum": ["gas", "oel", "fernwaerme", "nachtspeicher", "waermepumpe"],
                "description": "Die heutige Heizung.",
            },
            "sanierungsstand": {
                "type": "STRING",
                "enum": ["unsaniert", "teilsaniert", "saniert"],
                "description": (
                    "Zustand der Gebäudehülle. teilsaniert z. B. wenn Fenster "
                    "oder Dach schon erneuert wurden."
                ),
            },
            "waermesystem": {
                "type": "STRING",
                "enum": [
                    "fussbodenheizung",
                    "flaechenheizkoerper_gross",
                    "heizkoerper_standard",
                    "heizkoerper_klein_alt",
                ],
                "description": (
                    "Wie die Wärme im Haus verteilt wird. Bestimmt die nötige "
                    "Vorlauftemperatur und damit die Eignung."
                ),
            },
            "personen": {"type": "INTEGER", "description": "Personen im Haushalt."},
            "verbrauch_kwh_a": {
                "type": "NUMBER",
                "description": (
                    "Gemessener Jahresverbrauch in kWh, falls die Person ihn "
                    "kennt. Schlägt jede Schätzung — frag ruhig danach."
                ),
            },
            "pv_vorhanden": {
                "type": "BOOLEAN",
                "description": "Ob bereits eine PV-Anlage auf dem Dach ist.",
            },
            "prioritaeten": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": (
                    "Was der Person wichtig ist, in ihren Worten. Beispiel: "
                    "'Unabhängigkeit', 'Wirtschaftlichkeit', 'Klimaschutz'."
                ),
            },
            "bedenken": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Geäußerte Sorgen, in den Worten der Person.",
            },
            "offene_punkte": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": (
                    "Was du noch nicht weißt und geschätzt hast. Wird der Person "
                    "transparent angezeigt."
                ),
            },
        },
    },
}

_EIGNUNG_TOOL: dict[str, Any] = {
    "name": "waermepumpen_eignung_zeigen",
    "description": (
        "Zeigt, ob das Haus für eine Wärmepumpe geeignet ist: nötige "
        "Vorlauftemperatur, erwartete Jahresarbeitszahl, Heizlast und der "
        "Verlauf der Heizlast über den Winter. Beantwortet die Sorge, ob es im "
        "Winter reicht. Rufe das auf, sobald du Gebäude, Heizung und "
        "Wärmeverteilung kennst."
    ),
    "parameters": {"type": "OBJECT", "properties": {}},
}

_SZENARIEN_TOOL: dict[str, Any] = {
    "name": "szenarien_vergleichen",
    "description": (
        "Stellt die möglichen Wege nebeneinander: weiter wie bisher, "
        "Wärmepumpe, Wärmepumpe mit Dämmung, Wärmepumpe mit PV. Mit "
        "Investition, Förderung, Eigenanteil, laufenden Kosten und CO2. "
        "Die Person kann auf dem Bildschirm einen Weg auswählen."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "empfohlen": {
                "type": "STRING",
                "enum": ["bestand", "waermepumpe", "waermepumpe_huelle", "waermepumpe_pv"],
                "description": (
                    "Welchen Weg du auf Basis des Gesprächs hervorhebst. "
                    "Orientiere dich an den Prioritäten der Person."
                ),
            }
        },
    },
}

_WIRTSCHAFT_TOOL: dict[str, Any] = {
    "name": "wirtschaftlichkeit_zeigen",
    "description": (
        "Rechnet einen Weg über 20 Jahre durch: kumulierte Gesamtkosten "
        "gegenüber 'weiter wie bisher', Break-even-Punkt und jährliche "
        "Ersparnis. Nutze das, wenn die Person wissen will, ob es sich lohnt."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "szenario": {
                "type": "STRING",
                "enum": ["waermepumpe", "waermepumpe_huelle", "waermepumpe_pv"],
                "description": "Der Weg, der durchgerechnet werden soll.",
            }
        },
        "required": ["szenario"],
    },
}

_FOERDERUNG_TOOL: dict[str, Any] = {
    "name": "foerderung_und_fahrplan_zeigen",
    "description": (
        "Zeigt den erwarteten Zuschuss, wie sich die Förderquote zusammensetzt, "
        "und den Umsetzungsfahrplan in fünf Schritten inklusive des Hinweises, "
        "dass der Antrag vor der Beauftragung gestellt werden muss."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "szenario": {
                "type": "STRING",
                "enum": ["waermepumpe", "waermepumpe_huelle", "waermepumpe_pv"],
            },
            "einkommensbonus": {
                "type": "BOOLEAN",
                "description": (
                    "Nur auf true setzen, wenn die Person von sich aus gesagt "
                    "hat, dass das Haushaltseinkommen unter der Bonusgrenze "
                    "liegt. Frag nicht aktiv danach."
                ),
            },
        },
        "required": ["szenario"],
    },
}

_ABSCHLUSS_TOOL: dict[str, Any] = {
    "name": "naechsten_schritt_anbieten",
    "description": (
        "Schließt die Beratung ab: Zusammenfassung, Empfehlung mit Begründung, "
        "offene Punkte und ein konkreter nächster Schritt. Rufe das auf, wenn "
        "die Person genug gesehen hat oder selbst nach dem nächsten Schritt fragt."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "empfehlung": {
                "type": "STRING",
                "description": (
                    "Zwei bis drei Sätze in Alltagssprache: was du empfiehlst "
                    "und warum es zu dieser Person passt."
                ),
            },
            "begruendung": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Zwei bis vier Gründe, die für diesen Weg sprechen.",
            },
            "offene_punkte": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": (
                    "Was vor einer Entscheidung noch zu klären ist. Ehrlich "
                    "benennen, nicht beschönigen."
                ),
            },
            "schritt": {
                "type": "STRING",
                "enum": ["beratungstermin", "vor_ort_check", "foerder_check"],
                "description": "Der konkrete nächste Schritt.",
            },
        },
        "required": ["empfehlung", "begruendung", "schritt"],
    },
}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _profil_aktualisieren(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    profil = state.profil
    for feld in (
        "baujahr",
        "wohnflaeche_qm",
        "heizung",
        "sanierungsstand",
        "waermesystem",
        "personen",
        "verbrauch_kwh_a",
        "pv_vorhanden",
        "prioritaeten",
        "bedenken",
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
            "waermebedarf_kwh_a": calc.waermebedarf_kwh_a(profil),
            "hinweis": (
                "Das Profil ist jetzt auf dem Bildschirm. Bestätige kurz, was du "
                "verstanden hast, ohne alle Werte vorzulesen."
            ),
        },
    )


def _eignung_zeigen(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    check = calc.eignung(state.profil)
    surface = compose.eignung_surface(state.profil)
    return ToolResult(
        surfaces=[surface],
        result={
            "urteil": check["urteil"],
            "score": check["score"],
            "vorlauftemperatur_c": check["vorlauftemperatur_c"],
            "jaz": check["jaz"],
            "heizlast_kw": check["heizlast_kw"],
            "strombedarf_kwh_a": check["strombedarf_kwh_a"],
            "hinweise": check["hinweise"],
            "massnahmen": check["massnahmen"],
        },
    )


def _szenarien_vergleichen(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    empfohlen = args.get("empfohlen") or "waermepumpe"
    state.gewaehltes_szenario = empfohlen
    szenarien = state.szenarien()
    verfuegbar = {s.id for s in szenarien}
    if empfohlen not in verfuegbar:
        empfohlen = "waermepumpe"
        state.gewaehltes_szenario = empfohlen

    surface = compose.szenarien_surface(state.profil, szenarien, empfohlen_id=empfohlen)
    return ToolResult(
        surfaces=[surface],
        result={
            "szenarien": [
                {
                    "id": s.id,
                    "label": s.label,
                    "eigenanteil_eur": s.eigenanteil_eur,
                    "energiekosten_eur_a": s.energiekosten_eur_a,
                    "co2_kg_a": s.co2_kg_a,
                }
                for s in szenarien
            ],
            "hervorgehoben": empfohlen,
        },
    )


def _wirtschaftlichkeit_zeigen(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    szenarien = state.szenarien()
    fokus_id = args.get("szenario") or state.gewaehltes_szenario
    if fokus_id not in {s.id for s in szenarien}:
        fokus_id = "waermepumpe"
    state.gewaehltes_szenario = fokus_id

    bestand = next(s for s in szenarien if s.id == "bestand")
    fokus = next(s for s in szenarien if s.id == fokus_id)
    amort = calc.amortisation(bestand, fokus)

    surface = compose.wirtschaftlichkeit_surface(
        state.profil, szenarien, fokus_id=fokus_id
    )
    return ToolResult(
        surfaces=[surface],
        result={
            "szenario": fokus.label,
            "eigenanteil_eur": fokus.eigenanteil_eur,
            "ersparnis_eur_a": round(
                bestand.betriebskosten_eur_a - fokus.betriebskosten_eur_a
            ),
            "break_even_jahre": amort["jahre"],
            "break_even_erreichbar": amort["erreichbar"],
        },
    )


def _foerderung_zeigen(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    state.einkommensbonus = bool(args.get("einkommensbonus", state.einkommensbonus))
    szenarien = state.szenarien()
    szenario_id = args.get("szenario") or state.gewaehltes_szenario
    if szenario_id not in {s.id for s in szenarien}:
        szenario_id = "waermepumpe"
    state.gewaehltes_szenario = szenario_id
    szenario = next(s for s in szenarien if s.id == szenario_id)

    # Nur der Heizungsanteil ist über die Heizungsförderung förderfähig.
    details = calc.foerderung(
        min(szenario.investition_eur, calc.dd.FOERDERUNG["hoechstkosten_efh_eur"]),
        einkommensbonus=state.einkommensbonus,
    )

    surface = compose.foerderung_surface(state.profil, szenario, details)
    return ToolResult(
        surfaces=[surface],
        result={
            "foerderquote": details["satz"],
            "betrag_eur": details["betrag_eur"],
            "eigenanteil_eur": szenario.eigenanteil_eur,
            "hinweis": (
                "Antrag muss vor Beauftragung gestellt werden — das ist der "
                "Punkt, den du unbedingt aussprechen solltest."
            ),
        },
    )


def _bedenken_adressieren(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    surface = shared.bedenken_surface(
        titel=args.get("titel", "Ihre Frage"),
        einordnung=args.get("einordnung", ""),
        punkte=args.get("punkte") or [],
    )
    return ToolResult(surfaces=[surface], result={"status": "angezeigt"})


_SCHRITT_LABEL = {
    "beratungstermin": "Beratungstermin vereinbaren",
    "vor_ort_check": "Vor-Ort-Check anfragen",
    "foerder_check": "Förderfähigkeit prüfen lassen",
}


def _abschluss(state: EnergieState, args: dict[str, Any]) -> ToolResult:
    schritt = args.get("schritt", "beratungstermin")
    offene = args.get("offene_punkte") or state.offene_punkte

    surface = shared.handover_surface(
        journey="energie",
        titel="Ihr Weg zur neuen Heizung",
        empfehlung=args.get("empfehlung", ""),
        begruendung=args.get("begruendung") or [],
        offene_punkte=offene,
        schritt_label=_SCHRITT_LABEL.get(schritt, "Beratungstermin vereinbaren"),
        schritt_event=f"handover_{schritt}",
    )
    return ToolResult(
        surfaces=[surface],
        result={"status": "abgeschlossen", "zusammenfassung": state.snapshot()},
    )


JOURNEY = Journey(
    id="energie",
    label="Mein Zuhause",
    tagline=(
        "Von komplexen Sanierungsfragen zur verständlichen persönlichen Energiewende."
    ),
    opener=OPENER,
    system_instruction=SYSTEM_INSTRUCTION,
    function_declarations=[
        _PROFIL_TOOL,
        _EIGNUNG_TOOL,
        _SZENARIEN_TOOL,
        _WIRTSCHAFT_TOOL,
        _FOERDERUNG_TOOL,
        BEDENKEN_TOOL,
        _ABSCHLUSS_TOOL,
    ],
    handlers={
        "profil_aktualisieren": _profil_aktualisieren,
        "waermepumpen_eignung_zeigen": _eignung_zeigen,
        "szenarien_vergleichen": _szenarien_vergleichen,
        "wirtschaftlichkeit_zeigen": _wirtschaftlichkeit_zeigen,
        "foerderung_und_fahrplan_zeigen": _foerderung_zeigen,
        "bedenken_adressieren": _bedenken_adressieren,
        "naechsten_schritt_anbieten": _abschluss,
    },
    state_factory=EnergieState,
)
