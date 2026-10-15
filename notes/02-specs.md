# namelint: specification

Status: draft, pre-implementation. Written 2026-10-02.

Repository: `github.com/abilian/namelint`. Distribution: `namelint` on PyPI.

Background and the reasoning behind the rule set: `notes/01-background.md`.

## 1. Objective

A Python linter that reports **where a function's name contradicts its body**.

Existing tools check the shape of a name. `ruff`'s `pep8-naming` knows that `getUserName` is not `snake_case`; nothing knows that `get_user` opens a socket. That gap is the whole product: every check here needs the AST, and none of them is a grep over identifiers.

Scope for v1 is functions and methods. Classes and modules are out, as are variables.

### Target users

1. Python developers, running `uvx namelint src/` or a CI step. This is the audience that decides whether the tool is any good.
2. Coding agents, through a thin plugin in `letscode-plugins` that wraps this package for letscode, Claude Code and pi. That plugin depends on this one; this one knows nothing about agents.

### Non-goals

- No autofix. Renaming a function is an API change. A tool that does it silently is more dangerous than the defect.
- No style-shape checks. `ruff` owns case conventions, builtin shadowing and the annotation rules.
- No vocabulary opinions. The tool never says a verb is "too generic"; it says a name and a body disagree.
- No type inference in v1. Annotations and return-statement shapes only.

## 2. The checks

Eight checks, each reporting a contradiction the AST can see. Codes are `NAM1xx`; the prefix is checked against the flake8 plugin registry before any flake8 adapter ships.

| Code | Finding | Evidence in the body |
|---|---|---|
| `NAM101` | test function not named `test_*` | defined in a `test_*.py` module, or under a `tests/` directory |
| `NAM102` | `@property` whose name opens with a verb | `property` decorator, plus a first token the lexicon scores as verb-dominant (§8.2) |
| `NAM103` | `is_`/`has_`/`can_`/`should_`/`was_`/`check_` that does not return a bool | return annotation that is not `bool`, or returns of an evidently non-bool shape |
| `NAM104` | command verb (`set_`, `reset_`, `update_`) that returns a value | a `return` carrying a value other than `self`, `None` or a bool literal |
| `NAM105` | value verb (`get_`, `find_`, `to_`) returning nothing | no `return` holds a value, `return None` included, with no `yield` either |
| `NAM106` | `get_` that performs I/O | calls `open`, `Path.read_*`/`write_*`, `requests`/`httpx`/`urllib`, or a session-shaped object |
| `NAM107` | generator under a non-lazy name | `yield` or `yield from` in the body |
| `NAM108` | method repeating its class name | the class name appears as a token in the method name |

### Type information

**Annotations and return-statement shapes only.** Nothing is spawned and nothing is imported beyond the standard library.

A return is read as boolean when it is a bool literal, a comparison, a `not`, an `and`/`or` chain of such, or a call to a known predicate (`isinstance`, `issubclass`, `hasattr`, `callable`, `any`, `all`, a `.is*()` method). Anything else is **unknown**, so an unknown return produces no finding. Silence on the uncertain case is a choice, and §6 counts how large that silent bucket turns out to be.

### Suppression

