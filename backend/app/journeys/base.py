"""Shared machinery for both advisory journeys.

A journey is an ADK :class:`~google.adk.agents.Agent` — a system instruction
plus a set of `FunctionTool`s. ADK derives each tool's schema from its type
hints and docstring, so the declaration the model sees and the function that
runs can never drift apart.

Tools reach the browser through ADK's UI-widget channel: `render_ui_widget`
attaches a payload to the event the tool produces, and the WebSocket layer
forwards widgets whose provider is ``a2ui``. The provider field exists for
exactly this — pluggable rendering strategies — so no side channel is needed.
"""

from __future__ import annotations

from dataclasses import asdict, fields
from typing import Any, TypeVar

from google.adk.agents import Agent
from google.adk.events.ui_widget import UiWidget
from google.adk.tools import ToolContext

from ..a2ui.surface import Surface

#: Marks widgets this application knows how to render.
A2UI_PROVIDER = "a2ui"

#: Session-state keys. Prefixed so they never collide with agent-authored keys.
_SURFACES_KEY = "_a2ui_live_surfaces"
_PROFILE_KEY = "_advisory_profile"

T = TypeVar("T")


def push(tool_context: ToolContext, surface: Surface) -> None:
    """Streams a surface to the browser.

    The first push of a surface creates it; later pushes replace its contents
    in place, so a refined answer updates the card the client is already
    reading instead of stacking a near-duplicate below it.
    """
    live: list[str] = list(tool_context.state.get(_SURFACES_KEY, []))
    exists = surface.surface_id in live

    tool_context.render_ui_widget(
        UiWidget(
            id=surface.surface_id,
            provider=A2UI_PROVIDER,
            payload={
                "surfaceId": surface.surface_id,
                "title": surface.title,
                "isNew": not exists,
                # A2UI envelopes, already validated by Surface.messages().
                "messages": surface.messages(exists=exists),
            },
        )
    )

    if not exists:
        tool_context.state[_SURFACES_KEY] = [*live, surface.surface_id]


def load_profile(tool_context: ToolContext, factory: type[T]) -> T:
    """Rehydrates the journey's profile dataclass from session state."""
    stored = tool_context.state.get(_PROFILE_KEY) or {}
    known = {f.name for f in fields(factory)}  # type: ignore[arg-type]
    return factory(**{k: v for k, v in stored.items() if k in known})  # type: ignore[call-arg]


def save_profile(tool_context: ToolContext, profile: Any) -> None:
    """Persists the profile so the next tool call sees the same picture."""
    tool_context.state[_PROFILE_KEY] = asdict(profile)


def apply(profile: Any, **updates: Any) -> Any:
    """Applies the arguments the model actually supplied.

    ADK passes unset optional parameters as ``None``; writing those through
    would erase what an earlier turn established.
    """
    for key, value in updates.items():
        if value is not None:
            setattr(profile, key, value)
    return profile


def open_points(tool_context: ToolContext, supplied: list[str] | None) -> list[str]:
    """Keeps the open-points list sticky across turns."""
    if supplied:
        tool_context.state["_advisory_open_points"] = supplied
        return supplied
    return list(tool_context.state.get("_advisory_open_points", []))


# ---------------------------------------------------------------------------
# Prompt fragments shared by both journeys
# ---------------------------------------------------------------------------

HALTUNG = """
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


def opening_line(topics: list[str], frage_nach: str) -> str:
    """The nudge that starts the conversation.

    Composed from the journey's own topics rather than written separately, so
    what the agent says out loud and what the empty screen lists can never drift
    apart. Naming the three things first is the whole point: a warm greeting and
    an open question leave a first-time client with nothing to grab onto, and
    the most common failure of a voice product is a person who does not know
    what they are allowed to say.
    """
    return (
        "Begrüße die Person kurz und warm auf Deutsch. Sag ihr dann in einem "
        "Satz, wobei du helfen kannst: " + join_de(topics) + ". Stelle danach "
        f"genau eine offene Frage {frage_nach}. Insgesamt höchstens drei Sätze."
    )


def join_de(items: list[str]) -> str:
    """`a, b und c` — a spoken list, not a bulleted one."""
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " und " + items[-1]


class Journey:
    """One advisory journey: its identity, its agent, its opening line."""

    def __init__(
        self,
        *,
        journey_id: str,
        label: str,
        tagline: str,
        opener: str,
        instruction: str,
        tools: list[Any],
        model: str,
        steps: list[tuple[str, str]],
        topics: list[str],
    ) -> None:
        self.id = journey_id
        self.label = label
        self.tagline = tagline
        self.opener = opener
        #: What this journey can actually help with, in the client's words.
        #: Spoken in the greeting and listed on the empty screen — one source,
        #: so someone who missed the audio can read the same three things.
        self.topics = topics
        #: The advisory arc as (surface id, label) pairs, in order. The client
        #: marks a step done when its surface has arrived, which is why these
        #: are surface ids and not tool names: a step counts once the person
        #: can actually see it. Surfaces that answer a question rather than
        #: advance the conversation — a concern, the what-if view — are
        #: deliberately not steps.
        self.steps = steps
        self.agent = Agent(
            name=f"berater_{journey_id}",
            description=tagline,
            model=model,
            instruction=instruction,
            tools=tools,
        )
