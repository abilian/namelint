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
# NAM102 — a property named like a command
# ---------------------------------------------------------------------------

# `obj.compute_total` reads as an attribute at the call site, so a verb
# head promises an action the caller cannot see being taken, or hides
# one they should. Whether a head is a verb is a question for a lexicon
# (`ctx.verbs`, derived offline in `tools/build_verb_table.py`), never
# for a hand-written list: `name`, `value` and `record` are verbs in
# WordNet and nouns in every property ever written.


def check_property_named_as_verb(node: Function, ctx: Context) -> Finding | None:
    """NAM102: a `@property` whose first word is predominantly a verb."""
    if not _is_property(node):
        return None
    # A private name has an empty first word, so it never matches.
    head = node.name.split("_", 1)[0].lower()
    if head not in ctx.verbs:
        return None
    return Finding(
        "NAM102",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} is a property but opens with the verb {head!r};"
        " name what it holds, or make it a method",
        evidence=f"@property, {head!r} is predominantly a verb",
    )


def _is_property(node: Function) -> bool:
    return any(
        _dotted(decorator).rsplit(".", 1)[-1] in {"property", "cached_property"}
        for decorator in node.decorator_list
    )


# ---------------------------------------------------------------------------
# NAM103 — a predicate that does not return a bool
# ---------------------------------------------------------------------------

# `if is_ready():` reads the name, not the body. `check_` belongs here
# too: it answers a question, or raises when the answer is no. A predicate returning a
# string, a list or a count is read as truthy by every caller, so the
# empty string and the zero are the bug, and they surface far away.
#
# Annotations and return shapes only, per notes/02-specs.md §2: this tool
# does no type inference, and an unknown return is silence rather than a
# guess.

_PREDICATE_PREFIXES = ("is_", "has_", "can_", "should_", "was_", "check_")

# An annotation that says "unknown" is not evidence of a non-bool, which
# is §2's rule applied to the annotation rather than to the return.
_UNKNOWN_ANNOTATIONS = frozenset({"Any", "object"})

# `TypeGuard[X]` and `TypeIs[X]` annotate a function that returns a bool;
# the subscript says what the bool proves about the argument.
_BOOL_GUARDS = ("TypeGuard", "TypeIs")

# Literal shapes a return can carry that are evidently not booleans.
# A call is not here on purpose: `return self._check()` is unknown.
_NON_BOOL_NODES = (
    ast.JoinedStr,
    ast.List,
    ast.Dict,
    ast.Set,
    ast.Tuple,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.Lambda,
)


def check_predicate_returns_non_bool(node: Function, _ctx: Context) -> Finding | None:
    """NAM103: an `is_`/`has_`/`can_`/`should_`/`was_`/`check_` returning a non-bool."""
    if not node.name.startswith(_PREDICATE_PREFIXES):
        return None
    if _yields(node):
        return None  # a generator under a predicate name is NAM107's finding
    if node.returns is not None:
        shown = _non_bool_annotation(node)
        evidence = f"annotated -> {shown}"
    else:
        shown = _non_bool_return(node)
        evidence = f"returns {shown}"
    if shown is None:
        return None
    return _predicate_finding(node, evidence, shown)


def _non_bool_annotation(node: Function) -> str | None:
    """The return annotation, unparsed, when it says something other than bool."""
    annotation = node.returns
    if annotation is None or _bool_annotation(annotation) or _names_its_return(node):
        return None
    if node.name.startswith("check_") and _none_annotation(annotation):
        return None  # a `check_` may report by raising instead
    return ast.unparse(annotation)


def _predicate_finding(node: Function, evidence: str, shown: str) -> Finding:
    return Finding(
        "NAM103",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} reads as a predicate but {evidence};"
        f" callers will test {shown} for truth",
        evidence=evidence,
    )


def _bool_annotation(annotation: ast.expr) -> bool:
    """Whether this return annotation is a bool, or a guard that returns one."""
    annotation = _unquoted(annotation)
    if isinstance(annotation, ast.Subscript):
        return _dotted(annotation.value).rsplit(".", 1)[-1] in _BOOL_GUARDS
    return _dotted(annotation).rsplit(".", 1)[-1] == "bool"


def _none_annotation(annotation: ast.expr) -> bool:
    annotation = _unquoted(annotation)
    return isinstance(annotation, ast.Constant) and annotation.value is None


def _unquoted(annotation: ast.expr) -> ast.expr:
    """Parse a string annotation, from a forward reference or PEP 563.

    Parsing keeps `-> "bool"` reading as a bool. An unparsable string is
    returned as is, which no caller reads as a bool.
    """
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        try:
            return ast.parse(annotation.value, mode="eval").body
        except SyntaxError:
            return annotation
    return annotation


