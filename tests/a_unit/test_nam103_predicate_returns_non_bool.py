"""NAM103: a predicate whose body does not return a bool.

`if is_ready():` reads the name. A predicate returning a string or a
count is truthy for every value but one, so the empty string and the
zero are the bug.

The spec's rule for this family is that an unknown return is silence,
not a guess (`notes/02-specs.md` §2), so most of these tests check that
nothing fires.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

MODULE = Path("src/app/users.py")


def codes(source: str, path: Path = MODULE) -> list[str]:
    return [finding.code for finding in lint_source(source, path)]


def test_an_annotation_that_is_not_bool_is_reported() -> None:
    source = "def is_ready() -> str:\n    return state()\n"

    assert codes(source) == ["NAM103"]


def test_a_bool_annotation_is_left_alone() -> None:
    source = "def is_ready() -> bool:\n    return state() == 'ok'\n"

    assert codes(source) == []


def test_a_string_annotation_naming_bool_is_left_alone() -> None:
    """`-> "bool"` is a forward reference, and it is still a bool."""
    source = 'def is_ready() -> "bool":\n    return True\n'

    assert codes(source) == []


def test_a_type_guard_is_left_alone() -> None:
    """`TypeGuard[X]` returns a bool; the subscript says what it proves."""
    source = (
        "from typing import TypeGuard\n\n"
        "def is_str(value) -> TypeGuard[str]:\n    return isinstance(value, str)\n"
    )

    assert codes(source) == []


def test_a_type_is_is_left_alone() -> None:
    source = (
        "import typing\n\n"
        "def is_str(value) -> typing.TypeIs[str]:\n    return isinstance(value, str)\n"
    )

    assert codes(source) == []


def test_an_unannotated_predicate_returning_a_string_is_reported() -> None:
    source = "def has_name():\n    return 'anonymous'\n"

    assert codes(source) == ["NAM103"]


def test_an_unannotated_predicate_returning_a_list_is_reported() -> None:
    source = "def has_errors():\n    return [e for e in checks() if e]\n"

    assert codes(source) == ["NAM103"]


def test_an_unknown_return_produces_no_finding() -> None:
    """A call could return anything. The spec chooses silence over a guess."""
    source = "def is_ready():\n    return self._compute()\n"

    assert codes(source) == []


def test_returning_none_is_not_evidence_of_a_non_bool() -> None:
    """An early `return None` is how half the predicates ever written exit."""
    source = "def is_ready():\n    if not self.started:\n        return None\n    return True\n"

    assert codes(source) == []


def test_a_bool_literal_is_not_evidence() -> None:
    source = "def can_retry():\n    if done():\n        return False\n    return True\n"

    assert codes(source) == []


def test_a_non_predicate_name_is_left_alone() -> None:
    source = "def build_name() -> str:\n    return 'x'\n"

    assert codes(source) == []


def test_a_name_merely_starting_with_is_is_left_alone() -> None:
    """`issue_token` is not `is_`. The underscore is the whole boundary."""
    source = "def issue_token() -> str:\n    return 'x'\n"

    assert codes(source) == []


def test_a_generator_under_a_predicate_name_is_left_to_nam107() -> None:
    """Two findings on one function would be noise; NAM107 owns this one.

    `has_rows` would be silent under both checks, since NAM107 exempts a
    plural. The singular is what puts the two rules on the same function.
    """
    source = "def has_row():\n    yield 1\n"

    assert codes(source) == ["NAM107"]


def test_a_return_inside_a_nested_function_does_not_count() -> None:
    source = (
        "def is_ready():\n"
        "    def label():\n        return 'nested'\n"
        "    return bool(label())\n"
    )

    assert codes(source) == []


def test_an_async_predicate_is_checked_too() -> None:
    source = "async def is_ready() -> str:\n    return await state()\n"

    assert codes(source) == ["NAM103"]


def test_the_evidence_names_the_annotation() -> None:
    """A finding you can disagree with has to say what it saw."""
    findings = lint_source("def is_ready() -> list[str]:\n    return []\n", MODULE)

    assert findings[0].evidence == "annotated -> list[str]"


def test_the_evidence_names_the_returned_shape() -> None:
    findings = lint_source("def has_name():\n    return 'anonymous'\n", MODULE)

    assert findings[0].evidence == "returns 'anonymous'"


def test_a_factory_named_after_its_return_type_is_left_alone() -> None:
    """`is_instance_schema(cls) -> IsInstanceSchema` builds a schema.

    The `is_` belongs to the thing's name ("is-instance"), so it is not a
    predicate prefix. Four of the seven findings in the first corpus run
    were this, all of them wrong.
    """
    source = "def is_instance_schema(cls) -> IsInstanceSchema:\n    return {}\n"

    assert codes(source) == []


def test_a_handler_whose_last_word_names_its_return_is_left_alone() -> None:
    """pydantic's JSON-schema visitor: one method per core-schema kind."""
    source = "def is_instance_schema(self, schema) -> JsonSchemaValue:\n    return {}\n"

    assert codes(source) == []


def test_the_return_type_match_is_by_word_not_substring() -> None:
    """ "valid" and "validation" are two words, so this keeps its finding."""
    source = "def is_valid() -> ValidationResult:\n    return check()\n"

    assert codes(source) == ["NAM103"]


def test_an_any_annotation_is_unknown_and_produces_no_finding() -> None:
    """§2's rule for returns, applied to the annotation."""
    source = "def is_legacy_typeddict(_) -> Any:\n    return False\n"

    assert codes(source) == []


def test_a_check_returning_a_value_is_reported() -> None:
    """`check_` answers a question, so it returns a bool."""
    source = "def check_values(values):\n    return (values, [])\n"

    assert codes(source) == ["NAM103"]


def test_a_check_that_raises_instead_is_left_alone() -> None:
    source = (
        "def check_version(v) -> None:\n    if v < 2:\n        raise ValueError(v)\n"
    )

    assert codes(source) == []


def test_a_predicate_annotated_none_is_still_reported() -> None:
    """Only `check_` may answer by raising; `is_` must answer."""
    source = "def is_ready() -> None:\n    pass\n"

    assert codes(source) == ["NAM103"]
