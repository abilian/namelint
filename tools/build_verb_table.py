#!/usr/bin/env python3
"""Derive `src/namelint/data/verb_pos.json` from the UD English treebanks.

NAM102 needs to know whether a property name's head reads as a command.
Lexicon membership answers the wrong question: in WordNet `name`, `file`
and `value` are all verbs. Dominance is the question (notes/02-specs.md
§8.2), so this counts, per word form, how often the treebanks tag it as
a base-form verb.

Keyed by form, not lemma, on purpose. `closed` and `cached` are verbs by
lemma, yet as a property name they are participles used as adjectives,
which is exactly the naming the check must leave alone. Only `VB` and
`VBP` (the bare, imperative-shaped form) count as verb uses.

Run with `uv run tools/build_verb_table.py`. The release is pinned, so
the table is reproducible and its provenance is recorded inside it.
"""

from __future__ import annotations

import json
import urllib.request
from collections import Counter
from pathlib import Path

RELEASE = "r2.14"
TREEBANKS = {
    "UD_English-EWT": "en_ewt-ud",
    "UD_English-GUM": "en_gum-ud",
}
SPLITS = ("train", "dev", "test")
BASE_FORM_TAGS = frozenset({"VB", "VBP"})

# A form seen fewer times than this is unknown, and unknown is silence.
MIN_OCCURRENCES = 5

OUT = Path(__file__).parent.parent / "src" / "namelint" / "data" / "verb_pos.json"


def main() -> None:
    total: Counter[str] = Counter()
    verb: Counter[str] = Counter()
    for repo, prefix in TREEBANKS.items():
        for split in SPLITS:
            url = (
                "https://raw.githubusercontent.com/UniversalDependencies/"
                f"{repo}/{RELEASE}/{prefix}-{split}.conllu"
            )
            print(f"reading {url}")
            with urllib.request.urlopen(url) as response:  # noqa: S310 — fixed https URL
                _count(response.read().decode("utf-8"), total, verb)

    forms = {
        form: [verb[form], count]
        for form, count in sorted(total.items())
        if count >= MIN_OCCURRENCES and verb[form] and form.isalpha()
    }
    table = {
        "source": [f"{repo} {RELEASE}" for repo in TREEBANKS],
        "counts": "form -> [base-form verb uses (VB/VBP), all uses]",
        "forms": forms,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(table, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"wrote {len(forms)} forms to {OUT}")


def _count(conllu: str, total: Counter[str], verb: Counter[str]) -> None:
    for line in conllu.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if not cols[0].isdigit():  # multiword ranges `1-2` and empty nodes `1.1`
            continue
        form = cols[1].lower()
        total[form] += 1
        if cols[3] == "VERB" and cols[4] in BASE_FORM_TAGS:
            verb[form] += 1


if __name__ == "__main__":
    main()