**An allowlist of names, decided 2026-10-15 from the second corpus run.** The exceptions turned out to be names, not modules: `User.user_name` (a user name is not a user's name), `close_to_zero` (an adjective, not the verb), `options.update_width()` (a copy-and-update API). So `[tool.namelint.allow]` in `pyproject.toml` maps a code to function names or `Class.method` patterns with shell wildcards. No inline comments and no path exclusions: the project's exceptions stay in one reviewable place.

`--select` and `--ignore` by *code* exist, since turning a whole rule off is how calibration isolates one.

## 3. Commands

```sh
namelint PATH...                 # walk, report, exit 1 if anything fired
namelint --json PATH...          # one JSON object per finding, for counting
namelint --stats PATH...         # counts per code, per file; the calibration view
namelint --select NAM106 PATH... # one rule only
namelint --ignore NAM104 PATH... # all but one
namelint --version
```

Default output, one line per finding, the format every editor already parses:

```
src/app/users.py:42:5: NAM106 get_user performs I/O (calls httpx.get); use fetch_ or load_
```

Exit codes mirror `proselinter`: `0` clean, `1` findings, `2` the tool itself failed.

`uvx namelint ~/src/cpython/Lib` must work with no install step, because §6 runs it over nine checkouts.

## 4. Project structure

```
namelint/
├── pyproject.toml          # hatchling; no runtime dependencies
├── README.md
├── notes/                  # 01-background.md, 02-specs.md
├── Makefile                # check / test / format, same targets as letscode-plugins
├── src/namelint/
│   ├── __init__.py
│   ├── __main__.py         # python -m namelint
│   ├── finding.py          # the Finding record
│   ├── checks.py           # one function per code, pure, AST in / Findings out
│   ├── visitor.py          # the single NodeVisitor that drives them
│   ├── verbs.py            # loads data/verb_pos.json; the prefix lists
│   ├── report.py           # text, json, stats
│   ├── cli.py              # argparse, walking, exit codes
│   └── data/
│       └── verb_pos.json   # P(VERB|lemma), derived, see §8.2
├── tools/
│   └── build_verb_table.py # regenerates verb_pos.json from the lexicon
└── tests/
    ├── a_unit/             # one module per check, fast, no filesystem
    ├── b_integration/      # the CLI over fixture trees
    └── fixtures/           # small .py files, one per check, good and bad cases
```

Two constraints on the layout:

- **`checks.py` imports nothing but `ast` and `finding`.** It is the part that would move if this ever merges into another tool. It is also the part a flake8 adapter would call.
- **The core signature is flake8's plugin contract**: `lint_module(tree: ast.Module, path: Path) -> list[Finding]`. A flake8 adapter is then an entry point and a generator wrapper, written only if someone asks.

## 5. Code style

Follows the conventions already in use across these projects, so a reader moving between them finds the same shapes.

- Python 3.12+ to run. Parsing is best-effort for older syntax, since `ast` reads what the running interpreter understands.
- `uv` for everything. `ruff` for lint and format, `ty` and `pyrefly` for types. No `pip`, no `black`, no `flake8`.
- Type hints on every function. Records are `dataclass(frozen=True)`.
- Functional core, imperative shell: `checks.py` is pure, `cli.py` owns the filesystem and `sys.exit`.
- A complexity ceiling signals that a helper wants extracting. It is never a number to raise.
- No silenced linter. A `noqa` states its reason on the same line or it does not go in.
- Markdown soft-wrapped: one paragraph, one line.

Each check is one function with one job, named for what it reports. The prefix is `find_`, not `check_`: `NAM103` reads `check_` as a predicate, and a check returns a finding, so namelint would otherwise fail its own lint.

```python
def find_get_performs_io(node: ast.FunctionDef, ctx: Context) -> Finding | None:
```

## 6. Testing strategy

### Unit and integration

The pyramid used in `letscode-plugins`: `tests/a_unit/` for the checks themselves, `tests/b_integration/` for the CLI over fixture trees. `pytest`, AAA, `assert x == y`. Mocks are out, and so is `__init__.py` under `tests/`.

Every check gets at least four tests: the contradiction it reports, the legitimate case it must stay silent on, a boundary, and one unknowable case that must produce nothing.

**A check is not done until it has been sabotaged.** Break the detector, confirm the suite goes red, restore from a copy and diff. A test that passes with the check deleted is not a test.

### Calibration, which is the real acceptance criterion

A rule firing often on a reputable codebase is a wrong rule. It is no evidence about the codebase.

Corpus, chosen so each rule meets a codebase built to stress it:

| Project | Stresses |
|---|---|
| CPython `Lib/` | the reference for what Python naming means, old enough to hold exceptions |
| `attrs`, `pydantic` | modern, annotated throughout, so `NAM103`/`NAM104` run at full strength |
| `requests`, `httpx` | I/O-centred, so `NAM106` meets the HTTP-verb problem head on |
| `rich`, `click` | large public APIs where names are the product |
| `pytest` | the authority on `NAM101`, in a codebase where `run_` is idiomatic |
| `flask` | dispatch-heavy, so `handle_` gets tested |

Method:

1. `namelint --stats` over each checkout. Record findings per thousand functions, by code and project.
2. Hand-adjudicate a random thirty per code.
3. Any code above roughly two false positives in thirty gets a narrower detector, drops to advisory, or is cut.
4. Keep the adjudicated sample, so a later change is measured against the same cases and never against a fresh impression.

Predictions recorded now so the measurement can contradict them:

- `NAM101` finds almost nothing in `pytest`, and may find real dead tests elsewhere.
- ~~`NAM106` fires across `requests`, where `get` is the HTTP verb. The exception this demands is module-scoped, which is the evidence that decides the suppression design.~~ **Measured false.** `requests` reports 0 NAM106 findings in 711 functions: its HTTP verbs are `requests.api.get` calling `request()`, which puts the I/O one frame further down. The check fires in `flask` (1.37 per 1000) and `httpx` (0.88) instead. So nothing measured demands a module-scoped exception, which leaves the suppression design without evidence. It stays unbuilt.
- `NAM108` fires on legitimate disambiguation such as `Config.config_path`, and may not hold up.
- `NAM104` is the noisiest of the eight, since `main() -> bool` is ordinary.
- `NAM102` fires on noun/verb-ambiguous heads. An isolated-token tagger reads `account`, `report` and `record` as verbs, and all three are ordinary property names. This check and `NAM108` are the two most likely to be cut.

**Acceptance for v1**: every check at or below two false positives in thirty on the corpus, or cut. A tool that cries wolf on `requests` has no value, however elegant its AST pass.

## 7. Boundaries

### Always

- Report, never rewrite. The tool has no `--fix` and will not grow one.
- Stay silent when the evidence is absent. An unknown return type produces no finding.
- Name the evidence in the message. `NAM106` says which call made it I/O, which leaves room to disagree with that specific fact.
- Keep `checks.py` free of imports beyond `ast`.

### Ask first

- Adding a ninth check. Eight is the set the note argued for; a ninth needs the same argument and the same calibration.
- Adding a runtime dependency. There are none today. That is a feature.
- Shipping the flake8 adapter, which needs a code-prefix decision.
- Extending the allowlist beyond names (inline comments, paths).

### Never

- Never commit or push without being asked. Summarise, then wait.
- Never mention an AI assistant or co-author in a commit message.
- Never add a check that is an opinion about vocabulary. "Too generic" belongs in a style guide, never in a linter finding.
- Never hard-wrap Markdown.

## 8. Open questions

1. Code prefix: `NAM1xx` needs checking against the flake8 registry before a flake8 adapter could use it.
2. ~~Where the verb vocabulary comes from.~~ **Resolved.** A hand-written list of verbs common in code encodes one dialect and misses the domain's own vocabulary, which is the ubiquitous language a DDD codebase is built on: `underwrite`, `accrue`, `endorse`, `reinstate`. A real lexicon is the right source.

   But membership in a lexicon answers the wrong question. In WordNet `name`, `file`, `type`, `state`, `value`, `order`, `index`, `cost`, `price`, `label` and `title` are all verbs, so a membership test flags `@property def name`, the most common property in Python. **Dominance is the question; membership is not.** Is this lemma *predominantly* a verb?

   So: `P(VERB | lemma)`, derived offline and shipped as package data.

   - **Primary source**, a Universal Dependencies English treebank (EWT, GUM). Gold POS annotations, frequency-weighted, permissively licensed, small enough to vendor the derivation input.
   - **Tail fallback**, WordNet, for lemmas a 250k-token treebank never contains. `underwrite` and `accrue` are expected to be verb-only there, which is a cheap high-precision test. *Expected* is the right word: neither `nltk` nor `wn` was installed when this was written, so the claim is a prediction for the build to check.
   - **Unknown lemma produces no finding**, the same rule §3 applies to return types.

   `tools/build_verb_table.py` derives `src/namelint/data/verb_pos.json` and records the source corpus and its version, so "derived from UD English-EWT r2.14" stays checkable. The threshold on `P(VERB)` is one more number for §6 to set. The runtime stays dependency-free, because the lexicon is a build input.
3. Does `NAM101` have a false-positive class around helper functions in test modules (`make_user`, `assert_ok`)? Those are not tests and must not be flagged. The check may need to be "a function in a test module that contains an assertion and is not named `test_*`".

## 8b. Second corpus run (2026-10-15)

The four remaining checks, measured over the same nine projects before any allowlist. Findings were read by hand, informally; `calibration/sample.md` holds the seeded sample still to adjudicate formally.

- **`NAM104` as first specified** (bool under a non-predicate name) fired 9 times, none genuine: `check_length`, `takes_value`, `from_file`. Replaced by the rule the user set: if the verb implies a return, return something; if it does not, return nothing. The verb lists hold only verbs the corpus shows to be one-sided (`get_` returns in 916 of 921 public functions, `reset_` returns nothing in 56 of 59).
- **`NAM105`**: 28 findings, about 3 false (protocol `find_spec` fakes, `to_required` as a state transition). An explicit `return None` counts as a value, which removed importlib's `get_source()` family. click's 8 `format_*(ctx, formatter)` methods write into the formatter they are given, so they need allowlisting.
- **`NAM104`**: about half of a sample of 30 genuine. The rest are noun or adjective readings (`set_validator`, `close_to_zero_less`), copy-and-update APIs (rich's `update_width`), and status messages (idlelib's `set_break` returning `msg`).
- **`NAM102`**: at a verb share of 0.5, 25 findings and about 4 genuine; `drive`, `stem`, `handle`, `start` are ordinary nouns. At 0.9, 12 findings and 4 genuine (`get_unique_child`, three `raise_*`). The rest are noun compounds whose first word is nearly always a verb (`verify_mode`, `include_dir`, `fail_reason`), which no word-level lexicon can tell apart. It stays, leaning on the allowlist.
- **`NAM108`**: 217 findings at first, mostly `TestFoo.test_foo` and tkinter's `Wm.wm_*`. Skipping test classes, private methods, exact-name protocol methods and classes with three or more repeats leaves 37, about 14 genuine. Most of the rest name another instance of the same type (`Style.background_style`, `Text.append_text`): the allowlist's job.

Departures from §8.2: the verb table is keyed by word form, not lemma, so `closed` and `cached` (participles, used as adjectives) never count; only `VB`/`VBP` tags count as verb uses. The WordNet tail fallback is not built: neither `nltk` nor `wn` is available, and a word the treebanks do not know is silence anyway.

## 9. First milestone

The three whose evidence is unambiguous (`NAM101`, `NAM106`, `NAM107`), plus the CLI with `--json` and `--stats`, plus the corpus run. `NAM102` was in this milestone until the verb vocabulary turned out to need a derived lexicon and a threshold (§8.2); it now sits with the checks that wait on a measurement. The four that depend on return-type reading (`NAM103`, `NAM104`, `NAM105`) follow once the first four have been calibrated, since they share the type-reading machinery and should be built against known-good measurement. `NAM108` is last, because it is the one most likely to be cut.
