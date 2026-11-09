"""`namelint init` and `namelint allow`: writing the configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from namelint import allowlist, config
from namelint.cli.lint import (
    EXIT_CLEAN,
    Codes,
    UsageError,
    lint_paths,
    project,
    selected_codes,
)

if TYPE_CHECKING:
    from namelint.config import Allowlist


class AlreadyConfiguredError(UsageError):
    def __init__(self, target: Path) -> None:
        super().__init__(
            f"{target} already has {config.TABLE}; edit it, or use `namelint allow`"
        )


def init(*paths: Path, accept_existing: bool = False) -> int:
    """Add a [tool.namelint] table to pyproject.toml, with every setting at its default.

    Parameters
    ----------
    paths
        With --accept-existing, the files or directories to lint (default:
        the current directory).
    accept_existing
        Fill [tool.namelint.allow] with every current finding, so the next
        run is clean and only new code is reported.
    """
    target, _settings = project()
    if config.load(target) is not None:
        raise AlreadyConfiguredError(target)
    config.add_table(target)
    if accept_existing:
        return allow(*paths)
    allowlist.write(target, {})
    print(f"{target}: added {config.TABLE}")
    return EXIT_CLEAN


def allow(
    *paths: Path, select: Codes = (), ignore: Codes = (), prune: bool = False
) -> int:
    """Add every current finding to [tool.namelint.allow] in pyproject.toml.

    Parameters
    ----------
    paths
        Files or directories to lint (default: the current directory).
    select
        Record only the findings of these checks (repeatable).
    ignore
        Leave out the findings of these checks (repeatable).
    prune
        Also remove the entries that no longer match any finding. Run it over
        the whole project: an entry for code outside the paths given looks
        unused.
    """
    target, settings = project()
    existing = settings.allow or {}
    selected = selected_codes(settings, select, ignore)
    # Pruning needs every finding, allowed or not, to tell which entries
    # still match something.
    results, _ = lint_paths(
        paths or (Path(),), selected, {} if prune else existing, settings
    )
    findings = [finding for _, finding in results]
    kept = allowlist.pruned(existing, findings, selected) if prune else existing
    updated = allowlist.merged(
        kept, [f for f in findings if not allowlist.allowed(f, kept)]
    )
    allowlist.write(target, updated)
    before, after = _entries(existing), _entries(updated)
    print(
        f"{target}: {len(after - before)} names added to {allowlist.HEADER},"
        f" {len(before - after)} removed"
    )
    return EXIT_CLEAN


def _entries(allow: Allowlist) -> set[tuple[str, str]]:
    return {(code, pattern) for code, patterns in allow.items() for pattern in patterns}
