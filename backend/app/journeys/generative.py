"""The experiment: the model writes the A2UI itself.

Everywhere else in this demo the model chooses *when* to show something and the
composers choose *what* — see `docs/architecture.md`, "Semantic tools instead of
generated UI". That is an argument, and an argument is worth testing against the
thing it rejects.

So this journey removes the composers. The agent gets three tools:

    profil_merken     remember what you understood, as free-form JSON
    daten_abrufen     ask for the computed figures for one area
    oberflaeche_zeigen  emit an A2UI component tree, by hand

The catalog reference below is what the model has to hold in its head to do
that, and its length is most of the finding. Everything else — the renderer,
the transport, the audio, the domain arithmetic — is unchanged, so the only
variable is who builds the tree.

The numbers still come from `app.domain`. A version where the model invents
those too would be a strawman: it would fail for reasons everyone already
agrees on. This is the strongest form of the generative case — real figures,
free layout — which is the only version worth comparing against.

Run it from the landing page: both journeys appear a second time, marked
"frei generiert". `docs/experiment-generative-ui.md` has what to look for.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import fields
from typing import Any, Literal

from google.adk.tools import ToolContext

from ..a2ui import protocol
from ..a2ui.surface import Surface
from ..config import get_settings
from ..domain import demo_data as dd
from ..domain import energie as calc_energie
from ..domain import mobilitaet as calc_mobilitaet
from .base import HALTUNG, Journey, load_profile, push, save_profile

logger = logging.getLogger(__name__)

#: Where the running tally of what the model emitted lives.
_METRICS_KEY = "_genui_metrics"


# ---------------------------------------------------------------------------
# The catalog, as the model has to know it
# ---------------------------------------------------------------------------

_KATALOG = """
## Das A2UI-Format

Du baust Oberflächen, indem du `oberflaeche_zeigen` mit einer **flachen Liste**
von Komponenten aufrufst. Verschachtelt wird über `id`-Verweise, nicht über
verschachteltes JSON.

Regeln, die immer gelten:

- Jede Komponente hat eine eindeutige `id` und ein `component`.
- Genau **eine** Komponente hat `"id": "root"`. Sie ist die Wurzel.
- Eltern verweisen über `children` (Liste von ids) oder `child` (eine id).
- Verweise auf nicht existierende ids machen die Ansicht kaputt. Prüfe das.
- Text darf einfaches Markdown enthalten (`**fett**`, `- Punkt`).

Beispiel — Überschrift und eine Karte:

```json
[
  {"id": "t1", "component": "Text", "text": "Kosten", "variant": "caption"},
  {"id": "t2", "component": "Text", "text": "Über 4 Jahre", "variant": "h2"},
  {"id": "kopf", "component": "Column", "children": ["t1", "t2"]},
  {"id": "t3", "component": "Text", "text": "Das E-Auto ist teurer."},
  {"id": "karte", "component": "StatCard", "title": "Elektro gegen Verbrenner",
   "metric": "1.907 €", "metricLabel": "Nachteil", "tone": "caution",
   "child": "t3"},
  {"id": "root", "component": "Column", "children": ["kopf", "karte"]}
]
```

## Die erlaubten Komponenten

Nur diese. Alles andere wird nicht gerendert.

**Layout**
- `Column` / `Row` — `children` (Liste von ids), optional `align`, `justify`,
  `weight` (Zahl; in einer Row heißt `weight: 1` gleiche Breite).
- `Card` — `child` (eine id). Für mehrere Kinder eine Column hineinlegen.
- `Divider` — trennt, keine Pflichtfelder.

**Text**
- `Text` — `text`, optional `variant`: `h2` `h3` `h4` `h5` `caption` `body`.
  `caption` ist die kleine graue Zeile über einer Überschrift.

**Kennzahlkarte (bevorzugt für jede Zahl mit Bedeutung)**
- `StatCard` — `title`, optional `metric` (die große Zahl), `metricLabel`
  (die Einheit daneben), `tone`, `child` (id eines Text mit der Erklärung),
  `weight`.
  `tone` ist `positive` (spricht für die Person), `caution` (echter Nachteil)
  oder `neutral` (bloße Tatsache). **Färbe nichts schön**: eine Zahl, die
  teurer bedeutet, ist `caution`.

