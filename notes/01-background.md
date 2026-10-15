# Naming functions: rules to apply now, and a linter that might check them

Prompted by "The Naming Algorithm" (a Medium post with a decision tree and a verb blacklist). The tree is one practitioner's taste. A few of its calls are wrong for Python. What follows keeps only the parts that clean Python codebases already enforce, then asks which of those a tool could check.

Two things this note is careful about. It does not duplicate what `ruff` already does. And it separates a rule from its detector: several rules below are sound and have no safe automatic check. That puts them in a playbook. It does not drop them.

## Part 1. Rules we can apply today

Nine rules. Each is conventional in Python, each has a reference point in the standard library or a major style guide, and none of them needs a tool to be useful in review.

### 1. A function is a verb phrase. A class is a noun phrase.

`parse_config`, `send_invoice`, `Invoice`, `ConfigParser`. A function named `user_data()` reads as a variable at the call site. A class named `Validate` reads as a function.

Reference: PEP 8, plus every major style guide. The convention is universal enough that a violation usually signals a missing abstraction, where a mere naming slip would be the smaller problem.

### 2. A `@property` is a noun, with no verb.

`circle.area`, never `circle.calculate_area`. A property exists so the caller can forget that work happens; a verb in the name puts the work back in view.

Reference: the standard library throughout (`datetime.year`, `Path.parent`, `Exception.args`).

### 3. A predicate reads as a predicate.

Return a `bool`, open with `is_`, `has_`, `can_`, `should_` or `was_`. `is_expired`, `has_permission`, `can_retry`.

Reference: `str.isdigit`, `Path.exists`, `inspect.isclass`. The form `check_if_token_expired` from the source post is longer and says less.

### 4. A test function is `test_*`, because pytest says so.

This is no style rule. A test function outside the `test_*` pattern is never collected, so it never runs. A suite reporting green over it reports nothing. Treat a violation as a defect, never as a preference.

Reference: pytest's default `python_functions = test*`.

### 5. Imperative mutates; participle returns a copy.

`list.sort()` mutates and returns `None`. `sorted()` returns a new list. Likewise `list.reverse()` against `reversed()`. A function whose name is a bare imperative should mutate; one that returns a fresh object should say so.

The checkable half: **a function returning `None` on every path is an imperative**, so a query-shaped name on it (`get_`, `find_`, `compute_`) is a contradiction.

Reference: the `sort`/`sorted` pair is the canonical Python example.

### 6. The name must not lie about cost.

A name promising a cheap lookup must not open a socket. This is the one real insight in the source post, stated without its mistake. The problem with its `get_user` was never that `get` is vague. It was that `get` **promises cheap and total** while the function did a database round trip.

So keep `get_` for cheap total accessors, in line with `dict.get`, `getattr` and `os.environ.get`. Require a different verb once the body does I/O: `fetch_` over a network, `load_` or `read_` from disk, `save_`, `write_` or `send_` outward.

Reference: `dict.get` and `os.environ.get` are the contract. `requests.get` is the counter-example that confuses everyone, named for the HTTP verb.

### 7. Do not stutter.

`User.get_user_name()` inside class `User` repeats what the receiver already said. Prefer `user.name` or `user.get_name()`.

Reference: Go's style guide states this most directly. Python practice follows it, as in `Path.name`, never `Path.get_path_name`.

### 8. A generator announces that it is lazy.

`iter_rows`, `walk_tree`, or a plural noun (`items`, `values`). A caller who believes they hold a list and actually hold a one-shot iterator writes a bug that surfaces two loops later.

Reference: `dict.items`, `os.walk`, `itertools` throughout.

### 9. No noise word as the whole name.

`data`, `info`, `stuff`, `helper`, `util`, `manager`, `object`: none says anything alone. `process_data()` names its argument twice and its work zero times.

Reference: the one rule here taken straight from *Clean Code*. It is also the first I would weaken if it proves noisy. Compounds are often fine (`UserManager` in a codebase with a manager layer); the bare noun rarely is.

### What `ruff` already enforces

No point rebuilding these. `pep8-naming` (N801 to N818) covers case conventions, `self`/`cls`, and exception-name suffixes. `flake8-builtins` (A001 to A003) covers shadowing. `pydocstyle` and `flake8-annotations` cover the surrounding documentation and typing. The nine rules above are what is left over.

### What we are not taking from the source post

Its blacklist bans `compare`, `main` and `run`. But `compare` is the precise name for a three-way comparison, the kind `functools.cmp_to_key` consumes. `main` is required by `if __name__ == "__main__":`. And `run` is a protocol name on a runner object (`subprocess.run`, `Thread.run`). Banning any of the three produces false positives in every codebase.

