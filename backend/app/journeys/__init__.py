"""The advisory journeys sharing one technical core.

Two of them are the product: the model chooses when to show something and
the composers choose what. Two more are the experiment behind
`docs/experiment-generative-ui.md`, where the model writes the A2UI itself.
They are registered here so both appear on the landing page and can be run
side by side.
"""

from __future__ import annotations

from functools import lru_cache

from .base import A2UI_PROVIDER, Journey
from . import energie, generative, mobilitaet

DEFAULT_JOURNEY = "energie"

_BUILDERS = {
    "energie": energie.build,
    "mobilitaet": mobilitaet.build,
    # The experiment. Same figures, same renderer, no composers.
    "energie_frei": lambda: generative.build("energie"),
    "mobilitaet_frei": lambda: generative.build("mobilitaet"),
}

#: The handover summary builder for each journey, used when a session ends.
SUMMARIES = {"energie": energie.summary, "mobilitaet": mobilitaet.summary}


@lru_cache(maxsize=None)
def get_journey(journey_id: str | None = None) -> Journey:
    """Resolves a journey id, falling back to the default.

    Cached because building a Journey constructs an ADK Agent, and every
    WebSocket connection asks for one.
    """
    builder = _BUILDERS.get(journey_id or DEFAULT_JOURNEY, _BUILDERS[DEFAULT_JOURNEY])
    return builder()


def all_journeys() -> list[Journey]:
    return [get_journey(journey_id) for journey_id in _BUILDERS]


__all__ = [
    "A2UI_PROVIDER",
    "DEFAULT_JOURNEY",
    "Journey",
    "SUMMARIES",
    "all_journeys",
    "get_journey",
]