**Daten**
- `MetricChart` — `title`, `subtitle`, `chartType` (`bar` `groupedBar`
  `stackedBar` `line`), `categories` (Liste von Texten), `series` (Liste von
  `{"label": "...", "werte": [Zahlen]}`), `unit`, `valueFormat`
  (`number` `currency` `percent`).
- `ComparisonTable` — `title`, `columns` (Liste von `{"id": "...",
  "label": "..."}`), `rows` (Liste von `{"label": "...", "werte": ["..."],
  "hervorheben": true, "akzent": "positive"}`), `highlight` (Spalten-id).

**Interaktion**
- `Button` — `child` (id eines Text), `variant` (`primary` `default`
  `borderless`), `action`:
  `{"event": {"name": "dein_event_name", "context": {}}}`.
- `ChoicePicker` — `label`, `options` (Liste von `{"label": "...",
  "value": "..."}`), `value` (Datenbindung, siehe unten), `displayStyle`
  (`chips` oder `checkbox`).
- `Slider` — `label`, `min`, `max` (ganze Zahlen), `value` (Datenbindung).
- `Modal` — `trigger` (id) und `content` (id). Für die Annahmen.

**Listen aus Daten**
- `List` — `children` als Vorlage: `{"componentId": "vorlage_id",
  "path": "/pfad"}`, plus `direction` (`vertical` `horizontal`).
  In der Vorlage sind Bindungen **relativ** zum Element: `{"path": "titel"}`.

## Datenbindung

Statt eines festen Werts kannst du überall `{"path": "/schluessel"}` schreiben.
Der Wert kommt dann aus dem Datenmodell, das du als `data_json` mitschickst.
Zwei Komponenten, die denselben Pfad lesen, bleiben synchron — genau so hängen
ein `ChoicePicker` und die Hervorhebung einer Tabelle zusammen.

## Die Namen der Ansichten

Die `surface_id` ist nicht nur ein Name — die Oberfläche verwendet sie:

- `profil` landet in der Seitenspalte und bleibt dort stehen. Baue diese
  Ansicht, sobald du etwas über die Person weißt, und ruf sie mit derselben id
  erneut auf, wenn sich etwas ändert. Kurz halten: Zeile für Zeile, was du
  verstanden hast.
- Die ids aus deinem Gesprächsbogen ({steps}) füllen die Fortschrittsleiste.
  Nimm für die Ansicht zu einem Bereich genau den Namen des Bereichs.
- Alles andere darfst du frei benennen.

## Was eine gute Ansicht ausmacht

