"""The allowlist: `[tool.namelint.allow]` in `pyproject.toml`.

Each key is a code, each value a list of names: a function name, or
`Class.method`, either with shell wildcards (`close_to_*`). This module
matches findings against it, and writes it back for `namelint init`
and `namelint allow`. `config.py` reads it.

There is no TOML writer in the standard library, and the only runtime
dependency is the command line's (notes/02-specs.md §7). So writing replaces the text
of the `[tool.namelint.allow]` table and nothing else: every other line
of `pyproject.toml` is left byte for byte as it was.
"""

from __future__ import annotations

import json
import re
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING

from namelint import config as settings
from namelint.config import Allowlist, ConfigError

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from namelint.finding import Finding

HEADER = "[tool.namelint.allow]"

_HEADER_LINE = re.compile(r"^\[tool\.namelint\.allow\][ \t]*(#.*)?$", re.MULTILINE)
_NEXT_TABLE = re.compile(r"^[ \t]*\[", re.MULTILINE)


def allowed(finding: Finding, allow: Allowlist) -> bool:
    return any(_matches(finding, pattern) for pattern in allow.get(finding.code, ()))


def pruned(
    allow: Allowlist, findings: Sequence[Finding], selected: frozenset[str]
) -> Allowlist:
    """`allow` without the patterns that match none of `findings`.

    A code that did not run says nothing about its patterns, so they stay.
    A code left with no patterns is dropped.
    """
    kept = {
        code: [
            pattern
            for pattern in patterns
            if code not in selected
            or any(f.code == code and _matches(f, pattern) for f in findings)
        ]
        for code, patterns in allow.items()
    }
    return {code: patterns for code, patterns in kept.items() if patterns}


def _matches(finding: Finding, pattern: str) -> bool:
    return fnmatchcase(finding.qualname, pattern) or fnmatchcase(finding.name, pattern)


def merged(allow: Allowlist, findings: Iterable[Finding]) -> Allowlist:
    """`allow` plus the qualified name of every finding, sorted, no repeats."""
    names = {code: set(entries) for code, entries in allow.items()}
    for finding in findings:
        names.setdefault(finding.code, set()).add(finding.qualname)
    return {code: sorted(names[code]) for code in sorted(names)}


def write(config: Path, allow: Allowlist) -> None:
    """Replace the `[tool.namelint.allow]` table in `config`, or append one.

    Comments inside that table are lost; everything outside it is kept.
    An allowlist spelled some other way (`allow = {...}` under
    `[tool.namelint]`) cannot be rewritten in place, so it is refused
    rather than duplicated.
    """
    text = config.read_text(encoding="utf-8") if config.is_file() else ""
    table = _render(allow)
    header = _HEADER_LINE.search(text)
    if header is None:
        loaded = settings.load(config) if text else None
        if loaded is not None and loaded.allow is not None:
            raise ConfigError(
                config, f"allowlist is not a {HEADER} table; edit it by hand"
            )
        text = (text.rstrip("\n") + "\n\n" if text else "") + table
    else:
        following = _NEXT_TABLE.search(text, header.end())
        end = following.start() if following else len(text)
        tail = text[end:]
        text = text[: header.start()] + table + ("\n" + tail if tail else "")
    config.write_text(text, encoding="utf-8")


def _render(allow: Allowlist) -> str:
    lines = [HEADER]
    for code, names in allow.items():
        lines.append(f"{code} = [")
        # A JSON string is a valid TOML basic string, escapes included.
        lines += [f"    {json.dumps(name)}," for name in names]
        lines.append("]")
    return "\n".join(lines) + "\n"
