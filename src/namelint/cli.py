"""The command line: walking, selection, exit codes.

`namelint PATH...` lints. Two commands write the allowlist instead:
`namelint init` adds an empty one to `pyproject.toml` (with
`--accept-existing`, one holding every current finding), and
`namelint allow` adds the current findings to it.

The imperative shell. Everything that touches the filesystem or decides
a process's fate lives here; `checks.py` stays pure.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator, Sequence
from importlib import metadata
from pathlib import Path

from namelint import allowlist
from namelint.allowlist import Allowlist, ConfigError
from namelint.checks import CODES, OPT_IN
from namelint.report import Reported, as_json, as_stats, as_text
from namelint.visitor import functions, lint_module

SKIP_DIRS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox", "build", "dist"}
)

# What `ast.parse` raises on input it cannot turn into a tree. A corpus
# run meets more than bad syntax: CPython's own test suite carries
# fixtures that raise `ValueError`, and a deeply nested literal raises
# `RecursionError`. One such file must not end a run over 23,000
# functions, which is what happened the first time this was measured.
UNPARSABLE = (SyntaxError, ValueError, RecursionError, OSError, UnicodeDecodeError)

COMMANDS = ("init", "allow")

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run namelint and return an exit code.

    0 clean, 1 findings, 2 the tool itself failed.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    # Dispatched by hand rather than with argparse subparsers, so that
    # `namelint src/` keeps working. A directory named `init` is still
    # reachable as `namelint ./init`.
    command = argv[0] if argv and argv[0] in COMMANDS else None
    args = _parser(command).parse_args(argv[1:] if command else argv)
    selected = _selected_codes(args.select, args.ignore)
    if not selected:
        print("error: --select and --ignore leave no checks enabled", file=sys.stderr)
        return EXIT_ERROR
    config = allowlist.find_config(Path.cwd())
    # With no `pyproject.toml` anywhere up the tree, the commands create
    # one in the current directory.
    target = config or Path.cwd() / allowlist.CONFIG
    try:
        allow = allowlist.load(config)
        if command == "init":
            return _init(
                target, allow, args.paths, selected, accept=args.accept_existing
            )
        if command == "allow":
            return _allow(target, allow or {}, args.paths, selected)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    in_force = {} if args.no_allowlist else allow or {}
    results, scanned = _lint(args.paths, selected, in_force)
    _print(results, scanned, stats=args.stats, as_jsonl=args.json)
    return EXIT_FINDINGS if results else EXIT_CLEAN


def _init(
    target: Path,
    existing: Allowlist | None,
    paths: Sequence[Path],
    selected: frozenset[str],
    *,
    accept: bool,
) -> int:
    """Add an empty `[tool.namelint.allow]`, or with `accept` one holding every finding.

    Refuses a project that already declares an allowlist, even an empty
    one: that one belongs to `namelint allow`.
    """
    if existing is not None:
        print(
            f"error: {target} already has {allowlist.HEADER}; use `namelint allow`",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if accept:
        return _allow(target, {}, paths, selected)
    allowlist.write(target, {})
    print(f"{target}: added an empty {allowlist.HEADER}")
    return EXIT_CLEAN


def _allow(
    target: Path, allow: Allowlist, paths: Sequence[Path], selected: frozenset[str]
) -> int:
    """Add every finding not yet allowed to the allowlist in `target`."""
    results, _ = _lint(paths, selected, allow)
    findings = [finding for _, finding in results]
    allowlist.write(target, allowlist.merged(allow, findings))
    added = len({(f.code, f.qualname) for f in findings})
    print(f"{target}: {added} names added to {allowlist.HEADER}")
    return EXIT_CLEAN


def _lint(
    paths: Sequence[Path], selected: frozenset[str], allow: Allowlist
) -> tuple[list[Reported], int]:
    """Every finding under `paths` not allowed, and the functions scanned."""
    results: list[Reported] = []
    scanned = 0
    for path in _python_files(paths):
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
        results += [
            (str(path), finding)
            for finding in lint_module(tree, path)
            if finding.code in selected and not allowlist.allowed(finding, allow)
        ]
    return results, scanned


def _print(
    results: list[Reported], functions: int, *, stats: bool, as_jsonl: bool
) -> None:
    if stats:
        print(as_stats(results, functions))
        return
    body = as_json(results) if as_jsonl else as_text(results)
    if body:
        print(body)


def _parser(command: str | None) -> argparse.ArgumentParser:
    if command is None:
        parser = argparse.ArgumentParser(
            prog="namelint",
            description="Report where a function's name contradicts its body.",
            epilog="commands: `namelint init` adds an allowlist to pyproject.toml;"
            " `namelint allow` accepts the current findings into it.",
        )
        parser.add_argument("paths", nargs="+", type=Path, help="files or directories")
    else:
        parser = argparse.ArgumentParser(
            prog=f"namelint {command}",
            description=(
                "Add an empty [tool.namelint.allow] table to pyproject.toml."
                if command == "init"
                else "Add every current finding to the allowlist in pyproject.toml."
            ),
        )
        parser.add_argument(
            "paths",
            nargs="*",
            type=Path,
            default=[Path()],
            help="files or directories (default: the current directory)",
        )
    parser.add_argument(
        "--select",
        action="append",
        default=[],
        choices=CODES,
        metavar="CODE",
        help="run only these checks (repeatable); NAM107 runs only when selected",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        choices=CODES,
        metavar="CODE",
        help="skip these checks (repeatable)",
    )
    if command == "init":
        parser.add_argument(
            "--accept-existing",
            action="store_true",
            help="fill the allowlist with every current finding",
        )
    if command is None:
        parser.add_argument(
            "--json", action="store_true", help="one JSON object per line"
        )
        parser.add_argument(
            "--stats", action="store_true", help="counts per code, for calibration"
        )
        parser.add_argument(
            "--no-allowlist",
            action="store_true",
            help="report everything, ignoring [tool.namelint.allow]",
        )
    parser.add_argument(
        "--version",
        action="version",
        # The version lives in pyproject.toml; this reads it back from the
        # installed package's metadata.
        version=f"namelint {metadata.version('namelint')}",
    )
    return parser


def _selected_codes(select: list[str], ignore: list[str]) -> frozenset[str]:
    chosen = frozenset(select) if select else frozenset(CODES) - OPT_IN
    return chosen - frozenset(ignore)


def _python_files(paths: Sequence[Path]) -> Iterator[Path]:
    """Yield every `.py` file under `paths`, sorted, skipping the usual noise."""
    for path in paths:
        if path.is_file():
            yield path
        else:
            yield from sorted(
                found
                for found in path.rglob("*.py")
                if not SKIP_DIRS.intersection(found.parts)
            )


__all__ = ["main"]
