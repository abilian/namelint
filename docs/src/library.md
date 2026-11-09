# As a Library

```python
from pathlib import Path

from namelint.visitor import lint_source

source = "def get_user(u):\n    return httpx.get(u)\n"
for finding in lint_source(source, Path("x.py")):
    print(finding.code, finding.name, finding.evidence)
```

`lint_module(tree, path) -> list[Finding]` takes a parsed `ast.Module`. Its signature is flake8's plugin contract on purpose, so a flake8 adapter would need an entry point and a wrapper, with no second copy of the checks.

## Findings

Every `Finding` is a frozen dataclass with these fields:

| Field | Holds |
|---|---|
| `code` | the check, such as `NAM106` |
| `line`, `col` | where the function is defined |
| `name` | the function's name |
| `owner` | the enclosing class, if any |
| `message` | what is wrong, naming the evidence |
| `evidence` | the fact that produced the finding, such as `calls httpx.get` |
| `hint` | what to do about it |

The `evidence` field makes a finding arguable: "calls `httpx.get`" is a fact you can dispute, and "performs I/O" is not.

## The checks module

`namelint.checks` holds one pure function per code, each taking a function node and a `Context`. It imports nothing beyond `ast` and the two records, touches no filesystem, and reads no configuration. The verb table reaches it through `Context`.

There is no ruff plugin, because ruff has no plugin API.
