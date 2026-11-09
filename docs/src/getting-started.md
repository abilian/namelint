# Getting Started

This page takes an existing project from its first namelint run to a clean one that reports only new code.

## Run it

Run this from the project's root:

```sh
namelint check
```

With no path, `check` lints the current directory, skipping what git ignores and the usual tool directories (`.venv`, `build`, `node_modules` and the like). Each finding names the function, the check, and the fact that triggered it:

```
src/app/users.py
  42:5   NAM106  get_user performs I/O (calls httpx.get)
```

To read what a check means and how to fix its findings:

```sh
namelint explain NAM106
namelint explain NAM106 --level junior    # or senior (the default), or expert
namelint explain                          # the conventions behind all the checks
```

## Fix or accept each finding

Each finding has one of three outcomes:

- **The name is wrong.** Rename the function to say what it does: `get_user` becomes `fetch_user`.
- **The body is wrong.** Change it to keep the name's promise: the `set_` stops returning a value its callers ignore.
- **namelint misread the name.** `close_to_zero` doesn't close anything. Add the name to the [allowlist](allowlist.md).

## Adopt it on a large codebase

A codebase with years of history can report hundreds of findings. To start clean and report only new code:

```sh
namelint init --accept-existing
```

This adds a `[tool.namelint]` table to `pyproject.toml`, with every setting at its default, and fills `[tool.namelint.allow]` with every current finding. The next run is clean. Review the allowlist over time, fix the names you can, and shrink it with `namelint allow --prune`.

To start with an empty allowlist instead, run `namelint init` without the flag.

## Keep it clean

Add namelint to [CI or pre-commit](ci.md) so new findings get caught in review.