- Eine Ansicht beantwortet **eine** Frage. Kein Dashboard.
- Über jeder Ansicht eine `caption` und eine `h2`.
- Zahlen gehören in `StatCard`, nicht in Fließtext.
- Ganz unten ein `Modal`, dessen Inhalt die Annahmen und die Datenquelle nennt.
- Zwei bis vier Karten in einer `Row`, mit `weight: 1`.
""".strip()


def katalog(journey_id: str) -> str:
    """The catalog reference, with this journey's step ids filled in.

    A plain replace rather than `format`, because the text is mostly JSON and
    every brace in it is literal.
    """
    ids = ", ".join(f"`{surface_id}`" for surface_id, _ in _STEPS[journey_id])
    return _KATALOG.replace("{steps}", ids)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def _profile_class(journey_id: str) -> type:
    return (
        calc_energie.Gebaeudeprofil
        if journey_id == "energie"
        else calc_mobilitaet.Mobilitaetsprofil
    )


def _record(tool_context: ToolContext, entry: dict[str, Any]) -> None:
    """Keeps a tally, and prints it, so a run can be compared with a composed one.

    The whole point of the experiment is the numbers you cannot feel: how much
    JSON the model had to produce for one screen, and how often it had to be
    sent back. Both go to the server log as they happen, because that is where
    someone running the demo will actually see them.
    """
    log: list[dict[str, Any]] = list(tool_context.state.get(_METRICS_KEY, []))
    tool_context.state[_METRICS_KEY] = [*log, entry]

    if entry.get("ok"):
        logger.info(
            "genui %-16s %4d components  %5d chars  %6.1f ms",
            entry.get("surface", "?"),
            entry.get("komponenten", 0),
            entry.get("chars", 0),
            entry.get("ms", 0.0),
        )
    else:
        logger.warning(
            "genui %-16s REJECTED after %5d chars: %s",
            entry.get("surface", "?"),
            entry.get("chars", 0),
            entry.get("grund", "?"),
        )


def make_tools(journey_id: str) -> list[Any]:
    """Builds the three tools, closed over which journey they belong to."""
    profile_class = _profile_class(journey_id)
    known = {f.name for f in fields(profile_class)}

    def profil_merken(tool_context: ToolContext, aenderungen_json: str) -> dict[str, Any]:
        """Merkt sich, was du über die Person verstanden hast.

        Args:
            aenderungen_json: Ein JSON-Objekt mit den Feldern, die du gerade
                verstanden hast. Erlaubte Felder bekommst du zurück, wenn du
                etwas Unbekanntes schickst. Beispiel für Energie:
                {"baujahr": 1985, "wohnflaeche_qm": 160, "heizung": "gas"}.
                Beispiel für Mobilität:
                {"taeglich_km": 55, "lademoeglichkeit": "wallbox_zuhause"}.
        """
        try:
            changes = json.loads(aenderungen_json)
        except json.JSONDecodeError as exc:
            return {"fehler": f"Kein gültiges JSON: {exc}"}
        if not isinstance(changes, dict):
            return {"fehler": "Erwartet wird ein JSON-Objekt."}

        profile = load_profile(tool_context, profile_class)
        applied, ignored = {}, []
        for key, value in changes.items():
            if key in known:
                setattr(profile, key, value)
                applied[key] = value
            else:
                ignored.append(key)
        save_profile(tool_context, profile)

        result: dict[str, Any] = {"uebernommen": applied}
        if ignored:
            result["unbekannt"] = ignored
            result["erlaubte_felder"] = sorted(known)
        return result

    def daten_abrufen(tool_context: ToolContext, bereich: str) -> dict[str, Any]:
        """Liefert die gerechneten Zahlen für einen Bereich.

        Erfinde niemals Zahlen. Alles, was du zeigst, muss von hier kommen.

        Args:
            bereich: Für „Mein Zuhause": `eignung`, `szenarien`,
                `wirtschaftlichkeit`, `foerderung`, `annahmen`.
                Für „Meine Mobilität": `reichweite`, `woche`, `langstrecke`,
                `laden`, `fahrzeuge`, `kosten`, `annahmen`.
        """
        profile = load_profile(tool_context, profile_class)
        try:
            data = _facts(journey_id, profile, bereich)
        except KeyError:
            return {
                "fehler": f"Unbekannter Bereich {bereich!r}.",
                "verfuegbar": sorted(_AREAS[journey_id]),
            }
        return data

    def oberflaeche_zeigen(
        tool_context: ToolContext,
        surface_id: str,
        titel: str,
        components_json: str,
        data_json: str = "{}",
    ) -> dict[str, Any]:
        """Zeigt eine Oberfläche, die du selbst gebaut hast.

        Args:
            surface_id: Kurzer Bezeichner, z. B. `kosten`. Rufst du dieselbe id
                erneut auf, wird die Ansicht ersetzt statt eine zweite anzulegen.
            titel: Überschrift für die Ansicht, in einfachen Worten.
            components_json: Die flache Liste der Komponenten als JSON-Array.
                Genau eine Komponente muss `"id": "root"` haben.
            data_json: Das Datenmodell als JSON-Objekt, falls du Bindungen
                (`{"path": "/x"}`) verwendest. Sonst weglassen.
        """
        started = time.perf_counter()

        try:
            components = json.loads(components_json)
            data = json.loads(data_json or "{}")
        except json.JSONDecodeError as exc:
            _record(
                tool_context,
                {"surface": surface_id, "ok": False, "grund": "json", "chars": len(components_json)},
            )
            return {
                "fehler": f"Kein gültiges JSON: {exc}",
                "hinweis": "Schick die Liste noch einmal, vollständig und gültig.",
            }

        if not isinstance(components, list):
            return {"fehler": "components_json muss ein JSON-Array sein."}

        try:
            protocol.validate_tree(components)
        except ValueError as exc:
            _record(
                tool_context,
                {
                    "surface": surface_id,
                    "ok": False,
                    "grund": str(exc),
                    "chars": len(components_json),
                    "komponenten": len(components),
                },
            )
            return {
                "fehler": str(exc),
                "hinweis": (
                    "Bau den Baum neu: genau eine Komponente mit id 'root', "
                    "keine doppelten ids, und jedes Kind muss existieren."
                ),
            }

        push(
            tool_context,
            Surface(
                surface_id=surface_id,
                title=titel,
                components=components,
                data=data if isinstance(data, dict) else {},
            ),
        )
        _record(
            tool_context,
            {
                "surface": surface_id,
                "ok": True,
                "chars": len(components_json) + len(data_json or ""),
                "komponenten": len(components),
                "ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return {
            "status": "angezeigt",
            "komponenten": len(components),
            "hinweis": "Sag jetzt in ein bis zwei Sätzen, was zu sehen ist.",
        }

    return [profil_merken, daten_abrufen, oberflaeche_zeigen]


# ---------------------------------------------------------------------------
# The figures, unchanged — only the layout is the model's job here
# ---------------------------------------------------------------------------

_AREAS = {
    "energie": {
        "eignung",
        "szenarien",
        "wirtschaftlichkeit",
        "foerderung",
        "annahmen",
    },
    "mobilitaet": {
        "reichweite",
        "woche",
        "langstrecke",
        "laden",
        "fahrzeuge",
        "kosten",
        "annahmen",
    },
}


def _facts(journey_id: str, profile: Any, bereich: str) -> dict[str, Any]:
    if bereich not in _AREAS[journey_id]:
        raise KeyError(bereich)

    if journey_id == "energie":
        if bereich == "eignung":
            return calc_energie.eignung(profile)
        if bereich == "annahmen":
            return {"annahmen": calc_energie.annahmen(profile), "quelle": dd.QUELLE_ENERGIE}

        szenarien = calc_energie.szenarien(profile)
        rows = [
            {
                "id": s.id,
                "label": s.label,
                "beschreibung": s.beschreibung,
                "investition_eur": s.investition_eur,
                "foerderung_eur": s.foerderung_eur,
                "eigenanteil_eur": s.eigenanteil_eur,
                "energiekosten_eur_a": s.energiekosten_eur_a,
                "betriebskosten_eur_a": s.betriebskosten_eur_a,
                "co2_kg_a": s.co2_kg_a,
                "massnahmen": s.massnahmen,
            }
            for s in szenarien
        ]
        if bereich == "szenarien":
            return {"szenarien": rows}
        if bereich == "wirtschaftlichkeit":
            bestand = szenarien[0]
            return {
                "verlauf": calc_energie.kostenverlauf(szenarien),
                "amortisation": {
                    s.id: calc_energie.amortisation(bestand, s) for s in szenarien[1:]
                },
                "szenarien": rows,
            }
        details = calc_energie.foerderung(
            min(szenarien[1].investition_eur, dd.FOERDERUNG["hoechstkosten_efh_eur"])
        )
        return {"foerderung": details, "eigenanteil_eur": szenarien[1].eigenanteil_eur}

    if bereich == "reichweite":
        return calc_mobilitaet.reichweite(profile)
    if bereich == "woche":
        return calc_mobilitaet.wochenprofil(profile)
    if bereich == "langstrecke":
        return calc_mobilitaet.langstrecke(profile)
    if bereich == "laden":
        return calc_mobilitaet.ladeoptionen(profile)
    if bereich == "fahrzeuge":
        return {"vorschlaege": calc_mobilitaet.fahrzeugvorschlaege(profile)}
    if bereich == "kosten":
        return calc_mobilitaet.kostenvergleich(profile)
    return {
        "annahmen": calc_mobilitaet.annahmen(profile),
        "quelle": dd.QUELLE_MOBILITAET,
    }


# ---------------------------------------------------------------------------
# The journeys
# ---------------------------------------------------------------------------

_BOGEN = {
    "energie": """
