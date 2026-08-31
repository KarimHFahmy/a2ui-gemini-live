"""German number formatting, in one place.

Lives at the app root rather than in `a2ui` or `domain` because both compose
strings a client reads: the composers build the cards, and `domain` builds the
assumption lines that go inside them. Neither layer should import the other.
"""

from __future__ import annotations


def de(value: float, *, decimals: int = 0, unit: str | None = None) -> str:
    """A number the way German writes it: comma for decimals, point for thousands.

    Surfaces were formatting with Python's defaults, so a seasonal performance
    factor rendered as `3.2` and a heat load as `12.4 kW` on a page that is
    otherwise entirely German. It surfaced when the agent started reading the
    screen back (`a2ui.readback`) and would have said those out loud.

    Figures that recompute in the browser go through the renderer's own
    `formatNumber`, already pinned to de-DE; this is for the ones composed here.
    """
    body = f"{value:,.{decimals}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return f"{body} {unit}" if unit else body
