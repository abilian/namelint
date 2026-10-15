"""NAM105: a value verb whose body never returns a value.

`total = get_total()` expects a value. A `get_` that only stores into
`self` is a command under a query's name, and the caller holds `None`.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

MODULE = Path("src/app/stats.py")


def codes(source: str) -> list[str]:
    return [finding.code for finding in lint_source(source, MODULE)]


def test_a_get_that_only_stores_is_reported() -> None:
    source = "class S:\n    def get_top_level(self):\n        self.top = compute()\n"

    assert codes(source) == ["NAM105"]


def test_a_bare_return_is_still_no_value() -> None:
    source = "def find_user(uid):\n    if not uid:\n        return\n    log(uid)\n"

    assert codes(source) == ["NAM105"]


def test_a_query_returning_a_value_is_left_alone() -> None:
    source = "def get_total(items):\n    return sum(items)\n"

    assert codes(source) == []


def test_an_explicit_return_none_is_a_value() -> None:
    """importlib's `get_source()` returns None to mean "no source"."""
    source = "def get_source(self, name):\n    return None\n"

    assert codes(source) == []


def test_an_abstract_declaration_is_left_alone() -> None:
    source = (
        "import abc\n\nclass Base(abc.ABC):\n"
        "    @abc.abstractmethod\n    def get_total(self):\n        '''The total.'''\n"
    )

    assert codes(source) == []


def test_a_body_that_ends_by_raising_is_left_alone() -> None:
    source = (
        "def get_total(self):\n    log('unsupported')\n    raise NotImplementedError\n"
    )

    assert codes(source) == []


def test_a_private_query_is_left_alone() -> None:
    source = "def _count_elements(mapping, items):\n    for x in items:\n        mapping[x] += 1\n"

    assert codes(source) == []


def test_a_two_sided_verb_is_left_alone() -> None:
    """`load_config()` filling `self` is a command by convention."""
    source = "class C:\n    def load_config(self):\n        self.config = read()\n"

    assert codes(source) == []
