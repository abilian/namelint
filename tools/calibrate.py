#!/usr/bin/env python3
"""Fetch the golden corpus and measure every check against it.

The step that decides which rules ship. A rule firing often on a
codebase nobody thinks is badly named is a wrong rule, and it is no
evidence about the codebase. See `notes/02-specs.md` §6.

    uv run tools/calibrate.py                 # fetch what is missing, measure
    uv run tools/calibrate.py --only click    # one project
    uv run tools/calibrate.py --no-fetch      # measure what is already there
    uv run tools/calibrate.py --sample 30     # adjudication sample size

Writes three files under `calibration/`:

    summary.md     the table, with the commit each number came from
    findings.jsonl every finding, for counting and for diffing two runs
    sample.md      a seeded random sample per code, to adjudicate by hand

The commit of every checkout is recorded, because "measured against
pytest" is a claim, and a claim with no version behind it rots.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from namelint.checks import CODES

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
OUT = ROOT / "calibration"


@dataclass(frozen=True)
class Project:
    """One checkout, and the part of it worth scanning."""

    name: str
    url: str
    paths: tuple[str, ...] = ("",)
    why: str = ""
    ref: str = ""  # a tag or branch; empty means the default branch

    @property
    def checkout(self) -> Path:
        return CORPUS / self.name

    def targets(self) -> list[Path]:
        return [self.checkout / part for part in self.paths]


# Chosen so each rule meets a codebase built to stress it. `cpython` is
# restricted to `Lib/`, since the rest of that tree is C and build
# scaffolding.
PROJECTS = (
    Project(
        "cpython",
        "https://github.com/python/cpython",
        ("Lib",),
        "the reference for what Python naming means",
        # Pinned: `main` uses syntax a 3.14 interpreter cannot parse, so
        # measuring it measures our interpreter instead of the corpus.
        ref="v3.13.0",
    ),
    Project("attrs", "https://github.com/python-attrs/attrs", why="modern, annotated"),
    Project(
        "pydantic", "https://github.com/pydantic/pydantic", why="modern, annotated"
    ),
    Project(
        "requests", "https://github.com/psf/requests", why="NAM106 meets the HTTP verb"
    ),
    Project(
        "httpx", "https://github.com/encode/httpx", why="NAM106 meets the HTTP verb"
    ),
    Project("rich", "https://github.com/Textualize/rich", why="names are the product"),
    Project("click", "https://github.com/pallets/click", why="names are the product"),
    Project(
        "pytest", "https://github.com/pytest-dev/pytest", why="the authority on NAM101"
    ),
    Project(
        "flask", "https://github.com/pallets/flask", why="dispatch-heavy, tests handle_"
    ),
)


def main(argv: list[str] | None = None) -> int:
    """Fetch, measure, and write the three calibration files."""
    args = _parser().parse_args(argv)
    chosen = [p for p in PROJECTS if not args.only or p.name in args.only]
    if not chosen:
        print(f"error: no project matches {args.only}", file=sys.stderr)
        return 2

    OUT.mkdir(exist_ok=True)
    rows: list[dict] = []
    findings: list[dict] = []

    for project in chosen:
        if not args.no_fetch:
            _fetch(project)
        if not project.checkout.is_dir():
            print(f"{project.name}: not checked out, skipped", file=sys.stderr)
            continue
        found, functions = _measure(project)
        findings += found
        rows.append(
            {
                "project": project.name,
                "commit": _commit(project.checkout),
                "functions": functions,
                "counts": Counter(f["code"] for f in found),
            }
        )
        print(f"{project.name:10} {functions:>7} functions, {len(found):>5} findings")

    _write_findings(findings)
    _write_summary(rows)
    _write_sample(findings, size=args.sample, seed=args.seed)
    print(f"\nwrote {OUT / 'summary.md'}, findings.jsonl, sample.md")
    return 0


def _fetch(project: Project) -> None:
    """Shallow-clone the project, or leave an existing checkout alone."""
    if project.checkout.is_dir():
        return
    CORPUS.mkdir(exist_ok=True)
    print(f"{project.name:10} cloning {project.url}")
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "clone",
            "--depth",
            "1",
            "--quiet",
            *(["--branch", project.ref] if project.ref else []),
            project.url,
            str(project.checkout),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(f"{project.name}: clone failed: {result.stderr.strip()}", file=sys.stderr)


def _commit(checkout: Path) -> str:
    """The SHA a measurement came from. A number with no commit is a rumour."""
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(checkout), "rev-parse", "--short", "HEAD"],  # noqa: S607
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "unknown"


def _measure(project: Project) -> tuple[list[dict], int]:
    """Run namelint over the project, in JSON, and count its functions."""
    targets = [str(path) for path in project.targets() if path.exists()]
    if not targets:
        return [], 0
    found = [
        json.loads(line)
        for line in _namelint(["--json", *targets]).splitlines()
        if line.strip()
    ]
    functions = functions_from_stats(_namelint(["--stats", *targets]))
    for record in found:
        record["project"] = project.name
        record["path"] = str(Path(record["path"]).relative_to(project.checkout))
    return found, functions


# Every check, opt-in ones included: calibration is what decides whether
# a check on probation can become a default.
SELECT_ALL = [option for code in CODES for option in ("--select", code)]


def _namelint(args: list[str]) -> str:
    """namelint's stdout, with no allowlist: the corpus is measured raw.

    Exit 1 only means findings. Anything else is namelint failing, and a
    failure recorded as "no findings" would read as a perfect score.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "namelint", "--no-allowlist", *SELECT_ALL, *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode not in {0, 1}:
        raise CalibrationError(args, result.stderr)
    return result.stdout


