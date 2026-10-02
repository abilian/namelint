"""The command line: walking, selection, exit codes.

The imperative shell. Everything that touches the filesystem or decides
a process's fate lives here; `checks.py` stays pure.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

from namelint import __version__
from namelint.checks import CODES
from namelint.finding import Finding
from namelint.report import Reported, as_json, as_stats, as_text
from namelint.visitor import check_module

SKIP_DIRS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox", "build", "dist"}
)

# What `ast.parse` raises on input it cannot turn into a tree. A corpus
# run meets more than bad syntax: CPython's own test suite carries
# fixtures that raise `ValueError`, and a deeply nested literal raises
# `RecursionError`. One such file must not end a run over 23,000
# functions, which is what happened the first time this was measured.
UNPARSABLE = (SyntaxError, ValueError, RecursionError, OSError, UnicodeDecodeError)

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Lint the given paths and return an exit code.

    0 clean, 1 findings, 2 the tool itself failed.
    """
    args = _parser().parse_args(argv)
    selected = _selected_codes(args.select, args.ignore)
    if not selected:
        print("error: --select and --ignore leave no checks enabled", file=sys.stderr)
        return EXIT_ERROR

    results: list[Reported] = []
    functions = 0
    for path in _python_files(args.paths):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except UNPARSABLE as exc:
            # A file we cannot parse is reported and skipped. Refusing the
            # whole run because one vendored file is Python 2 would make
            # the corpus runs in notes/02-specs.md §6 impossible.
            print(f"{path}: skipped, {exc.__class__.__name__}: {exc}", file=sys.stderr)
            continue
        functions += _count_functions(tree)
        results += [
            (str(path), finding)
            for finding in check_module(tree, path)
            if finding.code in selected
        ]

    _print(results, functions, stats=args.stats, as_jsonl=args.json)
    return EXIT_FINDINGS if results else EXIT_CLEAN


def _print(
    results: list[Reported], functions: int, *, stats: bool, as_jsonl: bool
) -> None:
    if stats:
        print(as_stats(results, functions))
        return
    body = as_json(results) if as_jsonl else as_text(results)
    if body:
        print(body)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="namelint",
        description="Report where a function's name contradicts its body.",
    )
    parser.add_argument("paths", nargs="+", type=Path, help="files or directories")
    parser.add_argument(
        "--select",
        action="append",
        default=[],
        metavar="CODE",
        help="run only these checks (repeatable)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="CODE",
        help="skip these checks (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="one JSON object per line")
    parser.add_argument(
        "--stats", action="store_true", help="counts per code, for calibration"
    )
    parser.add_argument(
        "--version", action="version", version=f"namelint {__version__}"
    )
    return parser


def _selected_codes(select: list[str], ignore: list[str]) -> frozenset[str]:
    chosen = frozenset(select) & frozenset(CODES) if select else frozenset(CODES)
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


def _count_functions(tree: ast.Module) -> int:
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )


__all__ = ["Finding", "main"]
