"""The verb-dominant word forms NAM102 reads, loaded from package data.

`data/verb_pos.json` is derived by `tools/build_verb_table.py` from the
UD English treebanks. This module applies the threshold and hands the
result to `Context`, so `checks.py` never touches a file.
"""

from __future__ import annotations

import json
from importlib.resources import files

# A head counts as a verb when at least this share of its treebank uses
# are base-form verbs. At 0.5 the corpus flagged `drive`, `stem`,
# `handle` and `start`, all ordinary nouns; 0.9 keeps only words that
# are almost never anything else (`get`, `raise`, `write`, `include`).
THRESHOLD = 0.9


def load_verbs(threshold: float = THRESHOLD) -> frozenset[str]:
    """Forms whose base-form verb share reaches `threshold`."""
    table = json.loads(files("namelint").joinpath("data/verb_pos.json").read_text())
    return frozenset(
        form
        for form, (verb, total) in table["forms"].items()
        if verb / total >= threshold
    )


VERBS = load_verbs()