The post also blacklists `handle`, while `ken-python/coding-guidelines.md` recommends `handle_` for event handlers. We keep `handle_` on a dispatch surface, where the protocol sets the name.

## Part 2. Automating it: `namelinter`

The useful check is never "is this verb on a list". That is a grep. A grep over names cannot separate a `fetch_user` that opens a socket from one that reads a dict. The useful check compares the **name against the body**, which an AST pass can do for about half the rules above.

### Tier 1: a contradiction the AST can see

| Check | Rule | Signal in the body |
|---|---|---|
| test function not named `test_*` | 4 | defined in a `test_*.py` module or under `tests/` |
| `@property` whose name opens with a verb | 2 | decorator, plus a first token in a verb list |
| `is_`/`has_`/`can_` returning a non-bool | 3 | return annotation, or every `return` yields a comparison or bool literal |
| bool return under a non-predicate name | 3 | annotation is `bool` |
| `get_`/`find_`/`compute_` returning `None` on every path | 5 | no `return` with a value anywhere |
| `get_` performing I/O | 6 | calls `open`, `requests`/`httpx`, `Path.read_*`/`write_*`, a session object |
| generator under a non-lazy name | 8 | `yield` in the body |
| method repeating its class name | 7 | `ClassName` appears in the method name |

Eight checks, each a few lines of `ast` walking. Each one reports a mismatch in the code; none offers an opinion about vocabulary.

### Tier 2: lower confidence, reported as `inspect`

Four cases: mutation under a non-mutating verb, `parse_` taking no string, `render_` returning no string, a bare noise word as the full name. These need either type inference or a judgement the AST cannot supply, so they go out tagged advisory, the way rules 29 and 31 do in the prose linter.

### Tier 3: no detector

Rules 1 and 9 in their general form. A playbook entry, read while naming.

### Shape

A self-standing PEP 723 script, `namelinter.py`, the way `proselinter.py` began. No install step, runnable against any checkout, one `ast.NodeVisitor`. It finds a home in `ken` later if the measurement justifies one, since naming is code quality and `letscode_ken.autocheck` already runs over every file the model writes.

## Part 3. Calibrating against clean code

The step that decides whether any of this ships. **A rule firing often on a reputable codebase is a wrong rule. It is no evidence about the codebase.** The prose linter learned this the hard way, which is why `proselinter --calibrate` exists.

Proposed corpus, chosen for being well reviewed and stylistically unlike each other:

| Project | Why it is in the corpus |
|---|---|
| CPython `Lib/` | the reference for what Python naming means, old enough to hold exceptions |
| `attrs`, `pydantic` | heavily reviewed, modern, annotated throughout |
| `httpx`, `requests` | I/O-centred, so rule 6 gets a real workout |
| `rich`, `click` | large public APIs where names are the product |
| `pytest` | the authority on rule 4, in a codebase where `run_` is idiomatic |
| `flask` | dispatch-heavy, so `handle_` gets tested |

Method:

1. Count findings per thousand functions, by rule and by project.
2. Adjudicate a random sample of thirty per rule by hand.
3. Any rule above roughly two false positives in thirty either gets a narrower detector or drops to Tier 2.
4. Keep the adjudication, so a later change to a detector is measured against the same sample instead of a fresh impression.

Four predictions, written down now so the measurement can embarrass them:

- Rule 4 should find almost nothing in `pytest`, and may find real dead tests elsewhere.
- Rule 6 will fire on `requests.get` and its relatives, where `get` is the HTTP verb. That needs an exception for a module whose domain is HTTP.
- Rule 7 will fire on legitimate disambiguation (`Config.config_path`), and may not hold up as a Tier 1 check.
- Rule 3's inverse arm (a bool return under a non-predicate name) is the one I expect to be noisiest, because `main() -> bool` and its like are ordinary.

## Open questions

1. Does Tier 1 read annotations only, or shell out to a type checker for return types? Annotations are cheap and this codebase annotates everything; inference means reading `ty` or `pyrefly` output.
2. Per-project exceptions: the prose linter solved this with `.prose.json` plus `/prose:allow`. The same shape would work here. The HTTP case above suggests we need it on day one.
3. Does it check anything beyond functions? Classes and modules have conventions of their own, and nothing above addresses them.

## Next step

Write the eight Tier 1 checks as `namelinter.py`, run them over the corpus in Part 3, and bring back the counts. The rules in Part 1 are usable in review today and wait on none of that.