def _names_its_return(node: Function) -> bool:
    """Whether the name describes what the function returns, so it is a factory.

    `is_instance_schema(cls) -> IsInstanceSchema` builds an "is-instance"
    schema: the `is_` belongs to the thing's name and is not a predicate
    prefix at all. The tell is that the name's last word also names the
    returned type, which held for four of the seven findings in the
    first corpus run, all of them wrong.

    Whole words only. `is_valid -> ValidationResult` keeps its finding,
    because "valid" and "validation" are two words.
    """
    annotation = node.returns
    if annotation is None:
        return False
    words = _annotation_words(annotation)
    if words & _UNKNOWN_ANNOTATIONS_LOWER:
        return True
    return node.name.rsplit("_", 1)[-1].lower() in words


_UNKNOWN_ANNOTATIONS_LOWER = frozenset(name.lower() for name in _UNKNOWN_ANNOTATIONS)


def _annotation_words(annotation: ast.expr) -> frozenset[str]:
    """The lowercased words in an annotation: `str | bool` gives {str, bool}."""
    return frozenset(_words(ast.unparse(annotation)))


def _words(text: str) -> list[str]:
    """The lowercased words in an identifier, split on case and punctuation.

    `JsonSchemaValue` gives [json, schema, value]; `HTTPServer` gives
    [http, server]. Hand-rolled because `checks.py` imports nothing but
    `ast`, which is the boundary notes/02-specs.md §7 sets.
    """
    words: list[str] = []
    current = ""
    for i, char in enumerate(text):
        following = text[i + 1] if i + 1 < len(text) else ""
        if not char.isalnum():
            words.append(current)
            current = ""
        elif (
            char.isupper()
            and current
            and (not current[-1].isupper() or following.islower())
        ):
            words.append(current)
            current = char
        else:
            current += char
    words.append(current)
    return [word.lower() for word in words if word]


def _non_bool_return(node: Function) -> str | None:
    """The first returned value that is evidently not a bool, unparsed."""
    for value in _returned(node):
        if isinstance(value, ast.Constant):
            # `True`, `False` and `None` are not evidence of a non-bool.
            # `None` is an early exit in half the predicates ever written.
            if isinstance(value.value, bool) or value.value is None:
                continue
            return ast.unparse(value)
        if isinstance(value, _NON_BOOL_NODES):
            return ast.unparse(value)
    return None


# ---------------------------------------------------------------------------
# NAM104 and NAM105 — what the verb promises about the return
# ---------------------------------------------------------------------------

# A leading verb is a promise about the return. `total = get_total()`
# expects a value, and `reset_cache()` used in an expression is a bug the
# name invited. So a value verb must return something, and a command
# verb must not.
#
# Both lists hold only verbs the corpus shows to be one-sided: `get_`
# returns a value in 916 of 921 public functions, `reset_` returns none
# in 56 of 59. Two-sided verbs (`load_`, `create_`, `make_`, `read_`,
# `add_`, `run_`, `handle_`) are left out. `load_config()` filling
# `self` and `create_dir()` touching disk are commands by convention,
# and `create_model()` is a query, and the name cannot say which.
#
# Private functions are out of scope. A leading underscore says the name
# is nobody else's contract.

_VALUE_VERBS = frozenset(
    {
        "get",
        "find",
        "compute",
        "calc",
        "calculate",
        "count",
        "lookup",
        "as",
        "to",
        "format",
    }
)
_COMMAND_VERBS = frozenset(
    {
        "set",
        "reset",
        "clear",
        "close",
        "print",
        "emit",
        "insert",
        "append",
        "show",
        "stop",
        "warn",
        "init",
        "update",
        "save",
    }
)

# A declaration has no body to contradict its name.
_DECLARATION_DECORATORS = ("abstractmethod", "overload")


def check_command_returns_value(node: Function, _ctx: Context) -> Finding | None:
    """NAM104: a command verb (`set_`, `reset_`, `close`) that returns a value."""
    if _verb(node) not in _COMMAND_VERBS or _yields(node):
        return None
    for value in _returned(node):
        if not _command_status(value, node.name):
            shown = ast.unparse(value)
            return Finding(
                "NAM104",
                node.lineno,
                node.col_offset + 1,
                node.name,
                f"{node.name} reads as a command but returns {shown};"
                " name it for what it returns, or return nothing",
                evidence=f"returns {shown}",
            )
    return None


