"""What the agent says first, in whichever language it is speaking.

A voice product's most common failure is not a wrong answer, it is a person who
does not know what they are allowed to say. The opener used to be "greet warmly
and ask one open question", which leaves a first-time client staring at a
microphone with no idea of the scope.

The topics are a property of the journey, the greeting is composed from them,
and the client lists the same three on the empty screen. These pin that chain
together — it is only worth anything if all three stay in step, and now they
have to stay in step twice.
"""

from __future__ import annotations

import pytest

from app.journeys import LOCALES, all_journeys
from app.journeys.base import join_list, opening_line
from app.texts import Texts

#: Every journey in every language, which is the whole matrix a client can
#: land in.
JOURNEYS = [journey for locale in LOCALES for journey in all_journeys(locale)]


class TestJoinList:
    @pytest.mark.parametrize(
        ("locale", "expected"), [("de", "a, b und c"), ("en", "a, b and c")]
    )
    def test_three_items_read_as_a_spoken_list(self, locale, expected):
        assert join_list(Texts(locale), ["a", "b", "c"]) == expected

    @pytest.mark.parametrize(
        ("locale", "expected"), [("de", "a und b"), ("en", "a and b")]
    )
    def test_two_items_need_no_comma(self, locale, expected):
        assert join_list(Texts(locale), ["a", "b"]) == expected

    @pytest.mark.parametrize("locale", LOCALES)
    def test_one_item_stands_alone(self, locale):
        assert join_list(Texts(locale), ["a"]) == "a"

    @pytest.mark.parametrize("locale", LOCALES)
    def test_none_is_empty(self, locale):
        assert join_list(Texts(locale), []) == ""


class TestOpeningLine:
    @pytest.mark.parametrize("locale", LOCALES)
    def test_it_names_every_topic(self, locale):
        line = opening_line(Texts(locale), ["ob X passt", "was Y kostet"], "zum Haus")

        assert "ob X passt" in line
        assert "was Y kostet" in line

    @pytest.mark.parametrize("locale", LOCALES)
    def test_it_still_asks_one_open_question(self, locale):
        line = opening_line(Texts(locale), ["ob X passt"], "zum Haus")

        assert "zum Haus" in line
        assert ("eine offene Frage" if locale == "de" else "one open question") in line

    @pytest.mark.parametrize("locale", LOCALES)
    def test_it_keeps_the_greeting_short(self, locale):
        """A spoken greeting that runs long is worse than one that says nothing."""
        line = opening_line(Texts(locale), ["a", "b", "c"], "zum Haus")

        assert ("drei Sätze" if locale == "de" else "Three sentences") in line


@pytest.mark.parametrize("journey", JOURNEYS, ids=lambda j: f"{j.id}-{j.locale}")
class TestEveryJourneyOpensWithItsScope:
    def test_it_has_topics(self, journey):
        assert 2 <= len(journey.topics) <= 4, "one topic is not a scope; five is a menu"

    def test_the_topics_are_clauses_that_splice_into_a_sentence(self, journey):
        """They are spoken after a colon and printed as list items."""
        for topic in journey.topics:
            assert topic[0].islower(), f"starts mid-sentence, so lowercase: {topic!r}"
            assert len(topic) <= 60, f"too long to say in one breath: {topic!r}"
            assert not topic.endswith("."), "topics are joined into one sentence"

    def test_the_opener_names_all_of_them(self, journey):
        for topic in journey.topics:
            assert topic in journey.opener, f"{journey.id} never says {topic!r}"

    def test_the_standing_instruction_names_them_too(self, journey):
        """The opener fires once. A resumed session leans on the instruction."""
        for topic in journey.topics:
            assert topic in journey.agent.instruction, (
                f"{journey.id}'s instruction does not mention {topic!r}, so a "
                "re-greeting would drop the scope"
            )

    def test_the_agent_is_told_which_language_to_speak(self, journey):
        """Otherwise it answers in whatever language the client happens to use.

        The client picked a language on the landing page and the whole screen
        is in it; an agent that follows the caller's accent instead would put
        spoken English next to German cards.
        """
        expected = "Deutsch" if journey.locale == "de" else "English"

        assert expected in journey.agent.instruction
        assert expected in journey.opener
