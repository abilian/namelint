"""The checks themselves: AST in, findings out.

Every check here reports a *contradiction* between a name and a fact in
the body. None of them holds an opinion about vocabulary. "Too generic"
belongs in a style guide; this module only says that a name and a body
disagree.

Imports nothing but `ast` and the records in `finding`, which is what
keeps the module portable into a flake8 adapter or another tool.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator

from namelint.finding import Context, Finding

Function = ast.FunctionDef | ast.AsyncFunctionDef

# ---------------------------------------------------------------------------
# NAM101 — a test that will never run
# ---------------------------------------------------------------------------

# pytest collects `test*` and nothing else. A function in a test module
# that asserts and is not collected is a test that reports nothing, which
# makes this a defect rather than a style preference.
#
# The hard part is telling a test from an assertion-bearing helper
# (`assert_ok(response)`). The discriminator used here is arity: a test
# takes fixtures or nothing, while a helper takes the thing it checks. A
# decorated function is left alone, since that is what a fixture looks
# like.


def check_uncollected_test(node: Function, ctx: Context) -> Finding | None:
    """NAM101: an asserting, zero-argument function in a test module."""
    if not ctx.is_test_module or node.name.startswith("test"):
        return None
    # A leading underscore says private, which says "not collected" as
    # plainly as the name could. Every one of the nine findings in the
    # first corpus run was a `_`-prefixed helper, and all nine were wrong.
    if node.name.startswith("_"):
        return None
    if node.decorator_list or _positional_arity(node, ctx):
        return None
    if not _asserts(node):
        return None
    return Finding(
        "NAM101",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} asserts but pytest will not collect it;"
        f" rename to test_{node.name}",
        evidence="contains an assertion, takes no arguments",
    )


def _positional_arity(node: Function, ctx: Context) -> int:
    """Parameters the caller must supply, ignoring `self`/`cls`."""
    args = [*node.args.posonlyargs, *node.args.args]
    if ctx.class_name and args and args[0].arg in {"self", "cls"}:
        args = args[1:]
    return len(args)


def _asserts(node: Function) -> bool:
    return any(
        isinstance(child, ast.Assert)
        or (isinstance(child, ast.With) and _raises_block(child))
        for child in _own_body(node)
    )


def _raises_block(node: ast.With) -> bool:
    return any(
        _dotted(item.context_expr.func).endswith("raises")
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
    )


# ---------------------------------------------------------------------------
# NAM106 — a name that promises cheap and does I/O
# ---------------------------------------------------------------------------

# `get` is a contract in Python, not a lazy choice: `dict.get`,
# `getattr`, `os.environ.get` are all cheap and total. A `get_` that
# opens a socket breaks that promise, which is the one real defect in the
# article this rule came from.

_IO_CALLS = frozenset({"open"})
_IO_SUFFIXES = (
    "read_text",
    "read_bytes",
    "write_text",
    "write_bytes",
    "urlopen",
    "urlretrieve",
    "execute",
    "executemany",
    "fetchone",
    "fetchall",
    "connect",
    "recv",
    "send",
    "sendall",
)
_IO_ROOTS = frozenset(
    {"requests", "httpx", "urllib", "socket", "subprocess", "aiohttp"}
)
_CHEAP_NAMES = frozenset({"get", "getattr"})


def check_get_performs_io(node: Function, _ctx: Context) -> Finding | None:
    """NAM106: a `get_` whose body reaches a disk, a socket or a database."""
    if not (node.name == "get" or node.name.startswith("get_")):
        return None
    call = _first_io_call(node)
    if call is None:
        return None
    return Finding(
        "NAM106",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} performs I/O (calls {call}); get_ promises a cheap"
        " lookup, use fetch_, load_ or read_",
        evidence=f"calls {call}",
    )


def _first_io_call(node: Function) -> str | None:
    for child in _own_body(node):
        if not isinstance(child, ast.Call):
            continue
        name = _dotted(child.func)
        if not name or name in _CHEAP_NAMES:
            continue
        if name in _IO_CALLS or name.endswith(_IO_SUFFIXES):
            return name
        if name.split(".", 1)[0] in _IO_ROOTS:
            return name
    return None


# ---------------------------------------------------------------------------
# NAM107 — a generator that does not say it is lazy
# ---------------------------------------------------------------------------

# A caller who believes they hold a list and actually hold a one-shot
# iterator writes a bug that surfaces two loops later. A plural noun says
# it (`items`, `values`), and so does a lazy prefix.

_LAZY_PREFIXES = (
    "iter",
    "walk",
    "gen",
    "generate",
    "stream",
    "scan",
    "traverse",
    "produce",
    "yield",
    "enumerate",
    "chunk",
)


# A `yield` is not always iteration. In a pytest fixture or a
# `@contextmanager` it is a setup/teardown protocol, and the name is a
# noun on purpose: `db_session`, `temp_config`, `client`. Nearly every
# NAM107 finding in the first corpus run was one of these.
_PROTOCOL_DECORATORS = (
    "fixture",
    "contextmanager",
    "asynccontextmanager",
    "hookimpl",  # pluggy wrappers use `value = yield` as a send point
)


def check_unlazy_generator(node: Function, _ctx: Context) -> Finding | None:
    """NAM107: a generator whose name reads as if it returned a container."""
    if node.name.startswith("__") or not _yields(node):
        return None
    if _has_protocol_decorator(node):
        return None
    # A leading underscore is privacy, not a name. `_walk` and
    # `_stream_into_assistant` carry lazy prefixes and were both reported
    # until the underscore came off first.
    bare = node.name.lstrip("_")
    if bare.startswith(_LAZY_PREFIXES) or _plural(bare):
        return None
    return Finding(
        "NAM107",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} is a generator; name it iter_{node.name} or use a plural",
        evidence="contains yield",
    )


def _has_protocol_decorator(node: Function) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if _dotted(target).rsplit(".", 1)[-1].endswith(_PROTOCOL_DECORATORS):
            return True
    return False


def _yields(node: Function) -> bool:
    """Whether `node` itself yields, ignoring generators nested inside it."""
    return any(
        isinstance(child, (ast.Yield, ast.YieldFrom)) for child in _own_body(node)
    )


def _plural(name: str) -> bool:
    """Apply a crude plural test to the final word of a snake_case name."""
    last = name.rsplit("_", 1)[-1]
    return last.endswith("s") and not last.endswith("ss")


# ---------------------------------------------------------------------------
# Driving them
# ---------------------------------------------------------------------------

CHECKS = (check_uncollected_test, check_get_performs_io, check_unlazy_generator)
CODES = ("NAM101", "NAM106", "NAM107")


def check_function(node: Function, ctx: Context) -> list[Finding]:
    """Every finding the checks report for one function."""
    return [found for check in CHECKS if (found := check(node, ctx)) is not None]


def _own_body(node: Function) -> Iterator[ast.AST]:
    """Every node under `node`, without descending into a nested function.

    `ast.walk` would cross that boundary, so an inner generator would
    make its enclosing function look like one, and an assertion inside a
    nested helper would make its enclosing function look like a test.
    """
    stack: list[ast.AST] = list(node.body)
    while stack:
        current = stack.pop()
        yield current
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(current))


def _dotted(node: ast.AST) -> str:
    """Return `a.b.c` for an attribute chain, the bare id for a name, else ``""``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = _dotted(node.value)
        return f"{head}.{node.attr}" if head else node.attr
    return ""
