"""The three output shapes: text, JSON, stats.

`--stats` exists for calibration rather than for daily use. The question
it answers is "how often does this rule fire on a codebase nobody thinks
is badly named", and a rule that fires often there is a wrong rule.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence

from namelint.finding import Finding

Reported = tuple[str, Finding]


def as_text(results: Sequence[Reported]) -> str:
    """Render one line per finding, in the format every editor already parses."""
    return "\n".join(finding.rendered(path) for path, finding in results)


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
                "message": finding.message,
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
