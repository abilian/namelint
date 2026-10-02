# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-02

First release, to claim the name. Pre-release in substance: three of the eight specified checks, one of them on probation.

### Added

- `NAM101`: a function in a test module that asserts, takes no arguments, and is not named `test*`, so pytest never collects it.
- `NAM106`: a `get_` whose body reaches a disk, a socket, a subprocess or a database.
- `NAM107`: a generator whose name reads as if it returned a container.
- The `namelint` CLI: `--select`, `--ignore`, `--json`, `--stats`, `--version`. Exit 0 clean, 1 findings, 2 the tool itself failed.
- `tools/calibrate.py`: fetches the nine-project golden corpus and measures every check against it, writing a summary table, every finding as JSONL, and a seeded sample to adjudicate by hand.

### Known

- `NAM107` fires at 15.9 per thousand functions in `httpx` and 13.7 in `rich`, which is a rule in question rather than a result about those codebases. The false-positive class is the undecorated protocol generator.
- No configuration file and no suppression mechanism yet; both wait on corpus evidence about what needs suppressing.
