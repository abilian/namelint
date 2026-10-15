# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `NAM102`: a `@property` whose name opens with a word the UD English treebanks tag as a bare verb at least 90% of the time. The table is derived by `tools/build_verb_table.py` and shipped as package data.
- `NAM104`: a command verb (`set_`, `reset_`, `clear_`, `update_`, …) that returns a value. Replaces the specified "bool under a non-predicate name", which found nothing genuine in the corpus (0 of 9).
- `NAM105`: a value verb (`get_`, `find_`, `to_`, `as_`, `format_`, …) whose body never returns a value.
- `NAM108`: a method whose name repeats its class name as a run of words.
- An allowlist: `[tool.namelint.allow]` in `pyproject.toml` maps a code to function names or `Class.method` patterns, with shell wildcards.
- `namelint init` adds an empty `[tool.namelint.allow]` table to `pyproject.toml`; `namelint init --accept-existing` fills it with every current finding, for adopting namelint on an existing codebase. `namelint allow` adds the current findings to the allowlist. Both accept `--select`/`--ignore` and paths, and rewrite only the `[tool.namelint.allow]` table.
- `--json` output carries `qualname` (`Class.method`), and `Finding` carries `owner`.

### Changed

- `NAM103` treats `check_` as a predicate prefix. A `check_` annotated `-> None` stays quiet, since it answers by raising.

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
