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

from ..a2ui import readback
from ..a2ui.surface import Surface
from ..texts import DEFAULT_LOCALE, Locale, Texts

#: Marks widgets this application knows how to render.
A2UI_PROVIDER = "a2ui"

#: Session-state keys. Prefixed so they never collide with agent-authored keys.
_SURFACES_KEY = "_a2ui_live_surfaces"
_PROFILE_KEY = "_advisory_profile"
#: Set once when the session starts; every tool reads it to answer in the
#: client's language.
LOCALE_KEY = "_advisory_locale"


def texts_for(tool_context: ToolContext) -> Texts:
    """The locale this conversation is being held in.

    Read from session state rather than closed over, because the advisory tools
    are module-level functions shared by every session of that journey — and a
    tool that captured a locale at import time would answer the second client
    in the first one's language.
    """
    return Texts(tool_context.state.get(LOCALE_KEY, DEFAULT_LOCALE))

T = TypeVar("T")


def push(tool_context: ToolContext, surface: Surface) -> str:
    """Streams a surface to the browser and answers with what is now on it.

    The first push of a surface creates it; later pushes replace its contents
    in place, so a refined answer updates the card the client is already
    reading instead of stacking a near-duplicate below it.

    The return value is the surface read back in words (see
    :mod:`app.a2ui.readback`). It exists because the agent chooses *when* to
    show something and the composer chooses *what*, which left the agent
    talking about a picture it had never seen: it knew the break-even year
    because the tool returned it, but not that the chart draws four lines or
    where they cross. Deriving the description from the composed tree rather
    than writing it by hand is the point — two descriptions of one picture
    drift, and the day they disagree the agent is confidently wrong about
    something the client is looking at.
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

    return readback.describe(surface, texts_for(tool_context))


def shown(tool_context: ToolContext, *surfaces: Surface, **fields: Any) -> dict[str, Any]:
    """Pushes surfaces and builds the tool's answer around what they show.

    Every advisory tool ends this way, so the screen description cannot be
    forgotten on a tool someone adds later — which is exactly what would
    happen if it were one more key each of them had to remember.

    Several surfaces because a tool can revise more than one: correcting a
    price assumption redraws the what-if panel *and* the comparison built on
    it, and the client can see both.
    """
    described = [push(tool_context, surface) for surface in surfaces]
    return {**fields, "auf_dem_schirm": "\n\n".join(described)}


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

def opening_line(t: Texts, topics: list[str], frage_nach: str) -> str:
    """The nudge that starts the conversation.

    Composed from the journey's own topics rather than written separately, so
    what the agent says out loud and what the empty screen lists can never drift
    apart. Naming the three things first is the whole point: a warm greeting and
    an open question leave a first-time client with nothing to grab onto, and
    the most common failure of a voice product is a person who does not know
    what they are allowed to say.
    """
    return t("prompt.opening", themen=join_list(t, topics), frage=frage_nach)


def join_list(t: Texts, items: list[str]) -> str:
    """`a, b und c` / `a, b and c` — a spoken list, not a bulleted one."""
    if len(items) < 2:
        return "".join(items)
    return t("prompt.join", vorher=", ".join(items[:-1]), letzter=items[-1])


class Journey:
    """One advisory journey: its identity, its agent, its opening line."""

    def __init__(
        self,
        *,
        journey_id: str,
        locale: Locale,
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
        #: Which language this whole journey speaks — prompt, surfaces and voice.
        self.locale = locale
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
