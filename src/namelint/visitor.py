"""Walks a module and hands each function to the checks.

The signature `check_module(tree, path) -> list[Finding]` is deliberate:
it is also flake8's plugin contract, so an adapter later is an entry
point and a wrapper rather than a second implementation.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

from namelint.checks import Function, check_function
from namelint.finding import Context, Finding


def check_module(tree: ast.Module, path: Path) -> list[Finding]:
    """Every finding in one parsed module."""
    is_test = is_test_module(path)
    found: list[Finding] = []
    for node, class_name in _functions(tree):
        ctx = Context(is_test_module=is_test, class_name=class_name)
        found += check_function(node, ctx)
    return sorted(found, key=lambda f: (f.line, f.col, f.code))


def check_source(source: str, path: Path) -> list[Finding]:
    """Run `check_module` over text. Raises `SyntaxError` on unparsable input."""
    return check_module(ast.parse(source), path)


def is_test_module(path: Path) -> bool:
    """Whether pytest would collect this file for tests.

    Both halves of pytest's default: a `test_*.py` or `*_test.py` name,
    or any module living under a `tests/` directory.
    """
    name = path.name
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    return any(part in {"tests", "test"} for part in path.parts[:-1])


def _functions(tree: ast.Module) -> Iterator[tuple[Function, str | None]]:
    """Every function in the module, with the class it belongs to.

    Nested functions are skipped. A closure's name is private to its
    parent, so none of these rules has anything to say about it.
    """
    stack: list[tuple[ast.AST, str | None]] = [(tree, None)]
    while stack:
        node, class_name = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield child, class_name
            elif isinstance(child, ast.ClassDef):
                stack.append((child, child.name))
            else:
                stack.append((child, class_name))


__all__ = ["Function", "check_module", "check_source", "is_test_module"]
