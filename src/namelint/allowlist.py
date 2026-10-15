"""The allowlist: `[tool.namelint.allow]` in `pyproject.toml`.

Each key is a code, each value a list of names: a function name, or
`Class.method`, either with shell wildcards (`close_to_*`). This module
reads it, matches findings against it, and writes it back for
`namelint init` and `namelint allow`.

There is no TOML writer in the standard library, and a runtime
dependency is out (notes/02-specs.md §7). So writing replaces the text
of the `[tool.namelint.allow]` table and nothing else: every other line
of `pyproject.toml` is left byte for byte as it was.
"""

from __future__ import annotations

import json
import re
import tomllib
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING

from namelint.checks import CODES

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from namelint.finding import Finding

CONFIG = "pyproject.toml"
HEADER = "[tool.namelint.allow]"

_HEADER_LINE = re.compile(r"^\[tool\.namelint\.allow\][ \t]*(#.*)?$", re.MULTILINE)
_NEXT_TABLE = re.compile(r"^[ \t]*\[", re.MULTILINE)

Allowlist = dict[str, list[str]]


class ConfigError(Exception):
    """The allowlist in `pyproject.toml` is not what namelint reads."""

    def __init__(self, config: Path, problem: str) -> None:
        super().__init__(f"{config}: {problem}")


def find_config(start: Path) -> Path | None:
    """The `pyproject.toml` in `start` or its nearest parent, if any."""
    for directory in (start, *start.parents):
        config = directory / CONFIG
        if config.is_file():
            return config
    return None


def load(config: Path | None) -> Allowlist | None:
    """The validated allowlist in `config`, or None when it declares none.

    None and `{}` differ: an empty table is an allowlist `namelint init`
    already wrote, and must not write again.
    """
    if config is None:
        return None
    try:
        table = tomllib.loads(config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(config, str(exc)) from exc
    allow = table.get("tool", {}).get("namelint", {}).get("allow")
    if allow is None:
        return None
    for code, names in allow.items():
        if code not in CODES:
            raise ConfigError(config, f"unknown code {code} in {HEADER}")
        if not (isinstance(names, list) and all(isinstance(n, str) for n in names)):
            raise ConfigError(config, f"{code} must be a list of names")
    return allow


def allowed(finding: Finding, allow: Allowlist) -> bool:
    return any(
        fnmatchcase(finding.qualname, pattern) or fnmatchcase(finding.name, pattern)
        for pattern in allow.get(finding.code, ())
    )


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
        if text and load(config) is not None:
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
