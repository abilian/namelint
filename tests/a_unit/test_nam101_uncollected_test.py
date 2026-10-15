"""NAM101: a function pytest will never collect.

The defect is not a style preference. A function that asserts and is not
collected reports nothing, and a suite that stays green over it is
reporting nothing about the code it claims to cover.

The hard part is telling a test from an assertion-bearing helper, so
most of these tests are about staying silent.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

TEST_MODULE = Path("tests/test_users.py")
APP_MODULE = Path("src/app/users.py")


def codes(source: str, path: Path = TEST_MODULE) -> list[str]:
    return [finding.code for finding in lint_source(source, path)]


def test_an_asserting_zero_arg_function_in_a_test_module_is_reported() -> None:
    source = "def check_user_is_valid():\n    assert build().ok\n"

    assert codes(source) == ["NAM101"]


def test_a_helper_taking_what_it_checks_is_not_a_test() -> None:
    """`assert_ok(response)` is a helper. Arity is the discriminator."""
    source = "def assert_ok(response):\n    assert response.ok\n"

    assert codes(source) == []


def test_a_collected_test_is_left_alone() -> None:
    source = "def test_user_is_valid():\n    assert build().ok\n"

    assert codes(source) == []


def test_a_fixture_is_left_alone() -> None:
    """A fixture asserts sometimes and is never collected as a test."""
    source = "import pytest\n\n@pytest.fixture\ndef client():\n    assert True\n    return 1\n"

    assert codes(source) == []


def test_a_function_with_no_assertion_is_left_alone() -> None:
    source = "def build_user():\n    return User()\n"

    assert codes(source) == []


def test_pytest_raises_counts_as_an_assertion() -> None:
    source = (
        "import pytest\n\ndef user_rejects_bad_input():\n"
        "    with pytest.raises(ValueError):\n        parse('')\n"
    )

    assert codes(source) == ["NAM101"]


def test_outside_a_test_module_nothing_is_reported() -> None:
    """The same function in `src/` is ordinary code."""
    source = "def check_user_is_valid():\n    assert build().ok\n"

    assert codes(source, APP_MODULE) == []


def test_self_does_not_count_toward_arity() -> None:
    source = (
        "class TestUser:\n    def user_is_valid(self):\n        assert build().ok\n"
    )

    assert codes(source) == ["NAM101"]


def test_an_assertion_in_a_nested_helper_does_not_promote_its_parent() -> None:
    """`ast.walk` would cross the function boundary and report `build`."""
    source = (
        "def build():\n    def inner(value):\n        assert value\n    return inner\n"
    )

    assert codes(source) == []


def test_a_private_helper_is_left_alone() -> None:
    """A leading underscore says "not collected" as plainly as a name can.

    All nine findings in the first corpus run were `_`-prefixed helpers,
    and all nine were wrong.
    """
    source = "def _load_migration():\n    assert build().ok\n"

    assert codes(source) == []


def test_unittest_lifecycle_methods_are_left_alone() -> None:
    source = (
        "import unittest\n\nclass T(unittest.TestCase):\n"
        "    def setUp(self):\n        assert self.db\n"
        "    def tearDown(self):\n        assert self.db\n"
    )

    assert codes(source) == []


def test_pytest_xunit_setup_is_left_alone() -> None:
    source = "def setup_module():\n    assert PATH.exists()\n"

    assert codes(source) == []
