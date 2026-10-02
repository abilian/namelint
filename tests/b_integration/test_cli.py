"""The CLI over real files: exit codes, selection, output shapes."""

from __future__ import annotations

import json
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
