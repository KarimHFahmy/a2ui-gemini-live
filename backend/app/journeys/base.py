"""Journey definition: prompt, tools and the state a session carries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from ..a2ui.surface import Surface


@dataclass
class ToolResult:
    """What a tool hands back.

    ``surfaces`` are streamed to the renderer; ``result`` goes back to the model
    as the function response so it can talk about what the client now sees
    without re-deriving the numbers.
    """

    surfaces: list[Surface] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)


class JourneyState(Protocol):
    """Per-session state for a journey."""

    def snapshot(self) -> dict[str, Any]:
        """A serialisable view, used for the handover summary."""
        ...


ToolHandler = Callable[[Any, dict[str, Any]], ToolResult]


@dataclass(frozen=True)
class Journey:
    """Everything that makes one advisory journey distinct."""

    id: str
    label: str
    tagline: str
    #: Opening line the agent speaks when the session starts.
    opener: str
    system_instruction: str
    function_declarations: list[dict[str, Any]]
    handlers: dict[str, ToolHandler]
    state_factory: Callable[[], Any]

    def handle(self, state: Any, name: str, args: dict[str, Any]) -> ToolResult:
        handler = self.handlers.get(name)
        if handler is None:
            return ToolResult(result={"fehler": f"Unbekanntes Werkzeug: {name}"})
        return handler(state, args)


# ---------------------------------------------------------------------------
# Prompt fragments shared by both journeys
# ---------------------------------------------------------------------------

GEMEINSAME_HALTUNG = """
## Deine Haltung

Du bist ein persönlicher Berater, kein Chatbot und kein Verkäufer. Du sprichst
Deutsch, natürlich und in ganzen Sätzen, wie ein erfahrener Mensch am Telefon.

- **Zuhören vor Fragen.** Lass die Person erzählen. Stelle immer nur EINE Frage
  auf einmal, und nur wenn die Antwort die Beratung wirklich verändert.
- **Alltagssprache.** Keine Fachbegriffe ohne Erklärung, kein Produktjargon,
  keine Abkürzungen, die man nachschlagen muss.
- **Empathie ohne Druck.** Wenn jemand eine Sorge äußert, nimm sie ernst und
  benenne sie, bevor du sie einordnest. Verkaufe nichts. Dränge zu nichts.
- **Kurz sprechen.** Zwei bis vier Sätze pro Redebeitrag. Die Details stehen
  auf dem Bildschirm, du erklärst sie, du liest sie nicht vor.
- **Ehrlich bleiben.** Wenn etwas nicht passt, sag es. Ein „das lohnt sich für
  Sie so nicht" schafft mehr Vertrauen als eine schöngerechnete Empfehlung.

## Wie du den Bildschirm nutzt

Du baust die Oberfläche über deine Werkzeuge auf, während ihr sprecht. Das ist
kein Nachtrag zum Gespräch, sondern Teil davon.

- Rufe ein Werkzeug auf, sobald du genug verstanden hast — nicht erst am Ende.
- **Nie Zahlen erfinden.** Alle Zahlen kommen aus den Werkzeugen zurück. Sprich
  nur über Werte, die dir ein Werkzeug geliefert hat.
- Nach einem Werkzeugaufruf sagst du in ein bis zwei Sätzen, was jetzt zu sehen
  ist und was es für die Person bedeutet. Zähle nicht alle Zahlen auf.
- Aktualisiere `profil_aktualisieren`, sobald du etwas Neues verstanden hast.
  Die Person soll auf dem Schirm sehen, dass du sie richtig verstanden hast.
- Wenn eine Sorge im Raum steht, beantworte sie mit `bedenken_adressieren`,
  bevor du weiterrechnest.

## Grenzen

- Du gibst eine Orientierung, kein verbindliches Angebot. Sag das, wenn es
  relevant wird — nicht in jedem Satz.
- Alle Werte sind gekennzeichnete Demo-Beispieldaten.
- Frage nicht nach Namen, Adresse, Vertragsnummern oder anderen persönlichen
  Daten. Für die Beratung brauchst du sie nicht.
""".strip()


BEDENKEN_TOOL: dict[str, Any] = {
    "name": "bedenken_adressieren",
    "description": (
        "Beantwortet eine konkrete Sorge oder Rückfrage der Person mit einer "
        "eigenen Ansicht auf dem Bildschirm. Nutze das, sobald jemand eine "
        "Unsicherheit äußert ('ich habe Sorge, dass...', 'lohnt sich das "
        "überhaupt', 'was ist wenn...'). Formuliere die Sorge in der Sprache "
        "der Person, nicht in Fachsprache."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "titel": {
                "type": "STRING",
                "description": (
                    "Die Sorge als Frage, so wie die Person sie stellen würde. "
                    "Beispiel: 'Reicht die Wärmepumpe im Winter wirklich?'"
                ),
            },
            "einordnung": {
                "type": "STRING",
                "description": (
                    "Zwei bis drei Sätze, die die Sorge ernst nehmen und "
                    "einordnen. Keine Floskeln."
                ),
            },
            "punkte": {
                "type": "ARRAY",
                "description": "Zwei bis vier Aspekte, die die Sorge auflösen.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "titel": {"type": "STRING"},
                        "text": {"type": "STRING"},
                        "tone": {
                            "type": "STRING",
                            "enum": ["positive", "neutral", "caution"],
                            "description": (
                                "positive wenn der Punkt entlastet, caution wenn "
                                "er eine echte Einschränkung benennt."
                            ),
                        },
                    },
                    "required": ["titel", "text"],
                },
            },
        },
        "required": ["titel", "einordnung", "punkte"],
    },
}
