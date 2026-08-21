"""A surface: one coherent piece of advice, ready to stream to the renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import protocol
from .protocol import A2uiMessage


@dataclass
class Surface:
    """A composed A2UI surface.

    ``components`` is the layout (sent once) and ``data`` is the content
    (patched on every refinement). Splitting them is what makes a live
    conversation feel responsive: a follow-up question usually only changes
    the data.
    """

    surface_id: str
    title: str
    components: list[dict[str, Any]]
    data: dict[str, Any] = field(default_factory=dict)
    catalog_id: str = protocol.ADVISORY_CATALOG_ID

    def messages(self, *, exists: bool = False) -> list[A2uiMessage]:
        """Serialises the surface into the message stream.

        When the surface is already on screen we skip ``createSurface`` and
        replace its contents in place, so a refined answer updates the card the
        client is already looking at instead of stacking a new one below it.
        """
        protocol.validate_tree(self.components)

        out: list[A2uiMessage] = []
        if not exists:
            out.append(
                protocol.create_surface(self.surface_id, catalog_id=self.catalog_id)
            )
        out.append(protocol.update_data_model(self.surface_id, self.data))
        out.append(protocol.update_components(self.surface_id, self.components))
        return out
