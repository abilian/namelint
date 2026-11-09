"""NAM104: a command verb that returns a value.

`reset_cache()` promises to act, not to answer, so a caller never looks
at what it returns. A value returned there is either lost or the name
is wrong.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

MODULE = Path("src/app/cache.py")


def codes(source: str) -> list[str]:
    return [finding.code for finding in lint_source(source, MODULE)]


def test_a_command_returning_a_value_is_reported() -> None:
    source = (
        "def set_shape(lines, width):\n    return [line[:width] for line in lines]\n"
    )

    assert codes(source) == ["NAM104"]


def test_a_command_returning_nothing_is_left_alone() -> None:
    source = "def reset_cache(cache):\n    cache.clear()\n"

    assert codes(source) == []


def test_an_early_return_none_is_left_alone() -> None:
    source = "def clear_break(self, line):\n    if not line:\n        return None\n    self.breaks.pop(line)\n"

    assert codes(source) == []


def test_returning_self_for_chaining_is_left_alone() -> None:
    source = "class Q:\n    def set_limit(self, n):\n        self.n = n\n        return self\n"

    assert codes(source) == []


def test_a_success_flag_is_left_alone() -> None:
    source = "def update_file(path):\n    if same(path):\n        return False\n    write(path)\n    return True\n"

    assert codes(source) == []


def test_forwarding_the_same_command_is_left_alone() -> None:
    source = "class Jar(Base):\n    def set_cookie(self, c):\n        return super().set_cookie(c)\n"

    assert codes(source) == []


def test_a_bare_protocol_name_is_left_alone() -> None:
    """`close()` and `update()` belong to their types' contracts."""
    source = "def close(self):\n    return self._sock.close_and_report()\n"

    assert codes(source) == []


def test_a_private_command_is_left_alone() -> None:
    source = "def _set_shape(lines):\n    return lines\n"

    assert codes(source) == []


def test_a_two_sided_verb_is_left_alone() -> None:
    """`load_` both fills `self` and returns data; the name cannot say which."""
    source = "def load_config(path):\n    return parse(path)\n"

    assert codes(source) == []


def test_a_long_returned_value_is_cut_in_the_message() -> None:
    """A constructor call with ten keywords must not make a 200-column line."""
    source = f"def clear_cookie():\n    return Cookie(key={'k' * 80!r})\n"

    (finding,) = lint_source(source, MODULE)

    assert finding.message.endswith("returns Cookie(key='kkkkkkkkkkkkkkkkkkkkkkkkkkk…")
