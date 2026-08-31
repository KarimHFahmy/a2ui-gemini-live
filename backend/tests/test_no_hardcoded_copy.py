"""No client-facing sentence may live in the code any more.

The browser check catches German that reaches an English screen, but only when
it looks German — an umlaut, a function word. "Vor-Ort-Check anfragen" has
neither, and it shipped into the English handover surface with every other
guard passing. It was found by looking at a screenshot, which is not a method.

This is the structural version: the composers and the journeys may no longer
contain a German string literal at all. Every word a client reads goes through
`app.texts`, so a literal here is either a leak or a thing that should have
been a key. Docstrings and comments are exempt — the code is documented in
English and explained in German where the domain is German.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"

#: Where client-facing copy could plausibly hide. `texts/` is the catalog
#: itself and `domain/demo_data.py` holds figures, not sentences.
SOURCES = sorted(
    [*APP.glob("a2ui/composer_*.py"), *APP.glob("journeys/*.py"), *APP.glob("domain/*.py")]
)

#: Characters German has and English does not, plus function words that cannot
#: appear in an English sentence. Deliberately loose: a false positive here is
#: a string that should have been a catalog key anyway.
GERMAN = re.compile(
    r"[äöüßÄÖÜ]"
    r"|\b(der|die|das|und|von|mit|für|ist|sind|dem|den|eine|einen|nicht|auf"
    r"|sich|Ihre|Ihr|Sie|anfragen|anfordern|vereinbaren|prüfen|zeigen)\b"
)

#: Identifiers, not copy: catalog keys, state keys, scenario and tool ids.
#: A key is exempt because it is never rendered — it is looked up.
KEY = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_.]*)+$")


def literals(path: Path) -> list[tuple[int, str]]:
    """Every string literal in the module that is not a docstring."""
    tree = ast.parse(path.read_text())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))

    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(APP)))
def test_no_german_sentence_is_hard_coded(path: Path) -> None:
    offenders = [
        f"{path.name}:{line} {value!r}"
        for line, value in literals(path)
        if not KEY.match(value) and GERMAN.search(value)
    ]

    assert not offenders, (
        "client-facing copy belongs in app/texts, not in the code:\n  "
        + "\n  ".join(offenders)
    )
