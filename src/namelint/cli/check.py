"""`namelint check`: lint and report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cyclopts import Parameter

from namelint.cli.explain import (
    Level,
    explanation,
)
from namelint.cli.lint import (
    EXIT_CLEAN,
    EXIT_FINDINGS,
    Codes,
    UsageError,
    lint_paths,
    project,
    selected_codes,
)
from namelint.config import (
    OutputFormat,  # noqa: TC001 (Cyclopts reads annotations at runtime)
)
from namelint.report import (
    Reported,
    as_concise,
    as_github,
    as_grouped,
    as_json,
    as_settings,
    as_stats,
)


@Parameter(name="*")
@dataclass(frozen=True)
class CheckOptions:
    """The flags of `namelint check`, flattened onto its command line."""

    select: Codes = ()
    """Run only these checks (repeatable). NAM107 runs only when selected."""

    ignore: Codes = ()
    """Skip these checks (repeatable)."""

    output_format: OutputFormat | None = None
    """grouped: by file (default). full: grouped, with a hint under each
    finding. concise: one path:line:col line per finding, for editors.
    json: one JSON object per line. github: annotations in a GitHub
    Actions log."""

    stats: bool = False
    """Counts per check, with a rate per thousand functions."""

    no_allowlist: bool = False
    """Report everything, ignoring [tool.namelint.allow]."""

    exit_zero: bool = False
    """Exit 0 even when there are findings."""

    force_exclude: bool = False
    """Apply exclude to files named on the command line too, as pre-commit
    needs."""

    show_settings: bool = False
    """Print the settings this run resolves to, and where they came from,
    then exit."""

    explain: bool = False
    """After the report, explain each check that fired, once per check."""

    level: Level | None = None
    """How deep --explain goes: junior, senior (default) or expert."""


class LevelWithoutExplainError(UsageError):
    def __init__(self) -> None:
        super().__init__("--level needs --explain")


class ExplainFormatError(UsageError):
    def __init__(self, output: str) -> None:
        super().__init__(f"--explain does not combine with --output-format {output}")


def check(*paths: Path, options: CheckOptions | None = None) -> int:
    """Report where a function's name contradicts its body.

    Exits 0 when clean, 1 with findings, 2 when namelint itself fails.

    Parameters
    ----------
    paths
        Files or directories to lint (default: the current directory).
    """
    opts = options or CheckOptions()
    config, settings = project()
    output = opts.output_format or settings.output_format
    if opts.level and not opts.explain:
        raise LevelWithoutExplainError
    if opts.explain and output in {"json", "github"}:
        raise ExplainFormatError(output)
    selected = selected_codes(settings, opts.select, opts.ignore)
    if opts.show_settings:
        print(as_settings(config, settings, selected))
        return EXIT_CLEAN
    allow = {} if opts.no_allowlist else settings.allow or {}
    results, scanned = lint_paths(
        paths or (Path(),), selected, allow, settings, force_exclude=opts.force_exclude
    )
    if opts.stats:
        print(as_stats(results, scanned))
    else:
        _print(results, output)
    if opts.explain:
        for code in sorted({finding.code for _, finding in results}):
            print(f"\n{explanation(code, opts.level or 'senior')}")
    return EXIT_FINDINGS if results and not opts.exit_zero else EXIT_CLEAN


def _print(results: list[Reported], output: OutputFormat) -> None:
    if output == "json":
        body = as_json(results)
    elif output == "github":
        body = as_github(results)
    elif output == "concise":
        body = as_concise(results)
    else:
        body = as_grouped(results, hints=output == "full")
    if body:
        print(body)
