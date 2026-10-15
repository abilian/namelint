"""NAM106: a name that promises a cheap lookup and does I/O.

`get` is a contract in Python (`dict.get`, `getattr`, `os.environ.get`),
so the defect is the broken promise rather than a vague verb. A `get_`
that stays in memory is correct and must stay silent.
"""

from __future__ import annotations

from pathlib import Path

from namelint.visitor import lint_source

MODULE = Path("src/app/users.py")


def findings(source: str):
    return lint_source(source, MODULE)


def codes(source: str) -> list[str]:
    return [found.code for found in findings(source)]


def test_opening_a_file_is_reported() -> None:
    source = "def get_config(path):\n    return open(path).read()\n"

    assert codes(source) == ["NAM106"]


def test_an_http_call_is_reported() -> None:
    source = (
        "import httpx\n\ndef get_user(uid):\n    return httpx.get(f'/u/{uid}').json()\n"
    )

    assert codes(source) == ["NAM106"]


def test_a_database_cursor_is_reported() -> None:
    source = "def get_rows(cursor):\n    cursor.execute('select 1')\n    return cursor.fetchall()\n"

    assert codes(source) == ["NAM106"]


def test_a_path_read_is_reported() -> None:
    source = "def get_text(path):\n    return path.read_text()\n"

    assert codes(source) == ["NAM106"]


def test_an_in_memory_accessor_stays_silent() -> None:
    """The case that makes banning `get` wrong."""
    source = "def get_cached(key):\n    return _cache[key]\n"

    assert codes(source) == []


def test_a_dict_get_inside_the_body_is_not_io() -> None:
    source = "def get_name(record):\n    return record.get('name')\n"

    assert codes(source) == []


def test_a_differently_named_function_doing_io_is_not_this_rule() -> None:
    """`fetch_user` opening a socket is correctly named."""
    source = "import httpx\n\ndef fetch_user(uid):\n    return httpx.get('/u').json()\n"

    assert codes(source) == []


def test_the_evidence_names_the_call() -> None:
    """A finding that says 'performs I/O' cannot be argued with."""
    source = "import httpx\n\ndef get_user(uid):\n    return httpx.get('/u').json()\n"

    assert findings(source)[0].evidence == "calls httpx.get"


def test_io_inside_a_nested_function_does_not_count() -> None:
    source = (
        "def get_loader(path):\n"
        "    def load():\n        return open(path).read()\n"
        "    return load\n"
    )

    assert codes(source) == []
