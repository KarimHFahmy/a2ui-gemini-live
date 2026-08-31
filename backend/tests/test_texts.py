"""The two catalogs have to stay the same shape.

A missing key does not raise on the path that matters. It raises in whichever
code path nobody demoed, mid-conversation, in front of a client — and the
alternative, a silent fallback to the other language, is worse: a German
sentence rendered into an English session with nothing to notice it.

So the shape is asserted here rather than trusted: same keys, same types, same
placeholders. That last one is the subtle failure — a translator who drops
`{betrag}` from a sentence turns a figure into a crash the first time a client
reaches that surface.
"""

from __future__ import annotations

import string

import pytest

from app.texts import CATALOGS, LOCALES, Texts

#: The reference language: the copy was written in German and translated.
SOURCE = "de"
OTHERS = [locale for locale in LOCALES if locale != SOURCE]


def holes(value: str) -> set[str]:
    """The `{named}` placeholders in a catalog entry."""
    return {name for _, name, _, _ in string.Formatter().parse(value) if name}


def prose(value: str) -> str:
    """The literal text of an entry, with the placeholders removed."""
    return "".join(literal for literal, _, _, _ in string.Formatter().parse(value))


class TestTheCatalogsMatch:
    @pytest.mark.parametrize("locale", OTHERS)
    def test_no_key_is_missing_or_extra(self, locale):
        source, other = set(CATALOGS[SOURCE]), set(CATALOGS[locale])

        assert not source - other, f"{locale} is missing: {sorted(source - other)}"
        assert not other - source, f"{locale} has extra: {sorted(other - source)}"

    @pytest.mark.parametrize("locale", OTHERS)
    def test_a_list_stays_a_list_and_a_string_a_string(self, locale):
        for key, value in CATALOGS[SOURCE].items():
            assert type(CATALOGS[locale][key]) is type(value), key

    @pytest.mark.parametrize("locale", OTHERS)
    def test_a_list_keeps_its_length(self, locale):
        # Steps, assumption lines and weekday labels are read positionally or
        # zipped into fields; a translation one item short silently drops one.
        for key, value in CATALOGS[SOURCE].items():
            if isinstance(value, list):
                assert len(CATALOGS[locale][key]) == len(value), key

    @pytest.mark.parametrize("locale", OTHERS)
    def test_every_placeholder_survives_translation(self, locale):
        for key, value in CATALOGS[SOURCE].items():
            entries = value if isinstance(value, list) else [value]
            translated = CATALOGS[locale][key]
            translated = translated if isinstance(translated, list) else [translated]

            expected = set().union(*(holes(item) for item in entries))
            actual = set().union(*(holes(item) for item in translated))

            assert expected == actual, (
                f"{key}: {locale} has {sorted(actual)}, {SOURCE} has {sorted(expected)}"
            )


class TestNothingWasLeftUntranslated:
    def test_no_entry_is_identical_across_the_two(self):
        """Copy-paste is how half a catalog stays in the source language.

        Some entries legitimately match: a dash, a unit, `{fahrzeug}, {batterie}
        kWh` — which is placeholders and a unit and nothing to translate. So the
        measure is the *prose* in an entry, the literal text with the
        placeholders taken out, and anything with a sentence's worth of it has
        to differ.
        """
        untranslated = []
        for locale in OTHERS:
            for key, value in CATALOGS[SOURCE].items():
                other = CATALOGS[locale][key]
                if isinstance(value, str) and value == other and len(prose(value)) > 20:
                    untranslated.append(f"{locale}:{key}")

        assert not untranslated, f"still in {SOURCE}: {untranslated}"

    @pytest.mark.parametrize("locale", OTHERS)
    def test_the_translation_carries_no_german_umlauts(self, locale):
        """A crude but effective test for a half-finished entry.

        It only holds because English is the only other language here; a third
        one would need its own rule. Proper nouns that keep an umlaut would
        need an exemption, and there are none.
        """
        leaked = []
        for key, value in CATALOGS[locale].items():
            entries = value if isinstance(value, list) else [value]
            if any(set("äöüßÄÖÜ") & set(item) for item in entries):
                leaked.append(key)

        assert not leaked, f"{locale} still reads German in: {leaked}"


class TestTheAccessor:
    def test_a_missing_key_raises_rather_than_falling_back(self):
        """A fallback would ship the wrong language quietly."""
        with pytest.raises(KeyError):
            Texts("en")("no.such.key")

    def test_asking_for_a_list_as_a_string_is_an_error(self):
        with pytest.raises(TypeError):
            Texts("de")("energie.monate")

    def test_an_unknown_locale_falls_back_to_the_default(self):
        assert Texts("fr").locale == SOURCE

    @pytest.mark.parametrize(
        ("locale", "value", "expected"),
        [("de", 18200.5, "18.200,5"), ("en", 18200.5, "18,200.5")],
    )
    def test_numbers_follow_the_locale(self, locale, value, expected):
        assert Texts(locale).num(value, decimals=1) == expected

    @pytest.mark.parametrize(
        ("locale", "expected"), [("de", "1.234 €"), ("en", "€1,234")]
    )
    def test_the_euro_sign_goes_where_the_language_puts_it(self, locale, expected):
        assert Texts(locale).euro(1234) == expected
