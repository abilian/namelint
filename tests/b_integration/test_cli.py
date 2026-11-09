"""The CLI over real files: exit codes, selection, output shapes."""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

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

    assert main(["check", str(tmp_path)]) == EXIT_FINDINGS
    assert "NAM106" in capsys.readouterr().out


def test_linting_needs_the_check_command(tmp_path: Path) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main([str(tmp_path)]) == EXIT_ERROR


def test_clean_exits_zero_and_says_nothing(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", CLEAN)

    assert main(["check", str(tmp_path)]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_a_directory_is_walked(tmp_path: Path, capsys) -> None:
    write(tmp_path, "pkg/sub/app.py", DIRTY)

    main(["check", str(tmp_path)])

    assert "pkg/sub/app.py" in capsys.readouterr().out


def test_a_virtualenv_is_skipped(tmp_path: Path, capsys) -> None:
    """Otherwise every run lints its target's dependencies."""
    write(tmp_path, ".venv/lib/app.py", DIRTY)

    assert main(["check", str(tmp_path)]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_select_narrows_to_one_check(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main(["check", str(tmp_path), "--select", "NAM107"]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_ignore_drops_one_check(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main(["check", str(tmp_path), "--ignore", "NAM106"]) == EXIT_CLEAN
    assert capsys.readouterr().out == ""


def test_selecting_nothing_is_an_error(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert (
        main(["check", str(tmp_path), "--select", "NAM106", "--ignore", "NAM106"])
        == EXIT_ERROR
    )
    assert "no checks enabled" in capsys.readouterr().err


def test_json_output_is_one_object_per_line(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main(["check", str(tmp_path), "--output-format", "json"])
    record = json.loads(capsys.readouterr().out.strip())

    assert record["code"] == "NAM106"
    assert record["name"] == "get_user"
    assert record["evidence"] == "calls httpx.get"
    assert record["hint"].startswith("get_ promises a cheap lookup")


def test_stats_reports_a_rate_per_thousand(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main(["check", str(tmp_path), "--stats"])
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

    assert main(["check", str(tmp_path)]) == EXIT_FINDINGS
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

    assert main(["check", str(tmp_path)]) == EXIT_FINDINGS
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

    assert main(["check", "src"]) == EXIT_FINDINGS
    out = capsys.readouterr().out
    assert "user_id" in out
    assert "user_name" not in out


def test_an_allowlist_entry_takes_wildcards(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM108 = ["user_*"]')

    assert main(["check", "src"]) == EXIT_CLEAN


def test_an_allowlist_entry_only_covers_its_code(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM106 = ["user_*"]')

    assert main(["check", "src"]) == EXIT_FINDINGS


def test_an_unknown_code_in_the_allowlist_is_an_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM999 = ["x"]')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_json_carries_the_qualified_name(tmp_path: Path, monkeypatch, capsys) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    monkeypatch.chdir(tmp_path)

    main(["check", "src", "--output-format", "json"])

    first = json.loads(capsys.readouterr().out.splitlines()[0])
    assert first["qualname"] == "User.user_name"


def test_an_unknown_code_is_rejected(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", CLEAN)

    assert main(["check", str(tmp_path), "--ignore", "NAM999"]) == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_stats_counts_only_the_functions_checked(tmp_path: Path, capsys) -> None:
    """A closure is never checked, so it must not dilute the rate."""
    write(tmp_path, "app.py", "def outer():\n    def inner():\n        pass\n")

    main(["check", str(tmp_path), "--stats"])

    assert "functions scanned: 1" in capsys.readouterr().out


def test_no_allowlist_reports_everything(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path, "src/user.py", ALLOWLISTED)
    allow(tmp_path, monkeypatch, 'NAM108 = ["*"]')

    assert main(["check", "src"]) == EXIT_CLEAN
    assert main(["check", "src", "--no-allowlist"]) == EXIT_FINDINGS


GENERATOR = "def collect_entry(root):\n    yield root\n"


def test_an_opt_in_check_is_off_by_default(tmp_path: Path) -> None:
    write(tmp_path, "app.py", GENERATOR)

    assert main(["check", str(tmp_path)]) == EXIT_CLEAN


def test_an_opt_in_check_runs_when_selected(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", GENERATOR)

    assert main(["check", str(tmp_path), "--select", "NAM107"]) == EXIT_FINDINGS
    assert "NAM107" in capsys.readouterr().out


def test_version_comes_from_the_package_metadata(capsys) -> None:
    assert main(["--version"]) == EXIT_CLEAN
    assert capsys.readouterr().out.strip() == f"namelint {metadata.version('namelint')}"


def test_default_output_groups_findings_under_their_file(
    tmp_path: Path, capsys
) -> None:
    path = write(tmp_path, "app.py", DIRTY + DIRTY.replace("get_user", "get_team"))

    main(["check", str(tmp_path)])

    out = capsys.readouterr().out
    assert out.count(str(path)) == 1
    assert "  4:1  NAM106  get_user performs I/O (calls httpx.get)\n" in out
    assert "hint:" not in out
    assert out.endswith("2 findings in 1 file\n")


def test_full_output_puts_the_hint_under_the_finding(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main(["check", str(tmp_path), "--output-format", "full"])

    assert "hint: get_ promises a cheap lookup" in capsys.readouterr().out


def test_concise_output_is_one_editor_line_per_finding(tmp_path: Path, capsys) -> None:
    path = write(tmp_path, "app.py", DIRTY)

    main(["check", str(tmp_path), "--output-format", "concise"])

    assert capsys.readouterr().out == (
        f"{path}:4:1: NAM106 get_user performs I/O (calls httpx.get);"
        " get_ promises a cheap lookup, use fetch_, load_ or read_\n"
    )


def test_github_output_is_one_annotation_per_finding(tmp_path: Path, capsys) -> None:
    """A comma in a path would end the `file` property, so it is escaped."""
    path = write(tmp_path, "a,b.py", DIRTY)
    escaped = str(path).replace(",", "%2C")

    main(["check", str(tmp_path), "--output-format", "github"])

    assert capsys.readouterr().out == (
        f"::error title=namelint NAM106,file={escaped},line=4,col=1::"
        "NAM106 get_user performs I/O (calls httpx.get);"
        " get_ promises a cheap lookup, use fetch_, load_ or read_\n"
    )


def test_exit_zero_reports_but_does_not_fail(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main(["check", str(tmp_path), "--exit-zero"]) == EXIT_CLEAN
    assert "NAM106" in capsys.readouterr().out


def test_show_settings_prints_the_resolved_settings_and_lints_nothing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write(tmp_path, "app.py", DIRTY)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.namelint]\nignore = ["NAM108"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    assert main(["check", "--show-settings"]) == EXIT_CLEAN

    out = capsys.readouterr().out
    assert out.startswith(f"settings: {tmp_path / 'pyproject.toml'}\n")
    assert '"NAM106"' in out
    assert '"NAM108"' not in out
    assert "get_user" not in out


def test_explain_follows_the_report_once_per_check(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY + DIRTY.replace("get_user", "get_team"))

    assert main(["check", str(tmp_path), "--explain"]) == EXIT_FINDINGS

    out = capsys.readouterr().out
    report, _, explained = out.partition("2 findings in 1 file\n")
    assert "get_team" in report
    assert explained.count("NAM106: a get_ that performs I/O") == 1
    assert "The caller of a `get_`" in explained  # the senior section


def test_explain_takes_a_level(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    main(["check", str(tmp_path), "--explain", "--level", "junior"])

    assert "In Python, `get` means a cheap lookup" in capsys.readouterr().out


def test_level_without_explain_is_an_error(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert main(["check", str(tmp_path), "--level", "junior"]) == EXIT_ERROR
    assert "--level needs --explain" in capsys.readouterr().err


def test_explain_refuses_machine_formats(tmp_path: Path, capsys) -> None:
    write(tmp_path, "app.py", DIRTY)

    assert (
        main(["check", str(tmp_path), "--explain", "--output-format", "json"])
        == EXIT_ERROR
    )
    assert capsys.readouterr().out == ""
