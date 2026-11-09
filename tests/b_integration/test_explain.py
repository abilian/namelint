"""`namelint explain`: one text per topic and level."""

from __future__ import annotations

import pytest

from namelint.checks import CODES
from namelint.cli import EXIT_CLEAN, EXIT_ERROR, main
from namelint.cli.explain import LEVELS, OVERVIEW, explanation


@pytest.mark.parametrize("topic", [OVERVIEW, *CODES])
@pytest.mark.parametrize("level", LEVELS)
def test_every_topic_is_explained_at_every_level(topic: str, level) -> None:
    """A ninth check without its explanation fails here."""
    text = explanation(topic, level)

    title, _, body = text.partition("\n\n")
    assert title.startswith(topic if topic in CODES else "The naming conventions")
    assert body.strip()


def test_a_level_shows_its_own_section_only(capsys) -> None:
    assert main(["explain", "NAM106", "--level", "junior"]) == EXIT_CLEAN

    out = capsys.readouterr().out
    assert out.startswith("NAM106: a get_ that performs I/O\n")
    assert "fetch_user" in out
    assert "## " not in out
    assert "requests.get` calls `request()" not in out  # that is the expert text


def test_a_code_is_case_insensitive(capsys) -> None:
    main(["explain", "nam101"])

    assert capsys.readouterr().out.startswith("NAM101")


def test_without_a_code_it_explains_the_conventions(capsys) -> None:
    main(["explain"])

    assert capsys.readouterr().out.startswith("The naming conventions")


def test_an_unknown_code_is_an_error(capsys) -> None:
    assert main(["explain", "NAM999"]) == EXIT_ERROR
    assert "unknown code NAM999" in capsys.readouterr().err