1. **Zuhören**, dann `profil_merken`.
2. `daten_abrufen("eignung")` und eine Ansicht zur Eignung bauen — das ist die
   eigentliche Frage: passt eine Wärmepumpe zu diesem Haus?
3. `daten_abrufen("szenarien")` und die Wege gegenüberstellen.
4. `daten_abrufen("wirtschaftlichkeit")` für die Rechnung über 20 Jahre.
5. `daten_abrufen("foerderung")` für Zuschuss und Reihenfolge.
6. Zum Schluss eine Ansicht mit Empfehlung und nächstem Schritt.
""",
    "mobilitaet": """
1. **Zuhören**, dann `profil_merken`.
2. `daten_abrufen("reichweite")` und `("woche")` — die Alltagsfrage zuerst.
3. `daten_abrufen("laden")`: wo geladen wird, entscheidet über die Kosten.
   Diese Reihenfolge vor der Fahrzeugwahl, nicht danach.
4. `daten_abrufen("fahrzeuge")` für passende Klassen.
5. `daten_abrufen("kosten")` für Elektro gegen Verbrenner.
6. Zum Schluss eine Ansicht mit Empfehlung und nächstem Schritt.
""",
}

_ROLLE = {
    "energie": (
        "Du bist der persönliche Energieberater einer deutschen Energie-"
        "Experience. Die typische Person hat ein älteres Einfamilienhaus, eine "
        "Gasheizung, die in die Jahre kommt, und zwei Sorgen: „Reicht eine "
        "Wärmepumpe im Winter?“ und „Lohnt sich das für mich?“"
    ),
    "mobilitaet": (
        "Du bist der persönliche Mobilitätsberater einer deutschen E-Mobilitäts-"
        "Experience. Die typische Person pendelt täglich, fährt gelegentlich "
        "lange Strecken und hat keine eigene Wallbox."
    ),
}

_TOPICS = {
    "energie": [
        "ob eine Wärmepumpe zu Ihrem Haus passt",
        "was der Umstieg kostet und ab wann er sich lohnt",
        "welche Förderung Sie bekommen",
    ],
    "mobilitaet": [
        "ob ein E-Auto zu Ihren Wegen passt",
        "wo Sie laden würden und was das kostet",
        "welches Fahrzeug zu Ihnen passt",
    ],
}

_STEPS = {
    "energie": [
        ("profil", "Ihre Situation"),
        ("eignung", "Eignung"),
        ("szenarien", "Wege"),
        ("wirtschaftlichkeit", "Wirtschaftlichkeit"),
        ("foerderung", "Förderung"),
    ],
    "mobilitaet": [
        ("profil", "Ihr Alltag"),
        ("reichweite", "Reichweite"),
        ("laden", "Laden"),
        ("fahrzeuge", "Fahrzeuge"),
        ("kosten", "Kosten"),
    ],
}


def _instruction(journey_id: str) -> str:
    from .base import join_de

    return f"""
{_ROLLE[journey_id]}

