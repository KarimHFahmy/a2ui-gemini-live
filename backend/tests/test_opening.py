"""What the agent says first.

A voice product's most common failure is not a wrong answer, it is a person who
does not know what they are allowed to say. The opener used to be "greet warmly
and ask one open question", which leaves a first-time client staring at a
microphone with no idea of the scope.

The topics are now a property of the journey, the greeting is composed from
them, and the client lists the same three on the empty screen. These pin that
chain together — it is only worth anything if all three stay in step.
"""

from __future__ import annotations

import pytest

from app.journeys import all_journeys
from app.journeys.base import join_de, opening_line


class TestJoinDe:
    def test_three_items_read_as_a_spoken_list(self):
        assert join_de(["a", "b", "c"]) == "a, b und c"

    def test_two_items_need_no_comma(self):
        assert join_de(["a", "b"]) == "a und b"

    def test_one_item_stands_alone(self):
        assert join_de(["a"]) == "a"

    def test_none_is_empty(self):
        assert join_de([]) == ""


class TestOpeningLine:
    def test_it_names_every_topic(self):
        line = opening_line(["ob X passt", "was Y kostet"], "zum Haus")
        assert "ob X passt" in line
        assert "was Y kostet" in line

    def test_it_still_asks_one_open_question(self):
        line = opening_line(["ob X passt"], "zum Haus")
        assert "zum Haus" in line
        assert "eine offene Frage" in line

    def test_it_keeps_the_greeting_short(self):
        """A spoken greeting that runs long is worse than one that says nothing."""
        line = opening_line(["a", "b", "c"], "zum Haus")
        assert "höchstens drei Sätze" in line


@pytest.mark.parametrize("journey", all_journeys(), ids=lambda j: j.id)
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
