# Allowlist

Some findings are correct about the code and still wrong about the name. `close_to_zero` doesn't close anything, and `User.user_name` is a user's name. Only the author can tell, so these names go in the allowlist, under their code, in `pyproject.toml`:

```toml
[tool.namelint.allow]
NAM104 = ["update_width", "close_to_*"]
NAM108 = ["User.user_name", "Style.*_style"]
```

An entry matches a function name or `Class.method`, with shell wildcards. It covers only the code it sits under. An unknown code or a malformed entry is an error, with exit code 2. `--output-format json` prints each finding's `qualname`, ready to paste.

There are no inline suppression comments. An allowlist keeps the project's exceptions in one file a reviewer can read.

## Writing it with commands

`namelint init`
:   Adds a `[tool.namelint]` table with every setting at its default, and an empty `[tool.namelint.allow]`. It refuses to run if namelint is already configured. With `--accept-existing`, it fills the allowlist with every current finding: the next run is clean, and only new code gets reported.

`namelint allow`
:   Adds the current findings to the allowlist and keeps what is there. Narrow it with `--select`, `--ignore` and paths, and review the diff before committing. With `--prune`, it also removes the entries that no longer match any finding, so the allowlist shrinks as names get fixed.

Both lint the given paths (the current directory by default) and record each finding as `Class.method` or a bare function name.

!!! note "Prune over the whole project"
    Run `--prune` over the whole project. An entry for code outside the given paths looks unused and gets removed. Entries for checks that didn't run are kept.

Both commands rewrite only the `[tool.namelint.allow]` table, sorted, so regenerating it gives a stable diff. Every other line of `pyproject.toml` stays as it was, but comments inside that table are lost. With no `pyproject.toml` anywhere up the tree, one is created in the current directory.