def _command_status(value: ast.expr, name: str) -> bool:
    """Whether a command's return is a protocol, not a value it computes.

    Four shapes stay quiet: `return None` (an early exit), `return self`
    (chaining), a bool literal (success, as in `update_file() -> True`),
    and passing on the result of the same command one level down
    (`return super().set_cookie(...)`).
    """
    if isinstance(value, ast.Name) and value.id == "self":
        return True
    if isinstance(value, ast.Constant) and (
        value.value is None or isinstance(value.value, bool)
    ):
        return True
    return isinstance(value, ast.Call) and _dotted(value.func).endswith(name)


def check_query_returns_none(node: Function, _ctx: Context) -> Finding | None:
    """NAM105: a value verb (`get_`, `find_`, `to_`) whose returns carry nothing."""
    if _verb(node) not in _VALUE_VERBS or _is_stub(node) or _yields(node):
        return None
    if any(
        _dotted(decorator).rsplit(".", 1)[-1] in _DECLARATION_DECORATORS
        for decorator in node.decorator_list
    ):
        return None
    if next(_returned(node), None) is not None:
        return None
    return Finding(
        "NAM105",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} reads as a query but returns None on every path;"
        " return the value, or name it as a command",
        evidence="no return carries a value",
    )


def _verb(node: Function) -> str:
    """The leading word of a multi-word name, else ``""``.

    `get_user` gives `get`. A bare `get` or `close` is a protocol method
    (`dict.get`, `file.close`) whose contract lives in its type, so it
    gives nothing. A private or dunder name opens with an empty word,
    which no verb list holds.
    """
    if "_" not in node.name:
        return ""
    return node.name.split("_", 1)[0]


def _is_stub(node: Function) -> bool:
    """A body of docstring, `pass`, `...` and `raise`, or one ending in `raise`.

    Neither falls off the end with `None`: the first is a declaration,
    the second never returns at all on its last path.
    """
    if isinstance(node.body[-1], ast.Raise):
        return True
    return all(
        isinstance(statement, ast.Pass)
        or (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
        )
        for statement in node.body
    )


def _returned(node: Function) -> Iterator[ast.expr]:
    """Every expression the function itself returns, `return None` included.

    An explicit `return None` is a value: `get_source()` returning None
    for "no source" is the importlib protocol, not a command in
    disguise. Only falling off the end, or a bare `return`, is silence.
    """
    for child in _own_body(node):
        if isinstance(child, ast.Return) and child.value is not None:
            yield child.value


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
# NAM108 — a method that repeats its class name
# ---------------------------------------------------------------------------

# `user.user_name` says "user" twice; the call site already holds the
# class. The repeat is the whole class name as a run of words, so
# `Config.config_path` matches and `ConfigLoader.config_path` does not.
#
# Ambiguity is the norm here: `Style.background_style` is a different
# style, and a user name is not the same thing as a user's name. Those
# go in the allowlist. What the check skips on its own:
#
# - test modules and `Test*` classes, which mirror names by convention;
# - private methods, and a method named exactly like its class
#   (`Filter.filter`), which is a protocol;
# - a class where three or more methods repeat the name. That is a
#   namespace on purpose, as in tkinter's `Wm.wm_title`, `Wm.wm_frame`.

_PREFIX_CONVENTION = 3


def check_method_repeats_class(node: Function, ctx: Context) -> Finding | None:
    """NAM108: a method whose name contains its class name as whole words."""
    if ctx.class_name is None or ctx.is_test_module or node.name.startswith("_"):
        return None
    cls = _words(ctx.class_name)
    if cls[0] == "test" or _words(node.name) == cls or not _repeats(node.name, cls):
        return None
    if sum(_repeats(sibling, cls) for sibling in ctx.siblings) >= _PREFIX_CONVENTION:
        return None
    return Finding(
        "NAM108",
        node.lineno,
        node.col_offset + 1,
        node.name,
        f"{node.name} repeats its class name {ctx.class_name};"
        " the call site already says it",
        evidence=f"method of {ctx.class_name}",
    )


def _repeats(name: str, cls: list[str]) -> bool:
    words = _words(name)
    run = len(cls)
    return any(words[i : i + run] == cls for i in range(len(words) - run + 1))


# ---------------------------------------------------------------------------
# Driving them
# ---------------------------------------------------------------------------

CHECKS = (
    check_uncollected_test,
    check_property_named_as_verb,
    check_predicate_returns_non_bool,
    check_command_returns_value,
    check_query_returns_none,
    check_get_performs_io,
    check_unlazy_generator,
    check_method_repeats_class,
)
CODES = (
    "NAM101",
    "NAM102",
    "NAM103",
    "NAM104",
    "NAM105",
    "NAM106",
    "NAM107",
    "NAM108",
)


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
