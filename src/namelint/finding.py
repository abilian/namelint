"""What a check reports, and the context it needs to decide.

Both records are frozen and carry no behaviour. `checks.py` is a pure
function of an AST node and a `Context`, which is what keeps it free of
the filesystem and of every import beyond `ast`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """One contradiction between a name and the body under it.

    `evidence` names the fact that produced the finding, so a reader can
    disagree with that specific fact rather than with the rule. A
    `NAM106` that says "calls httpx.get" can be argued with; one that
    says "performs I/O" cannot.
    """

    code: str
    line: int
    col: int
    name: str
    message: str
    evidence: str = ""

    def rendered(self, path: str) -> str:
        """Render the one-line form every editor already parses."""
        return f"{path}:{self.line}:{self.col}: {self.code} {self.message}"


@dataclass(frozen=True)
class Context:
    """What a check needs to know that the node itself cannot say.

    Computed once by the visitor. Keeping it here, rather than handing
    checks a `Path`, is what lets `checks.py` import nothing but `ast`.
    """

    is_test_module: bool = False
    class_name: str | None = None
