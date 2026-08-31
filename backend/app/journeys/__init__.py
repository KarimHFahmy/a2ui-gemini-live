"""The advisory journeys sharing one technical core.

Both run in German or in English — the voice, the prompt, the composed
surfaces and the frontend chrome. A journey is built per locale, so `get_journey`
is keyed on both.
"""

from __future__ import annotations

from functools import lru_cache

from ..texts import DEFAULT_LOCALE, LOCALES, Locale
from .base import A2UI_PROVIDER, Journey
from . import energie, mobilitaet

DEFAULT_JOURNEY = "energie"

_BUILDERS = {
    "energie": energie.build,
    "mobilitaet": mobilitaet.build,
}

#: The handover summary builder for each journey, used when a session ends.
SUMMARIES = {"energie": energie.summary, "mobilitaet": mobilitaet.summary}


@lru_cache(maxsize=None)
def get_journey(
    journey_id: str | None = None, locale: Locale = DEFAULT_LOCALE
) -> Journey:
    """Resolves a journey id and a locale, falling back to the defaults.

    Cached because building a Journey constructs an ADK Agent, and every
    WebSocket connection asks for one. The locale is part of the key: the agent
    carries the instruction, and that is written in one language.
    """
    builder = _BUILDERS.get(journey_id or DEFAULT_JOURNEY, _BUILDERS[DEFAULT_JOURNEY])
    return builder(locale if locale in LOCALES else DEFAULT_LOCALE)


def all_journeys(locale: Locale = DEFAULT_LOCALE) -> list[Journey]:
    return [get_journey(journey_id, locale) for journey_id in _BUILDERS]


__all__ = [
    "A2UI_PROVIDER",
    "DEFAULT_JOURNEY",
    "DEFAULT_LOCALE",
    "LOCALES",
    "Journey",
    "Locale",
    "SUMMARIES",
    "all_journeys",
    "get_journey",
]
