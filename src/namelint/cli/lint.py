"""What `check` and `allow` share: settings, file walking, the lint loop.

The imperative shell. Everything that touches the filesystem or decides
a process's fate lives under `cli/`; `checks.py` stays pure.
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from cyclopts import Parameter

from namelint import allowlist, config
from namelint.checks import CODES, OPT_IN
from namelint.config import DEFAULT_EXCLUDE, Settings
from namelint.visitor import functions, lint_module

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from namelint.config import Allowlist
    from namelint.report import Reported

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

# What `ast.parse` raises on input it cannot turn into a tree. A corpus
# run meets more than bad syntax: CPython's own test suite has fixtures
# that raise `ValueError`, and a deeply nested literal raises
# `RecursionError`. One such file must not end a run over 23,000
# functions, which is what happened the first time this was measured.
UNPARSABLE = (SyntaxError, ValueError, RecursionError, OSError, UnicodeDecodeError)


class UsageError(ValueError):
    """The command line asks for something namelint cannot do.

    A `ValueError`, so Cyclopts reports one raised by a validator as a
    bad argument.
    """


class UnknownCodeError(UsageError):
    def __init__(self, code: str) -> None:
        super().__init__(f"unknown code {code}; known: {', '.join(CODES)}")


class NothingSelectedError(UsageError):
    def __init__(self) -> None:
        super().__init__("select and ignore leave no checks enabled")


def _known_codes(_type: object, codes: Sequence[str] | None) -> None:
    for code in codes or ():
        if code not in CODES:
            raise UnknownCodeError(code)


Codes = Annotated[tuple[str, ...], Parameter(validator=_known_codes)]


def project() -> tuple[Path, Settings]:
    """The `pyproject.toml` that governs this run, and its settings.

    With no `pyproject.toml` anywhere up the tree, the path is the one
    `init` and `allow` would create in the current directory.
    """
    target = config.find_config(Path.cwd()) or Path.cwd() / config.CONFIG
    return target, config.load(target) or Settings(root=target.parent)


def selected_codes(
    settings: Settings, select: Sequence[str], ignore: Sequence[str]
) -> frozenset[str]:
    """The checks to run: the command line's `select` wins over the settings',
    and both lists of ignored codes apply."""
    chosen = select or settings.select
    codes = frozenset(chosen) if chosen else frozenset(CODES) - OPT_IN
    codes -= frozenset([*settings.ignore, *ignore])
    if not codes:
        raise NothingSelectedError
    return codes


def lint_paths(
    paths: Sequence[Path],
    selected: frozenset[str],
    allow: Allowlist,
    settings: Settings,
    *,
    force_exclude: bool = False,
) -> tuple[list[Reported], int]:
    """Every finding under `paths` not allowed, and the functions scanned."""
    walk = _Walk(
        settings.root,
        (*DEFAULT_EXCLUDE, *settings.exclude),
        settings.respect_gitignore,
    )
    results: list[Reported] = []
    scanned = 0
    for path in walk.python_files(paths, force_exclude=force_exclude):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except UNPARSABLE as exc:
            # A file we cannot parse is reported and skipped. Refusing the
            # whole run because one vendored file is Python 2 would make
            # the corpus runs in notes/02-specs.md §6 impossible.
            print(f"{path}: skipped, {exc.__class__.__name__}: {exc}", file=sys.stderr)
            continue
        # Counted the way the visitor walks, nested functions excluded,
        # so `--stats` divides by the functions that were checked.
        scanned += sum(1 for _ in functions(tree))
        here = selected - walk.ignored_codes(path, settings.per_file_ignores)
        results += [
            (str(path), finding)
            for finding in lint_module(tree, path)
            if finding.code in here and not allowlist.allowed(finding, allow)
        ]
    return results, scanned


@dataclass(frozen=True)
class _Walk:
    """Which files a run reads, and how a path matches a pattern."""

    root: Path
    exclude: tuple[str, ...]
    respect_gitignore: bool

    def python_files(
        self, paths: Sequence[Path], *, force_exclude: bool
    ) -> Iterator[Path]:
        """Every `.py` file under `paths`, sorted, skipping `exclude`.

        A file named on the command line is linted even when excluded,
        since asking for it by name is the clearest instruction there
        is. `force_exclude` turns that off for tools such as pre-commit,
        which name every file they pass.
        """
        for path in paths:
            if path.is_file():
                if not (force_exclude and self._matches(path, self.exclude)):
                    yield path
                continue
            found = _git_files(path) if self.respect_gitignore else None
            if found is None:
                found = sorted(path.rglob("*.py"))
            yield from (f for f in found if not self._matches(f, self.exclude))

    def ignored_codes(
        self, path: Path, per_file: dict[str, tuple[str, ...]]
    ) -> frozenset[str]:
        return frozenset(
            code
            for pattern, codes in per_file.items()
            if self._matches(path, (pattern,))
            for code in codes
        )

    def _matches(self, path: Path, patterns: Sequence[str]) -> bool:
        """Whether a pattern matches a part of `path`, or the whole of it.

        The path is taken relative to `root` when it lies under it, so
        `migrations/*` means the same from any working directory.
        """
        resolved = path.resolve()
        relative = (
            resolved.relative_to(self.root.resolve())
            if resolved.is_relative_to(self.root.resolve())
            else path
        )
        candidates = (*relative.parts, relative.as_posix())
        return any(
            fnmatchcase(candidate, pattern)
            for pattern in patterns
            for candidate in candidates
        )


def _git_files(directory: Path) -> list[Path] | None:
    """The `.py` files under `directory` that git does not ignore, sorted.

    None outside a git work tree, or without git: the caller then walks
    the directory itself.
    """
    git = shutil.which("git")
    if git is None:
        return None
    listed = subprocess.run(  # noqa: S603 (fixed arguments, no shell)
        [
            git,
            "-C",
            str(directory),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.py",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if listed.returncode != 0:
        return None
    # `--cached` also lists tracked files deleted from the work tree.
    return sorted(
        directory / name
        for name in listed.stdout.split("\0")
        if name and (directory / name).is_file()
    )
