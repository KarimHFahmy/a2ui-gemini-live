"""The two advisory journeys sharing one technical core."""

from __future__ import annotations

from .base import Journey, ToolResult
from .energie import JOURNEY as ENERGIE
from .mobilitaet import JOURNEY as MOBILITAET

JOURNEYS: dict[str, Journey] = {ENERGIE.id: ENERGIE, MOBILITAET.id: MOBILITAET}

DEFAULT_JOURNEY = ENERGIE.id


def get_journey(journey_id: str | None) -> Journey:
    """Resolves a journey id, falling back to the default."""
    return JOURNEYS.get(journey_id or DEFAULT_JOURNEY, JOURNEYS[DEFAULT_JOURNEY])


__all__ = ["Journey", "ToolResult", "JOURNEYS", "DEFAULT_JOURNEY", "get_journey"]
