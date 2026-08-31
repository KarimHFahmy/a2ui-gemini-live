"""Numbers, in the reader's convention.

German and English swap the two separators — `18.200,5` against `18,200.5` —
so every composed figure has to know which locale it is being read in. This is
the one place that knows.

Only the separators change. The currency stays the euro and the units stay
metric: the product advises on the German market whichever language it is
speaking, and converting a Wärmebedarf into therms would be a different demo.

Figures that recompute in the browser go through the renderer's own
`formatNumber`, which is handed the same locale; see
`frontend/src/a2ui/catalog.ts`.
"""

from __future__ import annotations

from typing import Literal

Locale = Literal["de", "en"]

#: The default everywhere a locale has not been chosen yet.
DEFAULT_LOCALE: Locale = "de"

LOCALES: tuple[Locale, ...] = ("de", "en")

#: (thousands, decimal) for each locale.
_SEPARATORS: dict[str, tuple[str, str]] = {"de": (".", ","), "en": (",", ".")}


def num(
    value: float,
    locale: Locale = DEFAULT_LOCALE,
    *,
    decimals: int = 0,
    unit: str | None = None,
) -> str:
    """A number written the way `locale` writes it, optionally with a unit."""
    thousands, decimal = _SEPARATORS.get(locale, _SEPARATORS["de"])
    body = f"{value:,.{decimals}f}"
    body = body.replace(",", "\x00").replace(".", decimal).replace("\x00", thousands)
    return f"{body} {unit}" if unit else body


def euro(value: float, locale: Locale = DEFAULT_LOCALE, *, decimals: int = 0) -> str:
    """An amount in euros, with the sign where that language puts it.

    German writes `18.200 €`, English `€18,200`. The euro is the currency in
    both — this product advises on the German market either way.
    """
    body = num(value, locale, decimals=decimals)
    return f"€{body}" if locale == "en" else f"{body} €"


def pct(fraction: float, locale: Locale = DEFAULT_LOCALE, *, decimals: int = 0) -> str:
    """A share written as a percentage, with the locale's decimal separator.

    Python's `:.1%` always writes a point, which is how `4.5%` got into German
    copy that had every other figure right. The space before the sign is
    German typographic convention; English closes it up.
    """
    body = num(fraction * 100, locale, decimals=decimals)
    return f"{body}%" if locale == "en" else f"{body} %"
