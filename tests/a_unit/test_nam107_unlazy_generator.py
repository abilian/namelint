"""NAM107: a generator whose name reads as if it returned a container.

A caller who believes they hold a list and actually hold a one-shot
iterator writes a bug that surfaces two loops later.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

MODULE = Path("src/app/users.py")


def codes(source: str) -> list[str]:
    return [found.code for found in lint_source(source, MODULE)]


def test_a_singular_generator_is_reported() -> None:
    source = "def active_user(rows):\n    yield rows[0]\n"

    assert codes(source) == ["NAM107"]


def test_yield_from_counts() -> None:
    source = "def active_user(rows):\n    yield from rows\n"

    assert codes(source) == ["NAM107"]


def test_an_async_generator_is_reported() -> None:
    source = "async def active_user(rows):\n    yield rows[0]\n"

    assert codes(source) == ["NAM107"]


def test_a_lazy_prefix_stays_silent() -> None:
    source = "def iter_users(rows):\n    yield from rows\n"

    assert codes(source) == []


def test_a_plural_stays_silent() -> None:
    source = "def users(rows):\n    yield from rows\n"

    assert codes(source) == []


def test_a_double_s_ending_is_not_a_plural() -> None:
    """`address` ends in `s` and is singular."""
    source = "def address(rows):\n    yield from rows\n"

    assert codes(source) == ["NAM107"]


def test_a_function_returning_a_list_is_not_a_generator() -> None:
    source = "def active_user(rows):\n    return [rows[0]]\n"

    assert codes(source) == []


def test_a_dunder_is_left_alone() -> None:
    source = "class Bag:\n    def __iter__(self):\n        yield 1\n"

    assert codes(source) == []


def test_a_nested_generator_does_not_promote_its_parent() -> None:
    source = "def build(rows):\n    def inner():\n        yield 1\n    return inner\n"

    assert codes(source) == []


def test_a_pytest_fixture_is_left_alone() -> None:
    """In a fixture `yield` is setup/teardown, and the noun is deliberate."""
    source = "import pytest\n\n@pytest.fixture\ndef db_session():\n    yield 1\n"

    assert codes(source) == []


def test_a_context_manager_is_left_alone() -> None:
    source = (
        "from contextlib import contextmanager\n\n"
        "@contextmanager\ndef temp_config():\n    yield 1\n"
    )

    assert codes(source) == []


def test_a_parametrised_fixture_is_left_alone() -> None:
    source = (
        "import pytest\n\n@pytest.fixture(scope='session')\n"
        "def container():\n    yield 1\n"
    )

    assert codes(source) == []


def test_a_lazy_prefix_survives_a_leading_underscore() -> None:
    """`_walk` and `_stream_into_x` were both reported until the
    underscore was stripped before the prefix test."""
    for name in ("_walk", "_stream_into_assistant", "_iter_rows"):
        source = f"def {name}(rows):\n    yield from rows\n"

        assert codes(source) == [], name


def test_a_plural_survives_a_leading_underscore() -> None:
    source = "def _users(rows):\n    yield from rows\n"

    assert codes(source) == []


def test_a_pluggy_hook_wrapper_is_left_alone() -> None:
    """`value = yield` is pluggy's send point, not iteration."""
    source = (
        "from pluggy import HookimplMarker\nhookimpl = HookimplMarker('x')\n\n"
        "@hookimpl(wrapper=True)\ndef letscode_system_prompt():\n"
        "    prompt = yield\n    return prompt\n"
    )

    assert codes(source) == []


def test_the_suggested_name_keeps_a_private_name_private() -> None:
    source = "def _entry(root):\n    yield root\n"

    [finding] = lint_source(source, MODULE)

    assert "_iter_entry" in finding.message
    assert "iter__entry" not in finding.message
