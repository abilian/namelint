"""The CLI over real files: exit codes, selection, output shapes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from namelint.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main

DIRTY = "import httpx\n\n\ndef get_user(uid):\n    return httpx.get('/u').json()\n"
CLEAN = "def fetch_user(uid):\n    return 1\n"


def write(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_findings_exit_one(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path)]) == EXIT_FINDINGS
    assert "NAM106" in capsys.readouterr().out


def test_clean_exits_zero_and_says_nothing(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", CLEAN)

    assert main([str(tmp_path)]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_a_directory_is_walked(tmp_path: Path, capsys) -> None:
    write(tmp_path, "pkg/sub/app.py", DIRTY)

    main([str(tmp_path)])

    assert "pkg/sub/app.py" in capsys.readouterr().out


def test_a_virtualenv_is_skipped(tmp_path: Path, capsys) -> None:
    """Otherwise every run lints its target's dependencies."""
    write(tmp_path, ".venv/lib/app.py", DIRTY)

    assert main([str(tmp_path)]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_select_narrows_to_one_check(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path), "--select", "NAM107"]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_ignore_drops_one_check(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path), "--ignore", "NAM106"]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_selecting_nothing_is_an_error(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert (
        main([str(tmp_path), "--select", "NAM106", "--ignore", "NAM106"]) == EXIT_ERROR
    )
    assert "no checks enabled" in capsys.readouterr().err


def test_json_output_is_one_object_per_line(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main([str(tmp_path), "--json"])
    record = json.loads(capsys.readouterr().out.strip())

    assert record["code"] == "NAM106"
    assert record["name"] == "get_user"
    assert record["evidence"] == "calls httpx.get"


def test_stats_reports_a_rate_per_thousand(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main([str(tmp_path), "--stats"])
    out = capsys.readouterr().out

    assert "functions scanned: 1" in out
    assert "NAM106" in out
    assert "per 1000" in out


def test_an_unparsable_file_is_skipped_rather_than_fatal(
    tmp_path: Path, capsys
) -> None:
    """A corpus run meets Python 2 and vendored junk; one bad file must
    not end the run."""
    write(tmp_path, "broken.py", "def (:\n")
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path)]) == EXIT_FINDINGS
    captured = capsys.readouterr()

    assert "broken.py: skipped" in captured.err
    assert "NAM106" in captured.out


def test_a_file_raising_valueerror_is_skipped(tmp_path: Path, capsys) -> None:
    """`ast.parse` raises more than `SyntaxError`.

    CPython's own test suite carries fixtures that raise `ValueError`,
    and the first corpus run died on one after 23,000 functions.
    """
    write(tmp_path, "weird.py", "x = 1\x00\n")
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path)]) == EXIT_FINDINGS
    assert "NAM106" in capsys.readouterr().out


ALLOWLISTED = (
    "class User:\n"
    "    def user_name(self):\n        return self.first\n"
    "    def user_id(self):\n        return self.id\n"
)


def allow(tmp_path: Path, monkeypatch, body: str) -> None:
    write(tmp_path, "pyproject.toml", f"[tool.namelint.allow]\n{body}\n")
    monkeypatch.chdir(tmp_path)


def test_an_allowlisted_method_is_not_reported(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM108 = ["User.user_name"]')

    assert main(["src"]) == EXIT_FINDINGS
    out = capsys.readouterr().out
    assert "user_id" in out
    assert "user_name" not in out


def test_an_allowlist_entry_takes_wildcards(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM108 = ["user_*"]')

    assert main(["src"]) == EXIT_CLEAN


def test_an_allowlist_entry_only_covers_its_code(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM106 = ["user_*"]')

    assert main(["src"]) == EXIT_FINDINGS


def test_an_unknown_code_in_the_allowlist_is_an_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM999 = ["x"]')

    assert main(["src"]) == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_json_carries_the_qualified_name(tmp_path: Path, monkeypatch, capsys) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    monkeypatch.chdir(tmp_path)

    main(["src", "--json"])

    first = json.loads(capsys.readouterr().out.splitlines()[0])
    assert first["qualname"] == "User.user_name"


def test_an_unknown_code_is_rejected(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", CLEAN)

    with pytest.raises(SystemExit) as exited:
        main([str(tmp_path), "--ignore", "NAM999"])

    assert exited.value.code == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_stats_counts_only_the_functions_checked(tmp_path: Path, capsys) -> None:
    """A closure is never checked, so it must not dilute the rate."""
    write(tmp_path, "app.py", "def outer():\n    def inner():\n        pass\n")

    main([str(tmp_path), "--stats"])

    assert "functions scanned: 1" in capsys.readouterr().out


def test_no_allowlist_reports_everything(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM108 = ["*"]')

    assert main(["src"]) == EXIT_CLEAN
    assert main(["src", "--no-allowlist"]) == EXIT_FINDINGS


GENERATOR = "def collect_entry(root):\n    yield root\n"


def test_an_opt_in_check_is_off_by_default(tmp_path: Path) -> None:
    write(tmp_path, "app.py", GENERATOR)

    assert main([str(tmp_path)]) == EXIT_CLEAN


def test_an_opt_in_check_runs_when_selected(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", GENERATOR)

    assert main([str(tmp_path), "--select", "NAM107"]) == EXIT_FINDINGS
    assert "NAM107" in capsys.readouterr().out
