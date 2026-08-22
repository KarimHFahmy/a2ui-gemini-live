"""Shared fixtures.

Tools reach the browser through ADK's UI-widget channel and read/write session
state. Both are small enough to stand in for, so the whole tool surface is
testable without a runner, a model or a network connection.
"""

from __future__ import annotations

from typing import Any

import pytest
from google.adk.events import EventActions
from google.adk.tools import ToolContext


class FakeToolContext:
    """A stand-in for ADK's ToolContext.

    Borrows the real `render_ui_widget` so widget construction, id-collision
    rules and payload shape are exercised for real rather than mocked away.
    """

    def __init__(self) -> None:
        self.state: dict[str, Any] = {}
        self._event_actions = EventActions()

    render_ui_widget = ToolContext.render_ui_widget

    @property
    def widgets(self) -> list[Any]:
        return list(self._event_actions.render_ui_widgets or [])

    def messages(self) -> list[dict[str, Any]]:
        """Every A2UI envelope pushed since the last reset."""
        return [m for w in self.widgets for m in w.payload["messages"]]

    def reset_event(self) -> None:
        """Starts a new event, as ADK does between tool calls."""
        self._event_actions = EventActions()


@pytest.fixture
def ctx() -> FakeToolContext:
    return FakeToolContext()
