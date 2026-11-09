"""`namelint explain`: the naming conventions, for a reader new to them.

Each topic is `data/explain/<topic>.md`: a title line, then one `##`
section per level. The text lives in Markdown so it can be read and
reviewed as prose, outside the code.
"""

from __future__ import annotations

from importlib import resources
from typing import Literal, get_args

from namelint.checks import CODES
from namelint.cli.lint import EXIT_CLEAN, UnknownCodeError

Level = Literal["junior", "senior", "expert"]
LEVELS: tuple[str, ...] = get_args(Level)
OVERVIEW = "conventions"


def explain(code: str = OVERVIEW, /, *, level: Level = "senior") -> int:
    """Explain the naming conventions namelint checks, or one check.

    Parameters
    ----------
    code
        A check code such as NAM106 (default: the conventions as a whole).
    level
        junior: what the convention is, with an example. senior: why it
        matters and when to break it. expert: how the check decides and
        where it is wrong.
    """
    print(explanation(code.upper() if code != OVERVIEW else code, level))
    return EXIT_CLEAN


def explanation(topic: str, level: Level) -> str:
    """The title of `topic` and its section for `level`."""
    if topic != OVERVIEW and topic not in CODES:
        raise UnknownCodeError(topic)
    text = (
        resources.files("namelint")
        .joinpath(f"data/explain/{topic}.md")
        .read_text(encoding="utf-8")
    )
    title, _, body = text.partition("\n")
    sections = dict(_sections(body))
    return f"{title.removeprefix('# ')}\n\n{sections[level]}"


def _sections(body: str) -> list[tuple[str, str]]:
    """`(level, text)` for each `## Level` heading in `body`."""
    parts = body.split("\n## ")[1:]
    return [
        (heading.strip().lower(), text.strip())
        for heading, _, text in (part.partition("\n") for part in parts)
    ]
