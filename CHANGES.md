# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] 2026-11-09

### Added

- `--output-format` chooses the output: `grouped` (the default) prints each file once with its findings below it, `full` adds a hint under each finding, `concise` is the former one-line output for editors and CI, and `json` is the former `--json`.
- JSON output includes `hint`. `Finding` has a new `hint` field.
- A `[tool.namelint]` table in `pyproject.toml` sets `select`, `ignore`, `exclude` and `output-format`. The command line's `--select` and `--output-format` replace the configured values, and `--ignore` adds to them. An unknown key is an error.
- `namelint explain [CODE] [--level junior|senior|expert]` explains the naming conventions, or one check, at three depths.
- `--output-format github` prints GitHub Actions annotations.
- `--exit-zero` reports findings and exits 0.
- `--show-settings` prints the resolved settings with the path of their `pyproject.toml`.
- `--force-exclude` applies `exclude` to files named on the command line, for pre-commit.
- A pre-commit hook, `namelint`, in `.pre-commit-hooks.yaml`.
- `per-file-ignores` in `[tool.namelint]` skips checks in files matching a path pattern.
- Directory walks skip what git ignores. Set `respect-gitignore = false` to walk all files.
- `namelint allow --prune` also removes allowlist entries that match no finding.

### Changed

- Linting is now `namelint check PATH...`. A bare `namelint PATH...` is an error. With no path, `check` lints the current directory.
- `namelint init` writes `[tool.namelint]` with each setting at its default, as well as the empty allowlist. It refuses to run when `[tool.namelint]` already exists.
- `--json` is replaced by `--output-format json`.
- The command line is built on Cyclopts, namelint's first runtime dependency. The checks still import nothing beyond `ast`.
- The default output is grouped by file. Use `--output-format concise` for the previous `path:line:col:` lines.
- `Finding.message` no longer contains the advice, which moved to `Finding.hint`.
- A returned expression quoted in a `NAM103` or `NAM104` message is cut at 40 characters.

## [0.2.0] - 2026-10-15

### Added

- `NAM102`: a `@property` whose name opens with a word the UD English treebanks tag as a bare verb at least 90% of the time. The table is derived by `tools/build_verb_table.py` and shipped as package data.
- `NAM104`: a command verb (`set_`, `reset_`, `clear_`, `update_`, …) that returns a value. Replaces the specified "bool under a non-predicate name", which found nothing genuine in the corpus (0 of 9).
- `NAM105`: a value verb (`get_`, `find_`, `to_`, `as_`, `format_`, …) whose body never returns a value.
- `NAM108`: a method whose name repeats its class name as a run of words.
- An allowlist: `[tool.namelint.allow]` in `pyproject.toml` maps a code to function names or `Class.method` patterns, with shell wildcards.
- `namelint init` adds an empty `[tool.namelint.allow]` table to `pyproject.toml`; `namelint init --accept-existing` fills it with every current finding, for adopting namelint on an existing codebase. `namelint allow` adds the current findings to the allowlist. Both accept `--select`/`--ignore` and paths, and rewrite only the `[tool.namelint.allow]` table.
- `--json` output includes `qualname` (`Class.method`). `Finding` has a new `owner` field.

### Fixed

- `--stats` counted nested functions, which no check reads, so every rate was understated by up to a third. The calibration table is re-measured over 71,274 functions (previously 85,368).
- `--select` and `--ignore` exit 2 on an unknown code.
- `NAM101` reported unittest's `setUp`/`tearDown` and pytest's `setup_module`-style hooks, a third of its corpus findings. Setup and teardown hooks are now exempt.
- `NAM107` suggested `iter__entry` for a private `_entry`; it now suggests `_iter_entry`.
- An allowlist entry containing a backslash or a quote was written back unescaped, which changed the pattern.

### Changed

- `NAM103` treats `check_` as a predicate prefix. A `check_` annotated `-> None` stays quiet, since it answers by raising.
- `NAM107` is opt-in: it runs only with `--select NAM107`, while it fires 17 times per thousand functions in `httpx`.
- The library API is renamed so namelint passes its own lint: `check_module` and `check_source` are now `lint_module` and `lint_source`. Each check is named `find_<what it reports>`.
- `--no-allowlist` reports every finding, allowlist or not.

## [0.1.0] - 2026-10-02

This first release claims the name on PyPI. Four of the eight specified checks are implemented; `NAM107` is on probation.

### Added

- `NAM101`: a function in a test module that contains an assertion, takes no arguments, and is not named `test*`, so pytest never collects it.
- `NAM103`: an `is_`/`has_`/`can_`/`should_`/`was_` that returns a non-bool, read from the return annotation or from an evidently non-bool return. Two findings in 85,368 corpus functions, both genuine.
- `NAM106`: a `get_` whose body reaches a disk, a socket, a subprocess or a database.
- `NAM107`: a generator whose name reads as if it returned a container.
- The `namelint` CLI: `--select`, `--ignore`, `--json`, `--stats`, `--version`. Exit 0 clean, 1 findings, 2 the tool itself failed.
- `tools/calibrate.py`: fetches the nine-project golden corpus and measures every check against it, writing a summary table, every finding as JSONL, and a seeded sample to adjudicate by hand.

### Known

- `NAM107` fires at 15.9 per thousand functions in `httpx` and 13.7 in `rich`. That rate puts the rule in question; it says nothing about those codebases. The false-positive class is the undecorated protocol generator.
- Configuration and suppression are both absent; they wait on corpus evidence about what needs suppressing.
