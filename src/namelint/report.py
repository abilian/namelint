"""The output shapes: grouped (with or without hints), concise, JSON,
GitHub annotations, stats, and the resolved settings.

`--stats` exists for calibration rather than for daily use. The question
it answers is "how often does this rule fire on a codebase nobody thinks
is badly named", and a rule that fires often there is a wrong rule.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from itertools import groupby
from typing import TYPE_CHECKING

from namelint.config import DEFAULT_EXCLUDE
from namelint.finding import Finding

if TYPE_CHECKING:
    from pathlib import Path

    from namelint.config import Settings

Reported = tuple[str, Finding]


def as_concise(results: Sequence[Reported]) -> str:
    """Render one line per finding, in the format every editor already parses."""
    return "\n".join(finding.rendered(path) for path, finding in results)


def as_grouped(results: Sequence[Reported], *, hints: bool) -> str:
    """Render findings under their file, for a person reading a terminal.

    Each path is printed once, and each finding below it starts with
    its position and code in aligned columns. With `hints`, the advice
    goes on its own line under the finding.
    """
    if not results:
        return ""
    blocks = []
    for path, group in groupby(results, key=lambda reported: reported[0]):
        findings = [finding for _path, finding in group]
        width = max(len(f"{f.line}:{f.col}") for f in findings)
        lines = [path]
        for f in findings:
            lines.append(f"  {f'{f.line}:{f.col}':<{width}}  {f.code}  {f.message}")
            if hints:
                lines.append(f"  {'':<{width}}  {'':<6}  hint: {f.hint}")
        blocks.append("\n".join(lines))
    files = len(blocks)
    total = len(results)
    summary = f"{total} finding{'s' * (total > 1)} in {files} file{'s' * (files > 1)}"
    return "\n\n".join([*blocks, summary])


def as_github(results: Sequence[Reported]) -> str:
    """Render GitHub Actions workflow commands, which annotate the diff.

    The format is `::error file=...,line=...::message`. A property value
    escapes `%`, CR, LF, `:` and `,`; the message escapes the first three.
    """
    return "\n".join(
        f"::error title=namelint {finding.code},file={_escaped(path, prop=True)},"
        f"line={finding.line},col={finding.col}::"
        + _escaped(f"{finding.code} {finding.message}; {finding.hint}", prop=False)
        for path, finding in results
    )


def _escaped(text: str, *, prop: bool) -> str:
    text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return text.replace(":", "%3A").replace(",", "%2C") if prop else text


def as_settings(config: Path, settings: Settings, selected: frozenset[str]) -> str:
    """Render the settings a run resolves to, and where they came from."""
    found = "" if config.is_file() else " (not found: defaults apply)"
    allow = settings.allow or {}
    lines = [
        f"settings: {config}{found}",
        f"select = {json.dumps(sorted(selected))}",
        f"exclude = {json.dumps([*DEFAULT_EXCLUDE, *settings.exclude])}",
        f"per-file-ignores = {json.dumps(dict(settings.per_file_ignores))}",
        f"respect-gitignore = {json.dumps(settings.respect_gitignore)}",
        f"output-format = {json.dumps(settings.output_format)}",
        f"allow: {sum(map(len, allow.values()))} patterns under {len(allow)} codes",
    ]
    return "\n".join(lines)


def as_json(results: Sequence[Reported]) -> str:
    """Render one JSON object per line, so counting is a pipe not a parser."""
    return "\n".join(
        json.dumps(
            {
                "path": path,
                "line": finding.line,
                "col": finding.col,
                "code": finding.code,
                "name": finding.name,
                "qualname": finding.qualname,
                "message": finding.message,
                "hint": finding.hint,
                "evidence": finding.evidence,
            },
            ensure_ascii=False,
        )
        for path, finding in results
    )


def as_stats(results: Sequence[Reported], functions: int) -> str:
    """Render counts per code, with a rate comparable across projects.

    Per thousand functions, because a rule firing twice in `click` and
    twice in CPython's `Lib` has told you two different things.
    """
    by_code = Counter(finding.code for _path, finding in results)
    width = max((len(code) for code in by_code), default=6)
    lines = [f"functions scanned: {functions}"]
    for code, count in sorted(by_code.items()):
        rate = count / functions * 1000 if functions else 0.0
        lines.append(f"  {code:<{width}}  {count:>6}  {rate:>7.2f} per 1000")
    if not by_code:
        lines.append("  no findings")
    return "\n".join(lines)
