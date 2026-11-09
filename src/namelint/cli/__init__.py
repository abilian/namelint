"""The command line: `namelint check`, `init`, `allow` and `explain`."""

from __future__ import annotations

import sys
from importlib import metadata
from typing import TYPE_CHECKING

from cyclopts import App, CycloptsError, Parameter

from namelint.cli.check import check
from namelint.cli.explain import explain
from namelint.cli.init import allow, init
from namelint.cli.lint import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, UsageError
from namelint.config import ConfigError

if TYPE_CHECKING:
    from collections.abc import Sequence

app = App(
    name="namelint",
    help="Report where a Python function's name contradicts its body.",
    # The version lives in pyproject.toml; this reads it back from the
    # installed package's metadata.
    version=f"namelint {metadata.version('namelint')}",
    # No `--no-stats` or `--empty-select`: every flag means one thing.
    default_parameter=Parameter(negative=(), show_default=False),
)
app.command(check)
app.command(init)
app.command(allow)
app.command(explain)


def main(argv: Sequence[str] | None = None) -> int:
    """Run namelint and return an exit code.

    0 clean, 1 findings, 2 the tool itself failed, a bad command line
    included.
    """
    try:
        result = app(
            sys.argv[1:] if argv is None else list(argv),
            exit_on_error=False,
            result_action="return_value",
        )
    except CycloptsError:
        return EXIT_ERROR  # Cyclopts has already printed what was wrong.
    except (ConfigError, UsageError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_CLEAN if result is None else result


__all__ = ["EXIT_CLEAN", "EXIT_ERROR", "EXIT_FINDINGS", "app", "main"]
