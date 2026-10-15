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
namelint init                          # add an empty allowlist to pyproject.toml
namelint init --accept-existing        # ...holding every current finding
namelint allow --select NAM108 src/    # accept the current findings of one check
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

All eight specified checks are implemented. Each entry gives what the check reports and what it stays quiet about, since for this kind of rule the exemptions are most of the work. What a check cannot decide on its own goes in the [allowlist](#allowlist).

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

### `NAM102`: a property named like a command

`obj.get_child` reads as an attribute at the call site and as a bound method to anyone who knows Python. A verb head promises an action the caller cannot see being taken.

```python
class Node:
    @property
    def get_unique_child(self):  # NAM102 — 'get' is predominantly a verb
        ...
```

Whether a word is a verb comes from a table derived from the Universal Dependencies English treebanks (`tools/build_verb_table.py`), never from a hand-written list. Only words used as a bare verb at least 90% of the time count, so `name`, `value`, `drive` and `handle` stay quiet. A word the treebanks do not know (`parse`, `compute`) is silence.

Expect to allowlist noun compounds: `verify_mode` and `include_dir` open with words that are nearly always verbs, yet name a mode and a directory.

### `NAM103`: a predicate that does not return a bool

`if is_ready():` reads the name, never the body. An `is_`/`has_`/`can_`/`should_`/`was_`/`check_` that hands back a string or a count is truthy for every value but one, so the empty string and the zero are the bug. The failure lands in whatever caller tested the result.

```python
def is_capturing(self) -> str | bool:  # NAM103 — annotated -> str | bool
    if self._fixture:
        return f"fixture {self._fixture.name}"
    return False
```

The check reads annotations and return shapes, and does no type inference, so an unknown return is silence:

- a return the AST cannot read, such as `return self._compute()`.
- `-> Any` or `-> object`, which put the uncertainty in the annotation.
- `-> TypeGuard[X]` and `-> TypeIs[X]`, which do return a bool; the subscript says what it proves.
- `return None`, which is how half the predicates ever written take an early exit.
- a name whose last word also names the returned type, which makes it a factory: `is_instance_schema(cls) -> IsInstanceSchema` builds an "is-instance" schema. Whole words only, so `is_valid() -> ValidationResult` keeps its finding.
- a `check_` annotated `-> None`, which answers by raising.

### `NAM104` and `NAM105`: what the verb promises about the return

A leading verb is a promise. `total = get_total()` expects a value; `reset_cache()` promises to act and answer nothing. So a value verb must return something (`NAM105`). A command verb must not (`NAM104`).

```python
def get_top_level_stats(self):  # NAM105 — no return carries a value
    for func, stats in self.stats.items():
        self.total_calls += stats.calls


def set_shape(lines, width):  # NAM104 — returns [line[:width] for ...]
    return [line[:width] for line in lines]
```

Value verbs: `get`, `find`, `compute`, `calc`, `calculate`, `count`, `lookup`, `as`, `to`, `format`. Command verbs: `set`, `reset`, `clear`, `close`, `print`, `emit`, `insert`, `append`, `show`, `stop`, `warn`, `init`, `update`, `save`. Both lists hold only verbs the corpus shows to be one-sided: `get_` returns a value in 916 of 921 public functions, `reset_` returns none in 56 of 59. Verbs that go both ways (`load_`, `create_`, `make_`, `read_`, `add_`, `run_`, `handle_`) are in neither list.

Silent on:

- private and dunder names.
- a bare one-word name such as `get` or `close`, whose contract lives in its type.
- an explicit `return None` in a query: importlib's `get_source()` returns None to mean "no source".
- a query that is a declaration (`@abstractmethod`, `@overload`, a stub body) or that ends by raising.
- in a command: `return None` as an early exit, `return self` for chaining, a bool literal reporting success, and `return super().set_cookie(...)` passing on the same command.

Expect to allowlist the copy-and-update idiom, where `options.update_width(80)` returns a changed copy on purpose, and words that are not verbs here: `close_to_zero` is an adjective, and `set_validator` validates sets.

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

### `NAM108`: a method that repeats its class name

`config.read_config()` says "config" twice; the call site already holds the class.

```python
class Config:
    def read_config(self):  # NAM108 — method of Config
        ...
```

The whole class name must appear as a run of words, so `CodeContext.update_code_context` matches and `ConfigLoader.config_path` does not.

Silent on:

- test modules and `Test*` classes.
- private methods.
- a method named exactly like its class (`Filter.filter`).
- a class where three or more methods repeat the name. That is a namespace on purpose (tkinter's `Wm.wm_title`, `Wm.wm_frame`).

This is the check that most needs the allowlist. A user name is not the same thing as a user's name, and `Style.background_style` returns a different style. Only the author knows which repeat is a slip.

## Allowlist

When a finding is a legitimate use of an ambiguous name, list the name under its code in `pyproject.toml`:

```toml
[tool.namelint.allow]
NAM104 = ["update_width", "close_to_*"]
NAM108 = ["User.user_name", "Style.*_style"]
```

An entry matches a function name or `Class.method`, with shell wildcards. It covers only the code it sits under. namelint reads the `pyproject.toml` in the current directory or its nearest parent. An unknown code or a malformed entry is an error, with exit code 2. `--json` prints each finding's `qualname`, ready to paste.

Two commands write the allowlist for you:

- `namelint init` adds an empty `[tool.namelint.allow]` table and nothing else. It refuses to run if the table already exists. With `--accept-existing` it fills the table with every current finding, which is how to adopt namelint on an existing codebase: the next run is clean, and only new code gets reported.
- `namelint allow` adds the current findings to the allowlist, keeping what is there. Narrow it with `--select`/`--ignore` and paths, and review the diff before committing.

Both lint the given paths (the current directory by default) and record each finding as `Class.method` or a bare function name.

Both rewrite only the `[tool.namelint.allow]` table, sorted, so regenerating it gives a stable diff. Every other line of `pyproject.toml` is left as it was, but comments inside that table are lost. With no `pyproject.toml` anywhere up the tree, one is created in the current directory.

There are no inline suppression comments. An allowlist keeps the project's exceptions in one reviewable place.

## Calibration

A rule that fires often on a codebase no reviewer would call badly named is a **wrong rule**. It is also no evidence about that codebase. So every check is measured against a fixed corpus of nine projects before it ships. Any check running above roughly two false positives in thirty gets a narrower detector, drops to advisory, or is cut.

```sh
uv run tools/calibrate.py                 # fetch what is missing, then measure
uv run tools/calibrate.py --only click    # one project
uv run tools/calibrate.py --no-fetch      # re-measure after changing a detector
```

It shallow-clones CPython's `Lib/`, attrs, pydantic, requests, httpx, rich, click, pytest and flask into `corpus/`, then writes `calibration/summary.md` (the table), `findings.jsonl` (every finding, so two runs can be diffed) and `sample.md` (a seeded random sample per check, with source lines, as checkboxes to adjudicate by hand). The sample is seeded on purpose: measuring a changed detector against a fresh sample measures the sample. Every row records the commit it came from, because a number with no commit behind it is a rumour.

The current run covers 85,368 functions and reports 450 findings:

| Project | NAM101 | NAM102 | NAM103 | NAM104 | NAM105 | NAM106 | NAM107 | NAM108 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cpython | 0.45 | 0.05 | 0.16 | 0.57 | 0.23 | 0.42 | 1.86 | 0.29 |
| attrs | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.87 | 0.00 |
| pydantic | 0.79 | 0.11 | 0.00 | 1.13 | 0.45 | 0.56 | 0.68 | 0.11 |
| requests | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| httpx | 0.00 | 0.00 | 0.00 | 0.88 | 0.00 | 0.88 | **15.87** | 2.65 |
| rich | 0.55 | 0.55 | 0.00 | **6.03** | 0.00 | 0.00 | **13.71** | 2.19 |
| click | 0.00 | 0.00 | 0.00 | 0.00 | 4.24 | 0.00 | **7.43** | 3.18 |
| pytest | 0.46 | 0.77 | 0.15 | 0.15 | 0.00 | 0.46 | **7.97** | 0.31 |
| flask | 0.00 | 0.00 | 0.00 | 0.00 | 0.68 | 1.37 | 0.68 | 1.37 |

The table counts findings per thousand functions, with no allowlist. rich's `NAM104` rate is its copy-and-update `ConsoleOptions` API; click's `NAM105` is its `format_help(ctx, formatter)` family, which writes into the formatter it is given. CPython is pinned to `v3.13.0`, since `main` uses syntax a 3.14 interpreter cannot parse; a run against `main` would measure the interpreter.

## As a library

`check_module(tree, path) -> list[Finding]` is also flake8's plugin contract, so a flake8 adapter needs an entry point and a wrapper, with no second copy of the checks. `checks.py` imports nothing beyond `ast` and two frozen records; the verb table reaches it through `Context`. It is a pure function of a node and a `Context`: it touches no filesystem and reads no configuration.

```python
import ast
from pathlib import Path
from namelint.visitor import check_module, check_source

for finding in check_source(
    "def get_user(u):\n    return httpx.get(u)\n", Path("x.py")
):
    print(finding.code, finding.name, finding.evidence)
```

Every `Finding` has `code`, `line`, `col`, `name`, `message`, `evidence`, and `owner` (the enclosing class, if any). The `evidence` field names the fact that produced the finding: "calls `httpx.get`" is a fact you can dispute, "performs I/O" is not.

There is no ruff plugin, because ruff has no plugin API.

## Status

**Pre-release.** All eight checks are implemented; `NAM107` is on probation, and `NAM102`, `NAM104` and `NAM108` lean on the allowlist for names only their author can read. The output format and the `NAM1xx` codes are not frozen yet.

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