Du baust die Oberfläche in diesem Gespräch **selbst**. Es gibt keine fertigen
Ansichten: du rufst Zahlen ab und entscheidest, wie sie aussehen sollen.

{HALTUNG}

## Dein Gesprächsbogen
{_BOGEN[journey_id]}

## Zahlen

Alle Zahlen kommen aus `daten_abrufen`. Erfinde nichts, rechne nichts im Kopf
und runde nichts um, was du nicht gerechnet hast. Formatiere deutsch:
`1.907 €`, `3,8`, `45 °C`.

{katalog(journey_id)}

## Eröffnung

Sag als Erstes, wobei du helfen kannst: {join_de(_TOPICS[journey_id])}. Stelle
danach genau **eine** offene Frage. Zusammen höchstens drei Sätze.
""".strip()


def build(journey_id: Literal["energie", "mobilitaet"]) -> Journey:
    from .base import opening_line

    label = "Mein Zuhause" if journey_id == "energie" else "Meine Mobilität"
    frage = (
        "zum Zuhause der Person"
        if journey_id == "energie"
        else "zum Alltag und den typischen Wegen der Person"
    )
    return Journey(
        journey_id=f"{journey_id}_frei",
        label=f"{label} · frei generiert",
        tagline=(
            "Experiment: dieselbe Beratung, aber das Modell baut die Oberfläche "
            "selbst — ohne Composer."
        ),
        opener=opening_line(_TOPICS[journey_id], frage),
        instruction=_instruction(journey_id),
        tools=make_tools(journey_id),
        model=get_settings().model,
        steps=_STEPS[journey_id],
        topics=_TOPICS[journey_id],
    )


def metrics(tool_context_state: dict[str, Any]) -> dict[str, Any]:
    """A run's tally: how much JSON, how many components, how often wrong."""
    log = list(tool_context_state.get(_METRICS_KEY, []))
    ok = [e for e in log if e.get("ok")]
    return {
        "versuche": len(log),
        "angezeigt": len(ok),
        "abgelehnt": len(log) - len(ok),
        "zeichen_gesamt": sum(e.get("chars", 0) for e in log),
        "komponenten_gesamt": sum(e.get("komponenten", 0) for e in ok),
        "gruende": [e.get("grund") for e in log if not e.get("ok")],
    }
