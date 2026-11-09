# Running Checks

```sh
namelint check                                # lint the current directory
namelint check src/app/users.py               # or one file
namelint check --select NAM106 src/           # one check only (repeatable)
namelint check --ignore NAM108 src/           # everything but one (repeatable)
namelint check --stats src/                   # counts per check, with a rate
namelint check --no-allowlist src/            # report everything, allowlist or not
namelint check --exit-zero src/               # report findings, exit 0 anyway
namelint check --force-exclude FILE...        # apply exclude to named files too
namelint check --show-settings                # the settings in force, and their file
namelint check --explain src/                 # then explain each check that fired
```

Without `--select`, every check runs except the opt-in `NAM107`. Run `namelint check --help` for the full list of options.

## Output formats

`--output-format` chooses how findings are printed. It can also be set in the [configuration](configuration.md).

### `grouped` (the default)

Each file is named once, with its findings below it:

```
src/app/users.py
  42:5   NAM106  get_user performs I/O (calls httpx.get)
  108:1  NAM104  set_env_vars reads as a command but returns (count, skipped)

2 findings in 1 file
```

### `full`

The grouped output, with what to do about each finding on the line below it:

```
src/app/users.py
  42:5   NAM106  get_user performs I/O (calls httpx.get)
                 hint: get_ promises a cheap lookup, use fetch_, load_ or read_
```

### `concise`

The one line per finding that editors and CI annotators already parse, hint included:

```
src/app/users.py:42:5: NAM106 get_user performs I/O (calls httpx.get); get_ promises a cheap lookup, use fetch_, load_ or read_
```

### `json`

Each finding is one JSON object on its own line. It includes the finding's `qualname`, ready to paste into the allowlist, its `evidence` and its `hint`.

### `github`

This format prints GitHub Actions annotations, which show up on the pull request's diff. See [CI and pre-commit](ci.md).

## Explanations

`--explain` follows the report with an explanation of each check that fired, once per check, in code order. It is the same text `namelint explain CODE` prints:

```
$ namelint check --explain --level junior src/
src/app/users.py
  42:5   NAM106  get_user performs I/O (calls httpx.get)

1 finding in 1 file

NAM106: a get_ that performs I/O

In Python, `get` means a cheap lookup: `dict.get`, `getattr`, `os.environ.get`. ...
```

`--level` sets the depth: `junior` for what the convention is, with an example; `senior` (the default) for why it matters and when to break it; `expert` for how the check decides and where it goes wrong. `--level` without `--explain` is an error, and so is `--explain` with the `json` or `github` format, since explanations would break their output.

## Statistics

`--stats` counts findings per check and reports a rate per thousand functions, so two codebases of different sizes can be compared. Nested functions are not checked, so they are not counted either:

```
$ namelint check --stats ~/src/cpython/Lib
functions scanned: 51726
  NAM101      17     0.33 per 1000
  NAM102       3     0.06 per 1000
  NAM103      10     0.19 per 1000
  NAM104      35     0.68 per 1000
  NAM105      14     0.27 per 1000
  NAM106      26     0.50 per 1000
  NAM108      18     0.35 per 1000
```

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | no findings |
| 1 | findings (unless `--exit-zero`) |
| 2 | namelint itself failed: a bad option, an unknown code, an invalid configuration |

A file namelint can't parse is reported on stderr and skipped. One Python 2 file in a vendored tree must not end a run over 80,000 functions.
