"""Every word a client reads or hears, in both languages.

The whole experience runs in German or in English — the voice, the prompts,
the composed surfaces, the frontend chrome. This package holds the server half
of that: two flat dictionaries with identical key sets, one per language.

Two dictionaries rather than a gettext catalog because there is no translator
workflow here and no build step worth adding; two Python files sit side by side
in a diff and a test can compare their keys. That test matters more than it
sounds: a key present in `de` and missing in `en` does not raise, it renders a
German sentence into an English conversation, and nothing else would notice.

Keys are grouped by the surface they appear on (`eignung.title`), so a
composer's imports read as a table of contents for what it says.

    t = Texts("en")
    t("eignung.title")
    t("eignung.lead", urteil=t("eignung.verdict.good"))
    t.list("handover.assumptions")
"""

from __future__ import annotations

from typing import Any

from ..format_num import DEFAULT_LOCALE, LOCALES, Locale
from . import de as _de
from . import en as _en

CATALOGS: dict[str, dict[str, Any]] = {"de": _de.TEXTS, "en": _en.TEXTS}


class Texts:
    """One locale's words, callable.

    A missing key raises rather than falling back to the other language. A
    fallback is worse than a crash here: it ships a German sentence to an
    English client, quietly, and only in the code path nobody demoed.
    """

    __slots__ = ("locale", "_catalog")

    def __init__(self, locale: Locale = DEFAULT_LOCALE) -> None:
        self.locale: Locale = locale if locale in LOCALES else DEFAULT_LOCALE
        self._catalog = CATALOGS[self.locale]

    def __call__(self, key: str, **fields: Any) -> str:
        value = self._catalog.get(key)
        if value is None:
            raise KeyError(f"no text for {key!r} in {self.locale!r}")
        if not isinstance(value, str):
            raise TypeError(f"{key!r} is a list; use .list()")
        return value.format(**fields) if fields else value

    def list(self, key: str, **fields: Any) -> list[str]:
        """A list of strings — assumption lines, bullet points, options."""
        value = self._catalog.get(key)
        if value is None:
            raise KeyError(f"no text for {key!r} in {self.locale!r}")
        if not isinstance(value, list):
            raise TypeError(f"{key!r} is a single string; call it instead")
        return [item.format(**fields) if fields else item for item in value]

    def get(self, key: str, default: str = "", **fields: Any) -> str:
        """For keys built at runtime from data — a scenario id, a tone name.

        Those come from the domain rather than from a composer, so a value the
        catalog has never seen is a possibility rather than a bug, and an empty
        string is better than taking the conversation down.
        """
        value = self._catalog.get(key)
        if not isinstance(value, str):
            return default
        return value.format(**fields) if fields else value

    # Formatting belongs to the locale too, so a composer that has `t` never
    # has to also carry a locale around to write a number.

    def num(self, value: float, *, decimals: int = 0, unit: str | None = None) -> str:
        from ..format_num import num

        return num(value, self.locale, decimals=decimals, unit=unit)

    def euro(self, value: float, *, decimals: int = 0) -> str:
        from ..format_num import euro

        return euro(value, self.locale, decimals=decimals)

    @staticmethod
    def upper_first(text: str) -> str:
        """Capitalises a data-derived word that happens to start a label.

        German compounds the carrier into one word (`Erdgaspreis`) so it is
        already capitalised; English puts it in front as its own word, and
        `natural gas price in cents per kWh` starts a label in lower case.
        `.capitalize()` would flatten the rest, so only the first character
        moves.
        """
        return text[:1].upper() + text[1:] if text else text

    def pct(self, fraction: float, *, decimals: int = 0) -> str:
        from ..format_num import pct

        return pct(fraction, self.locale, decimals=decimals)


def texts(locale: Locale = DEFAULT_LOCALE) -> Texts:
    return Texts(locale)


__all__ = ["CATALOGS", "DEFAULT_LOCALE", "LOCALES", "Locale", "Texts", "texts"]