class CalibrationError(Exception):
    """namelint failed on a corpus project, so there is nothing to measure."""

    def __init__(self, args: list[str], stderr: str) -> None:
        super().__init__(f"namelint {' '.join(args)} failed:\n{stderr}")


def functions_from_stats(stats: str) -> int:
    for line in stats.splitlines():
        if line.startswith("functions scanned:"):
            return int(line.split(":")[1])
    raise CalibrationError(["--stats"], f"no 'functions scanned' line in:\n{stats}")


def _write_findings(findings: list[dict]) -> None:
    (OUT / "findings.jsonl").write_text(
        "\n".join(json.dumps(f, ensure_ascii=False) for f in findings) + "\n",
        encoding="utf-8",
    )


def _write_summary(rows: list[dict]) -> None:
    """The table, per thousand functions so projects are comparable."""
    codes = sorted({code for row in rows for code in row["counts"]})
    header = "| Project | Commit | Functions | " + " | ".join(codes) + " |"
    rule = "|---|---|---:|" + "---:|" * len(codes)
    lines = [
        "# Calibration",
        "",
        "Findings per thousand functions, with the raw count in brackets.",
        "**A rule firing often here is a wrong rule, and no evidence about these codebases.**",  # noqa: E501
        "",
        header,
        rule,
    ]
    for row in rows:
        cells = []
        for code in codes:
            count = row["counts"].get(code, 0)
            rate = count / row["functions"] * 1000 if row["functions"] else 0.0
            cells.append(f"{rate:.2f} ({count})")
        lines.append(
            f"| {row['project']} | `{row['commit']}` | {row['functions']} | "
            + " | ".join(cells)
            + " |"
        )
    totals = Counter()
    for row in rows:
        totals.update(row["counts"])
    scanned = sum(row["functions"] for row in rows)
    lines += ["", f"Total: {scanned} functions, {sum(totals.values())} findings."]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sample(findings: list[dict], *, size: int, seed: int) -> None:
    """A seeded sample per code, with the source line, for hand adjudication.

    Seeded so a later run adjudicates the same cases. Measuring a changed
    detector against a fresh sample measures the sample.
    """
    rng = random.Random(seed)  # noqa: S311 — sampling, not secrets
    by_code: dict[str, list[dict]] = {}
    for finding in findings:
        by_code.setdefault(finding["code"], []).append(finding)

    lines = [
        "# Adjudication sample",
        "",
        f"Seed {seed}, up to {size} per code. Mark each `ok` (a real finding) or",
        "`fp` (a false positive). A code above roughly two false positives in",
        "thirty gets a narrower detector, drops to advisory, or is cut.",
        "",
    ]
    for code in sorted(by_code):
        population = by_code[code]
        picked = rng.sample(population, min(size, len(population)))
        lines += [f"## {code} ({len(population)} findings, {len(picked)} sampled)", ""]
        ordered = sorted(picked, key=lambda f: (f["project"], f["path"], f["line"]))
        for finding in ordered:
            source = _source_line(finding)
            lines.append(
                f"- [ ] `{finding['project']}/{finding['path']}:{finding['line']}` "
                f"`{finding['name']}` — {finding['evidence']}"
            )
            if source:
                lines.append(f"      `{source}`")
        lines.append("")
    (OUT / "sample.md").write_text(
        "\n".join(lines).rstrip("\n") + "\n", encoding="utf-8"
    )


def _source_line(finding: dict) -> str:
    path = CORPUS / finding["project"] / finding["path"]
    try:
        text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return text[finding["line"] - 1].strip()[:110]
    except (OSError, IndexError):
        return ""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calibrate", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--only", action="append", default=[], metavar="NAME")
    parser.add_argument("--no-fetch", action="store_true", help="measure what is there")
    parser.add_argument("--sample", type=int, default=30, metavar="N")
    parser.add_argument("--seed", type=int, default=0, metavar="N")
    return parser


if __name__ == "__main__":
    sys.exit(main())
