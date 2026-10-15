"""NAM108: a method that repeats its class name.

`config.read_config()` says "config" twice. Ambiguous cases (a user
name is not a user's name) are the allowlist's job; these tests cover
what the check decides on its own.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import check_source

MODULE = Path("src/app/config.py")


def codes(source: str, path: Path = MODULE) -> list[str]:
    return [finding.code for finding in check_source(source, path)]


def method(cls: str, *names: str) -> str:
    body = "".join(f"    def {name}(self):\n        pass\n" for name in names)
    return f"class {cls}:\n{body}"


def test_repeating_the_class_name_is_reported() -> None:
    assert codes(method("Config", "read_config")) == ["NAM108"]


def test_a_camel_case_class_matches_as_a_run_of_words() -> None:
    assert codes(method("CodeContext", "update_code_context")) == ["NAM108"]


def test_part_of_the_class_name_is_left_alone() -> None:
    """`ConfigLoader.config_path` names the config, not the loader."""
    assert codes(method("ConfigLoader", "config_path")) == []


def test_a_word_inside_another_word_is_left_alone() -> None:
    assert codes(method("Config", "reconfigure")) == []


def test_a_method_named_exactly_like_its_class_is_left_alone() -> None:
    """`Filter.filter` is a protocol method."""
    assert codes(method("Filter", "filter")) == []


def test_a_prefix_shared_by_three_methods_is_a_namespace() -> None:
    """tkinter's `Wm.wm_title`, `Wm.wm_frame`: a convention, not a slip."""
    assert codes(method("Wm", "wm_title", "wm_frame", "wm_state")) == []


def test_two_repeats_are_still_reported() -> None:
    assert codes(method("History", "history_next", "history_prev")) == [
        "NAM108",
        "NAM108",
    ]


def test_a_test_class_is_left_alone() -> None:
    assert codes(method("TestConfig", "test_config_loads")) == []


def test_a_private_method_is_left_alone() -> None:
    assert codes(method("Config", "_validate_config")) == []


def test_a_function_outside_a_class_is_left_alone() -> None:
    assert codes("def read_config():\n    pass\n") == []
