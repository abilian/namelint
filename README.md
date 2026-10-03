# namelint

Reports where a Python function's **name contradicts its body**.

`ruff` already knows that `getUserName` is not `snake_case`. Nothing knows that `get_user` opens a socket, that `collect_entry` is a generator no caller can iterate twice, or that `check_user_is_valid` sits in a test module making claims pytest will never collect. That gap is this tool's subject. Every check needs the AST; none is a grep over identifiers.

It holds no opinion about vocabulary. "Too generic", "too long", "prefer a domain term" belong in a style guide and in code review. namelint reports only that a name and the code under it disagree, naming the fact that made them disagree, so the fact is what you argue with.

## Install

```sh
uv tool install namelint     # on PATH, globally
uvx namelint src/            # or without installing anything
pip install namelint
```

No runtime dependencies. That is a constraint the project accepted on purpose: a linter you hesitate to add because of what it drags in never gets added. Python 3.12 or newer.

## Use

```sh
namelint src/                          # lint a tree
namelint src/app/users.py              # or one file
namelint --select NAM106 src/          # one check only (repeatable)
namelint --ignore NAM107 src/          # everything but one (repeatable)
namelint --json src/                   # one JSON object per line
namelint --stats src/                  # counts per check, with a rate
```

Output is the one line every editor and CI annotator already parses:

```
src/app/users.py:42:5: NAM106 get_user performs I/O (calls httpx.get); get_ promises a cheap lookup, use fetch_, load_ or read_
```

Exit codes: **0** clean, **1** findings, **2** namelint itself failed. A file it cannot parse is reported on stderr and skipped: one Python 2 file in a vendored tree must not end a run over 80,000 functions.

`--stats` serves calibration. It reports per thousand functions, so two codebases of different sizes can be compared:

```
$ namelint --stats ~/src/cpython/Lib
functions scanned: 61820
  NAM101      28     0.45 per 1000
  NAM106      26     0.42 per 1000
  NAM107     115     1.86 per 1000
```

## The checks

Three of the eight specified checks are implemented. Each entry gives what the check reports and what it stays quiet about, since for this kind of rule the exemptions are most of the work.

### `NAM101`: a test that will never run

Reports a function in a test module that contains an assertion, takes no arguments, and is not named `test*`. pytest collects `test*` and nothing else, so the function reports nothing. A suite that stays green over it says nothing about the code it claims to cover.

```python
# tests/test_users.py
def check_user_is_valid():  # NAM101 — pytest will not collect this
    assert build().ok
```

Silent on:

- anything outside a test module. A test module is a `test_*.py`, a `*_test.py`, or any file under a `tests/` directory.
- a decorated function, since that is the shape of a fixture.
- a `_`-prefixed helper. A leading underscore already says "not collected".
- a helper that takes the thing it checks; arity is the discriminator, so `assert_ok(response)` stays quiet.

A `with pytest.raises(...)` counts as an assertion.

### `NAM106`: a `get_` that performs I/O

`get` is a contract in Python: `dict.get`, `getattr`, `os.environ.get` are all cheap and total. A `get_` that opens a socket breaks the promise its caller read.

```python
def get_user(uid):  # NAM106 — calls httpx.get
    return httpx.get(f"/u/{uid}").json()
```

It fires on `open`, `Path.read_*`/`write_*`, `urlopen`, DBAPI `execute`/`fetchone`/`fetchall`, socket `recv`/`send`, and anything rooted at `requests`, `httpx`, `urllib`, `socket`, `subprocess` or `aiohttp`. The message suggests `fetch_`, `load_` or `read_`. `dict.get` and `getattr` are never the evidence.

### `NAM107`: a generator under a non-lazy name

A caller who believes they hold a list and actually hold a one-shot iterator writes a bug that surfaces two loops later, far from this function.

```python
def collect_stale_entry(root):  # NAM107 — contains yield
    for path in root.iterdir():
        if stale(path):
            yield path
```

Silent on:

- a plural final word: `items`, `values`, `user_records`.
- a lazy prefix (`iter_`, `walk_`, `gen_`, `generate_`, `stream_`, `scan_`, `traverse_`, `produce_`, `yield_`, `enumerate_`, `chunk_`), checked after any leading underscores.
- dunders.
- a `yield` that belongs to a protocol: a pytest fixture, a `@contextmanager`, an `@asynccontextmanager`, a pluggy `@hookimpl` wrapper. In all four the noun name is correct on purpose (`db_session`, `temp_config`, `client`).

