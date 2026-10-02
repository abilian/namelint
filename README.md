# namelint

Reports where a Python function's **name contradicts its body**.

`ruff` already knows that `getUserName` is not `snake_case`. Nothing knows that `get_user` opens a socket, that `cleanup_files` is a generator nobody will iterate twice, or that `check_user_is_valid` sits in a test module asserting things pytest will never collect. That gap is what this tool is for: every check needs the AST, and none of them is a grep over identifiers.

It holds **no opinion about vocabulary**. "Too generic", "too long", "prefer a domain term" belong in a style guide and a code review. namelint only reports that a name and the code under it disagree, and it names the fact that made it disagree, so you can argue with that fact rather than with the rule.

## Install

```sh
uv tool install namelint     # on PATH, globally
uvx namelint src/            # or without installing anything
pip install namelint
```

No runtime dependencies, and that is a constraint rather than an accident: a linter you hesitate to add to a project because of what it drags in is a linter that does not get added. Python 3.12 or newer.

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

Exit codes: **0** clean, **1** findings, **2** namelint itself failed. A file it cannot parse is reported on stderr and skipped — one Python 2 file in a vendored tree must not end a run over 80,000 functions.

`--stats` exists for calibration rather than for daily use, and reports per thousand functions so that two codebases of different sizes can be compared:

```
$ namelint --stats ~/src/cpython/Lib
functions scanned: 61820
  NAM101      28     0.45 per 1000
  NAM106      26     0.42 per 1000
  NAM107     115     1.86 per 1000
```

## The checks

Three of the eight specified checks are implemented. Each is listed with what it reports **and what it deliberately stays quiet about**, because for this kind of rule the exemptions are most of the work.

### `NAM101` — a test that will never run

A function in a test module that contains an assertion, takes no arguments, and is not named `test*`. pytest collects `test*` and nothing else, so this function reports nothing, and a suite that stays green over it is telling you nothing about the code it claims to cover.

```python
# tests/test_users.py
def check_user_is_valid():  # NAM101 — pytest will not collect this
    assert build().ok
```

Silent on: anything under `src/` (a test module is a `test_*.py`, a `*_test.py`, or any file under a `tests/` directory); a decorated function, which is what a fixture looks like; a `_`-prefixed helper, since a leading underscore says "not collected" as plainly as a name can; and a helper that takes the thing it checks — `assert_ok(response)` is a helper, and arity is the discriminator. A `with pytest.raises(...)` counts as an assertion.

### `NAM106` — a `get_` that performs I/O

`get` is a contract in Python rather than a lazy choice: `dict.get`, `getattr`, `os.environ.get` are all cheap and total. A `get_` that opens a socket breaks the promise its caller read.

```python
def get_user(uid):  # NAM106 — calls httpx.get
    return httpx.get(f"/u/{uid}").json()
```

Reported on `open`, `Path.read_*`/`write_*`, `urlopen`, DBAPI `execute`/`fetchone`/`fetchall`, socket `recv`/`send`, and anything rooted at `requests`, `httpx`, `urllib`, `socket`, `subprocess` or `aiohttp`. The suggestion is `fetch_`, `load_` or `read_`. `dict.get` and `getattr` are never the evidence.

### `NAM107` — a generator under a non-lazy name

A caller who believes they hold a list and actually hold a one-shot iterator writes a bug that surfaces two loops later, far from this function.

```python
def collect_stale_entry(root):  # NAM107 — contains yield
    for path in root.iterdir():
        if stale(path):
            yield path
```

Silent on: a plural final word (`items`, `values`, `user_records`); a lazy prefix (`iter_`, `walk_`, `gen_`, `generate_`, `stream_`, `scan_`, `traverse_`, `produce_`, `yield_`, `enumerate_`, `chunk_`), checked after any leading underscores; dunders; and a `yield` that is a *protocol* rather than iteration — a pytest fixture, a `@contextmanager`, an `@asynccontextmanager`, a pluggy `@hookimpl` wrapper. In all four the noun name is correct on purpose (`db_session`, `temp_config`, `client`).

**This check is the one currently in question.** It fires at 15.9 per thousand functions in `httpx` and 13.7 in `rich`, which is far outside what a well-named codebase should produce, and the known false-positive class is the undecorated protocol generator: an ABC method where `yield request` *is* the interface. Expect it to get a narrower detector or to drop to advisory before 1.0.

### Still to come

`NAM102` a `@property` whose name opens with a verb · `NAM103` an `is_`/`has_`/`can_` that does not return a bool · `NAM104` a bool return under a non-predicate name · `NAM105` a query-shaped name that returns `None` on every path · `NAM108` a method repeating its class name. The three that depend on reading return types share machinery and are being built together; `NAM108` is last because it is the one most likely to be cut.

## Calibration

A rule firing often on a codebase nobody thinks is badly named is a **wrong rule**, and it is no evidence at all about that codebase. So every check is measured against a fixed corpus of nine projects before it is allowed to ship, and a check running above roughly two false positives in thirty gets a narrower detector, drops to advisory, or is cut.

```sh
uv run tools/calibrate.py                 # fetch what is missing, then measure
uv run tools/calibrate.py --only click    # one project
uv run tools/calibrate.py --no-fetch      # re-measure after changing a detector
```

It shallow-clones CPython's `Lib/`, attrs, pydantic, requests, httpx, rich, click, pytest and flask into `corpus/`, then writes `calibration/summary.md` (the table), `findings.jsonl` (every finding, so two runs can be diffed) and `sample.md` (a seeded random sample per check, with source lines, as checkboxes to adjudicate by hand). The sample is seeded deliberately: measuring a changed detector against a fresh sample measures the sample. Every row records the commit it came from, because a number with no commit behind it is a rumour.

The current run — 85,368 functions, 308 findings:

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

Findings per thousand functions. CPython is pinned to `v3.13.0`, since `main` uses syntax a 3.14 interpreter cannot parse and measuring it would measure the interpreter instead of the corpus.

## As a library

`check_module(tree, path) -> list[Finding]` is also flake8's plugin contract, so a flake8 adapter is an entry point and a wrapper rather than a second implementation. `checks.py` imports nothing but `ast` and two frozen records, and is a pure function of a node and a `Context` — no filesystem, no configuration.

```python
import ast
from pathlib import Path
from namelint.visitor import check_module, check_source

for finding in check_source(
    "def get_user(u):\n    return httpx.get(u)\n", Path("x.py")
):
    print(finding.code, finding.name, finding.evidence)
```

Every `Finding` carries `code`, `line`, `col`, `name`, `message` and `evidence`. `evidence` names the fact that produced the finding: "calls `httpx.get`" is arguable, "performs I/O" is not.

There is no ruff plugin because ruff has no plugin API.

## Status

**0.1.0, pre-release.** Three checks of eight, one of which is on probation. The output format and the `NAM1xx` codes are not frozen yet. There is no configuration file and no suppression mechanism; both are waiting on evidence from the corpus about what actually needs suppressing — `requests`, where `get` is the HTTP verb, already shows that the first exception needed is module-scoped.

## Development

```sh
uv sync
make test          # pytest
make lint          # ruff check, ruff format --check, ty, pyrefly, mypy
nox -s tests       # against 3.12, 3.13 and 3.14
```

Reasoning behind each rule, the corpus design and the open questions: `notes/02-specs.md`. Where the rules came from, and what was rejected: `notes/01-background.md`.

A new check is not finished when it passes its tests. It is finished when it has been run over the corpus and adjudicated, and the sample is in the commit.

## Licence

Apache 2.0. Copyright 2026 Abilian SAS.
