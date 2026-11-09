# The naming conventions namelint checks

## Junior

A function's name is a promise about what its body does. A reader who meets `user = get_user(uid)` in a code review trusts the name and moves on. They don't open `get_user` to check. When the body breaks the promise, the bug lands in that reader's code.

namelint checks a few promises that Python code makes all the time:

- A name that starts with a command verb (`set_`, `reset_`, `clear_`, `save_`) does something and returns nothing.
- A name that starts with a value verb (`get_`, `find_`, `to_`, `format_`) returns a value.
- A `get_` is cheap. It looks something up in memory, without waiting on a disk, a network or another process.
- A predicate (`is_`, `has_`, `can_`, `should_`, `was_`, `check_`) returns `True` or `False`.
- A property names a thing. The name is a noun (`size`, `owner`).
- A test function starts with `test`, or pytest skips it.
- A method doesn't repeat its class name. `user.name` reads better than `user.user_name`.
- A generator's name says it is lazy (`iter_lines`) or plural (`lines`). This one is opt-in.

When namelint reports a finding, read the message: it names the evidence, such as `calls httpx.get`. Then rename the function to match what it does, or change the body to match its name. If the name is right and namelint misread it, add the name to the allowlist in `pyproject.toml`.

Run `namelint explain NAM106` to read about one check, or add `--level senior` or `--level expert` for more depth.

## Senior

Every convention here is one Python programmers already follow without writing it down. `dict.get`, `getattr` and `os.environ.get` are cheap and always answer, so `get_` came to mean "cheap lookup". `list.append` and `dict.clear` return None, so a command verb came to mean "acts, answers nothing". namelint makes these unwritten rules checkable, and only where the body clearly contradicts the name.

namelint holds no opinion on vocabulary. It won't tell you that `fetch_` is better than `retrieve_`, or that a name is too long. Each check needs a fact from the body that contradicts the name: a `return` with a value, a call to `subprocess.run`, a `yield`. When the body gives no such fact, it says nothing. An unknown return type is silence, never a guess.

Private functions (a leading `_`) are out of scope for the checks on verbs and return values. A private name is a note to yourself. The callers sit a few lines away.

Some findings are correct about the code and still wrong about the name. `close_to_zero` doesn't close anything, and `User.user_name` is a user's name, which is a different thing from a name. Only the author can tell, so these go in `[tool.namelint.allow]` in `pyproject.toml`. The allowlist matches function names or `Class.method`, with shell wildcards, one list per code. There are no inline suppression comments, so every exception sits in one file a reviewer can read.

To adopt namelint on an existing codebase, run `namelint init --accept-existing`. It records every current finding in the allowlist, so only new code is reported.

## Expert

namelint reads the AST of each module and nothing else. It does no type inference, imports nothing, and resolves no names across modules. A check fires only on evidence it can show: a return annotation, the shape of a `return` expression, a call whose dotted name is known, a decorator. The `evidence` field of each finding names that fact, so a disagreement can be about the fact and never about the rule.

Each check is a pure function of an AST node and a `Context` (test module or not, enclosing class, sibling method names, the verb table). `checks.py` imports only `ast` and the two records, so a flake8 adapter could reuse it as is. Nested functions are not checked.

Every check is measured over a fixed corpus of nine projects (CPython's `Lib/`, attrs, pydantic, requests, httpx, rich, click, pytest and flask, 71,274 functions). A rule that fires often on code no reviewer would call badly named is a wrong rule. The bar is two false positives or fewer in a sample of thirty. `NAM107` misses that bar in protocol-heavy code, so it runs only when selected. The calibration tool and its outputs are in the repository, under `tools/calibrate.py` and `calibration/`.

The verb lists for `NAM104` and `NAM105` hold only verbs the corpus shows to be one-sided. `get_` returns a value in 916 of 921 public functions, and `reset_` returns nothing in 56 of 59. Verbs that go both ways (`load_`, `create_`, `read_`, `run_`) are in neither list. The verb test for `NAM102` comes from the Universal Dependencies English treebanks: a word counts as a verb when the treebanks tag it as a bare verb at least 90% of the time.