**This check is the one currently in question.** It fires at 15.9 per thousand functions in `httpx` and 13.7 in `rich`, far outside what a well-named codebase should produce. The known false-positive class is the undecorated protocol generator: an ABC method where `yield request` *is* the interface. Expect a narrower detector, or a drop to advisory, before 1.0.

### Still to come

| Code | Reports |
|---|---|
| `NAM102` | a `@property` whose name opens with a verb |
| `NAM103` | an `is_`/`has_`/`can_` that does not return a bool |
| `NAM104` | a bool return under a non-predicate name |
| `NAM105` | a query-shaped name that returns `None` on every path |
| `NAM108` | a method repeating its class name |

The three that depend on reading return types share machinery and are being built together. `NAM108` comes last, because it is the one most likely to be cut.

## Calibration

A rule that fires often on a codebase no reviewer would call badly named is a **wrong rule**. It is also no evidence about that codebase. So every check is measured against a fixed corpus of nine projects before it ships. Any check running above roughly two false positives in thirty gets a narrower detector, drops to advisory, or is cut.

```sh
uv run tools/calibrate.py                 # fetch what is missing, then measure
uv run tools/calibrate.py --only click    # one project
uv run tools/calibrate.py --no-fetch      # re-measure after changing a detector
```

It shallow-clones CPython's `Lib/`, attrs, pydantic, requests, httpx, rich, click, pytest and flask into `corpus/`, then writes `calibration/summary.md` (the table), `findings.jsonl` (every finding, so two runs can be diffed) and `sample.md` (a seeded random sample per check, with source lines, as checkboxes to adjudicate by hand). The sample is seeded on purpose: measuring a changed detector against a fresh sample measures the sample. Every row records the commit it came from, because a number with no commit behind it is a rumour.

The current run covers 85,368 functions and reports 308 findings:

| Project | NAM101 | NAM106 | NAM107 |
|---|---:|---:|---:|
| cpython `Lib/` | 0.45 | 0.42 | 1.86 |
| attrs | 0.00 | 0.00 | 0.87 |
| pydantic | 0.79 | 0.56 | 0.68 |
| requests | 0.00 | 0.00 | 0.00 |
| httpx | 0.00 | 0.88 | **15.87** |
| rich | 0.55 | 0.00 | **13.71** |
| click | 0.00 | 0.00 | **7.43** |
| pytest | 0.46 | 0.46 | **7.97** |
| flask | 0.00 | 1.37 | 0.68 |

Findings per thousand functions. CPython is pinned to `v3.13.0`, since `main` uses syntax a 3.14 interpreter cannot parse; a run against `main` would measure the interpreter.

## As a library

`check_module(tree, path) -> list[Finding]` is also flake8's plugin contract, so a flake8 adapter needs an entry point and a wrapper, with no second copy of the checks. `checks.py` imports nothing beyond `ast` and two frozen records. It is a pure function of a node and a `Context`: it touches no filesystem and reads no configuration.

```python
import ast
from pathlib import Path
from namelint.visitor import check_module, check_source

for finding in check_source(
    "def get_user(u):\n    return httpx.get(u)\n", Path("x.py")
):
    print(finding.code, finding.name, finding.evidence)
```

Every `Finding` has `code`, `line`, `col`, `name`, `message` and `evidence`. The `evidence` field names the fact that produced the finding: "calls `httpx.get`" is a fact you can dispute, "performs I/O" is not.

There is no ruff plugin, because ruff has no plugin API.

## Status

**0.1.0, pre-release.** Three of the eight checks are implemented; one of them is on probation. The output format and the `NAM1xx` codes are not frozen yet. Configuration and suppression are both absent, pending corpus evidence about what needs suppressing. `requests`, where `get` is the HTTP verb, already shows the first exception to be module-scoped.

## Development

```sh
uv sync
make test          # pytest
make lint          # ruff check, ruff format --check, ty, pyrefly, mypy
nox -s tests       # against 3.12, 3.13 and 3.14
```

The design lives in two notes files:

- `notes/02-specs.md`: the reasoning behind each rule, the corpus design, the open questions.
- `notes/01-background.md`: where the rules came from, and which candidates were dropped.

A check is finished when it has been run over the corpus and adjudicated, with the sample committed beside it. Green unit tests are the step before that.

## Licence

namelint is distributed under the Apache License 2.0, copyright 2026 Abilian SAS.
