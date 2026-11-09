"""The `[tool.namelint]` table in `pyproject.toml`.

```toml
[tool.namelint]
select = ["NAM101", "NAM106"]   # run only these (default: all but NAM107)
ignore = ["NAM108"]             # never run these
exclude = ["migrations"]        # shell patterns, on top of .venv, build...
per-file-ignores = { "scripts/*" = ["NAM106"] }
respect-gitignore = false       # default: skip what git ignores
output-format = "full"          # grouped, full, concise, json or github

[tool.namelint.allow]
NAM104 = ["update_width", "close_to_*"]
```

Every key is optional, and an unknown key is an error, so a typo never
passes for a setting that was applied.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast, get_args

from namelint.checks import CODES

CONFIG = "pyproject.toml"
TABLE = "[tool.namelint]"

OutputFormat = Literal["grouped", "full", "concise", "json", "github"]
FORMATS: tuple[str, ...] = get_args(OutputFormat)

Allowlist = dict[str, list[str]]

# Skipped in every walk; `exclude` in the settings adds to these.
DEFAULT_EXCLUDE = (
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".tox",
    ".nox",
    "build",
    "dist",
)

_LISTS = ("select", "ignore", "exclude")
_KEYS = frozenset(
    {*_LISTS, "output-format", "per-file-ignores", "respect-gitignore", "allow"}
)


class ConfigError(Exception):
    """The namelint configuration in `pyproject.toml` is not what namelint reads."""

    def __init__(self, config: Path, problem: str) -> None:
        super().__init__(f"{config}: {problem}")


@dataclass(frozen=True)
class Settings:
    """`[tool.namelint]`, validated. The defaults are what an empty table means."""

    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    output_format: OutputFormat = "grouped"
    # A shell pattern for paths, then the codes to skip in them.
    per_file_ignores: dict[str, tuple[str, ...]] = field(default_factory=dict)
    respect_gitignore: bool = True
    # The directory holding `pyproject.toml`. Path patterns are relative
    # to it, so they mean the same from any working directory.
    root: Path = field(default_factory=Path)
    # None and `{}` differ: an empty table is one `namelint init` already
    # wrote, and must not write again.
    allow: Allowlist | None = None


def find_config(start: Path) -> Path | None:
    """The `pyproject.toml` in `start` or its nearest parent, if any."""
    for directory in (start, *start.parents):
        config = directory / CONFIG
        if config.is_file():
            return config
    return None


def load(config: Path | None) -> Settings | None:
    """The settings in `config`, or None when it has no `[tool.namelint]`."""
    if config is None or not config.is_file():
        return None
    try:
        document = tomllib.loads(config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(config, str(exc)) from exc
    table = document.get("tool", {}).get("namelint")
    if table is None:
        return None
    unknown = sorted(set(table) - _KEYS)
    if unknown:
        raise ConfigError(config, f"unknown key {unknown[0]!r} in {TABLE}")
    lists = {key: _strings(config, key, table.get(key, [])) for key in _LISTS}
    for key in ("select", "ignore"):
        _known_codes(config, key, lists[key])
    output = table.get("output-format", "grouped")
    if output not in FORMATS:
        raise ConfigError(
            config, f"output-format must be one of {', '.join(FORMATS)}, not {output!r}"
        )
    gitignore = table.get("respect-gitignore", True)
    if not isinstance(gitignore, bool):
        raise ConfigError(config, "respect-gitignore must be true or false")
    allow = table.get("allow")
    if allow is not None:
        _check_allow(config, allow)
    return Settings(
        select=tuple(lists["select"]),
        ignore=tuple(lists["ignore"]),
        exclude=tuple(lists["exclude"]),
        output_format=cast("OutputFormat", output),
        per_file_ignores=_per_file_ignores(config, table.get("per-file-ignores", {})),
        respect_gitignore=gitignore,
        root=config.parent,
        allow=allow,
    )


def _strings(config: Path, key: str, value: object) -> list[str]:
    if not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
        raise ConfigError(config, f"{key} must be a list of strings")
    return value


def _known_codes(config: Path, key: str, codes: list[str]) -> None:
    for code in codes:
        if code not in CODES:
            raise ConfigError(config, f"unknown code {code} in {key}")


def _per_file_ignores(config: Path, table: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(table, dict):
        raise ConfigError(config, "per-file-ignores must be a table of patterns")
    for pattern, codes in table.items():
        _known_codes(config, "per-file-ignores", _strings(config, pattern, codes))
    return {pattern: tuple(codes) for pattern, codes in table.items()}


def _check_allow(config: Path, allow: object) -> None:
    if not isinstance(allow, dict):
        raise ConfigError(config, "allow must be a table of codes")
    for code, names in allow.items():
        if code not in CODES:
            raise ConfigError(config, f"unknown code {code} in [tool.namelint.allow]")
        _strings(config, code, names)


# What `namelint init` writes: every setting at its default, so the
# table shows what can be changed without a trip to the README.
TEMPLATE = """\
[tool.namelint]
# Every check runs except NAM107, which is opt-in. `select` narrows the
# set and `ignore` removes from it. `namelint explain CODE` describes one.
# select = ["NAM101", "NAM102", "NAM103", "NAM104", "NAM105", "NAM106", "NAM108"]
ignore = []
# Shell patterns for paths to skip, on top of .venv, build, dist and the like.
exclude = []
# Checks to skip in some files, such as { "migrations/*" = ["NAM108"] }.
per-file-ignores = {}
# Skip what git ignores. Outside a git repository, every file is walked.
respect-gitignore = true
# grouped, full (a hint under each finding), concise (one line each),
# json, or github (annotations in a GitHub Actions log).
output-format = "grouped"
"""


def add_table(config: Path) -> None:
    """Append `TEMPLATE` to `config`, creating the file if there is none."""
    text = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        (text.rstrip("\n") + "\n\n" if text else "") + TEMPLATE, encoding="utf-8"
    )
