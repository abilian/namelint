# namelint

namelint reports where a Python function's **name contradicts its body**.

`ruff` already knows that `getUserName` is not `snake_case`. Nothing knows that `get_user` opens a socket, that `collect_entry` is a generator no caller can iterate twice, or that `check_user_is_valid` sits in a test module where pytest will never collect it. namelint covers that gap. Every check reads the AST, and none is a search over identifiers.

```
$ namelint check src/
src/app/users.py
  42:5   NAM106  get_user performs I/O (calls httpx.get)
  108:1  NAM104  set_env_vars reads as a command but returns (count, skipped)

2 findings in 1 file
```

## What it checks, and what it doesn't

A function's name is a promise to the reader who calls it. namelint checks eight promises that Python code makes all the time:

| Code | Reports |
|---|---|
| [`NAM101`](checks/NAM101.md) | a function in a test module that holds an assertion, but that pytest will never collect |
| [`NAM102`](checks/NAM102.md) | a property whose name starts with a verb |
| [`NAM103`](checks/NAM103.md) | an `is_`/`has_`/`can_` predicate that returns something other than a bool |
| [`NAM104`](checks/NAM104.md) | a command (`set_`, `reset_`, `save_`) that returns a value |
| [`NAM105`](checks/NAM105.md) | a query (`get_`, `find_`, `to_`) that returns nothing |
| [`NAM106`](checks/NAM106.md) | a `get_` that reads a file, calls the network or runs a process |
| [`NAM107`](checks/NAM107.md) | a generator with a name that sounds like a list (opt-in) |
| [`NAM108`](checks/NAM108.md) | a method that repeats its class name |

It holds no opinion about vocabulary. "Too generic", "too long" and "prefer a domain term" belong in a style guide and in code review. namelint reports only that a name and the code under it disagree, and names the fact that made them disagree, so that fact is what you argue with.

## Install

```sh
uv tool install namelint     # on PATH, globally
uvx namelint check src/      # or without installing anything
pip install namelint
```

namelint needs Python 3.12 or newer. Its one runtime dependency is [Cyclopts](https://cyclopts.readthedocs.io/), for the command line. The checks themselves import nothing beyond `ast`.

## Next

- [Getting Started](getting-started.md) takes a project from its first run to a clean one.
- [The Conventions](checks/conventions.md) explains the promises behind the checks.

!!! warning "Pre-release"
    namelint is alpha software. The output formats and the `NAM1xx` codes may still change.
