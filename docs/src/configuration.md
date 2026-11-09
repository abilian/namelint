# Configuration

namelint reads `[tool.namelint]` from the `pyproject.toml` in the current directory or its nearest parent. `namelint init` writes the table with every setting at its default:

```toml
[tool.namelint]
# select = ["NAM101", "NAM102", "NAM103", "NAM104", "NAM105", "NAM106", "NAM108"]
ignore = []
exclude = []
per-file-ignores = {}
respect-gitignore = true
output-format = "grouped"
```

`namelint check --show-settings` prints the settings in force and the file they came from.

## Settings

`select`
:   Lists the checks to run. Without it, every check runs except the opt-in `NAM107`.

`ignore`
:   Lists the checks to skip.

`exclude`
:   Lists shell patterns for paths to skip. They add to the directories always skipped: `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, `.tox`, `.nox`, `build` and `dist`. A file named on the command line is linted even when a pattern matches it, unless `--force-exclude` is given.

`per-file-ignores`
:   Maps a path pattern to the checks to skip in matching files: `{ "migrations/*" = ["NAM108"] }`.

`respect-gitignore`
:   Skips what git ignores, using `git ls-files`. Outside a git repository, or without git, namelint walks all directories.

`output-format`
:   `grouped`, `full`, `concise`, `json` or `github`. See [Running Checks](running-checks.md#output-formats).

## Path patterns

A path pattern is matched against each part of a path. It is also matched against the whole path, taken relative to the directory holding `pyproject.toml`. So `migrations/*` means the same thing from any working directory.

## Command line and configuration

On the command line, `--select` replaces the configured list, `--ignore` adds to it, and `--output-format` replaces the configured format.

An unknown key, an unknown code or a value of the wrong type is an error, with exit code 2, so a typo can't pass for a setting that was applied.
