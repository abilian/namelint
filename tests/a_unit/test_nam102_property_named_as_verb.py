"""NAM102: a property whose name opens with a verb.

`obj.get_child` reads as an attribute at the call site, and as a bound
method to anyone who knows Python. Whether a word is a verb comes from
the treebank table, and only words that are almost always verbs count,
so `name`, `drive` and `handle` stay quiet.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import check_source

MODULE = Path("src/app/tree.py")


def codes(source: str) -> list[str]:
    return [finding.code for finding in check_source(source, MODULE)]


def prop(name: str, decorator: str = "property") -> str:
    return f"class Node:\n    @{decorator}\n    def {name}(self):\n        return self._x\n"


def test_a_property_opening_with_get_is_reported() -> None:
    assert codes(prop("get_child")) == ["NAM102"]


def test_a_cached_property_counts_as_a_property() -> None:
    assert codes(prop("raise_error", "functools.cached_property")) == ["NAM102"]


def test_a_noun_property_is_left_alone() -> None:
    assert codes(prop("name")) == []


def test_a_word_that_is_as_often_a_noun_is_left_alone() -> None:
    """`handle` is a verb in the treebank 84% of the time, below the bar."""
    assert codes(prop("handle")) == []


def test_a_method_opening_with_a_verb_is_left_alone() -> None:
    source = "class Node:\n    def get_child(self):\n        return self._x\n"

    assert codes(source) == []


def test_a_private_property_is_left_alone() -> None:
    assert codes(prop("_get_child")) == []


def test_a_word_the_table_does_not_know_is_silence() -> None:
    """`frobnicate` is in no treebank, and unknown is never a finding."""
    assert codes(prop("frobnicate_all")) == []
