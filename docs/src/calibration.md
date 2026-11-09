# Calibration

A rule that fires often on a codebase no reviewer would call badly named is a **wrong rule**. Its findings say nothing about that codebase either. So every check is measured against a fixed corpus of nine projects before it ships. A check that runs above roughly two false positives in thirty gets a narrower detector, drops to opt-in, or is cut.

## Running it

Run these from a clone of the repository:

```sh
uv run tools/calibrate.py                 # fetch what is missing, then measure
uv run tools/calibrate.py --only click    # one project
uv run tools/calibrate.py --no-fetch      # re-measure after changing a detector
```

It shallow-clones CPython's `Lib/`, attrs, pydantic, requests, httpx, rich, click, pytest and flask into `corpus/`, then writes three files to `calibration/`:

- `summary.md`, the table below.
- `findings.jsonl`, every finding, so two runs can be diffed.
- `sample.md`, a seeded random sample per check, with source lines, as checkboxes to adjudicate by hand.

The sample is seeded on purpose: measuring a changed detector against a fresh sample measures the sample. Every row records the commit it came from.

## Current results

The current run covers 71,274 functions and reports 437 findings, every check included. The table counts findings per thousand functions, with no allowlist:

| Project | NAM101 | NAM102 | NAM103 | NAM104 | NAM105 | NAM106 | NAM107 | NAM108 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cpython | 0.33 | 0.06 | 0.19 | 0.68 | 0.27 | 0.50 | 2.22 | 0.35 |
| attrs | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.09 | 0.00 |
| pydantic | 0.98 | 0.14 | 0.00 | 1.40 | 0.56 | 0.70 | 0.84 | 0.14 |
| requests | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| httpx | 0.00 | 0.00 | 0.00 | 0.95 | 0.00 | 0.95 | **17.08** | 2.85 |
| rich | 0.59 | 0.59 | 0.00 | **6.49** | 0.00 | 0.00 | **14.75** | 2.36 |
| click | 0.00 | 0.00 | 0.00 | 0.00 | **6.18** | 0.00 | **10.82** | 4.64 |
| pytest | 0.17 | 0.84 | 0.17 | 0.17 | 0.00 | 0.50 | **8.72** | 0.34 |
| flask | 0.00 | 0.00 | 0.00 | 0.00 | 1.17 | 2.33 | 1.17 | 2.33 |

rich's `NAM104` rate comes from its copy-and-update `ConsoleOptions` API. click's `NAM105` rate comes from its `format_help(ctx, formatter)` family, which writes into the formatter it is given. `NAM107`'s rates are why it is opt-in.

CPython is pinned to `v3.13.0`, since `main` uses syntax a 3.14 interpreter can't parse.
