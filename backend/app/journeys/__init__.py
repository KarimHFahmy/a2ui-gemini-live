"""The two advisory journeys sharing one technical core."""

from __future__ import annotations

from functools import lru_cache

from .base import A2UI_PROVIDER, Journey
from . import energie, mobilitaet

DEFAULT_JOURNEY = "energie"

_BUILDERS = {"energie": energie.build, "mobilitaet": mobilitaet.build}

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
