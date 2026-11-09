"""`[tool.namelint]` in `pyproject.toml`: settings the command line can override."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from namelint.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main

# One NAM106 and one NAM104.
SOURCE = (
    "import httpx\n\n\ndef get_user(uid):\n    return httpx.get('/u')\n\n\n"
    "def set_shape(lines):\n    return lines\n"
)


def project(tmp_path: Path, monkeypatch, settings: str) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        f"[tool.namelint]\n{settings}\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)


def test_select_in_the_settings_narrows_the_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'select = ["NAM104"]')

    main(["check", "src"])

    out = capsys.readouterr().out
    assert "NAM104" in out
    assert "NAM106" not in out


def test_select_on_the_command_line_wins(tmp_path: Path, monkeypatch, capsys) -> None:
    project(tmp_path, monkeypatch, 'select = ["NAM104"]')

    main(["check", "src", "--select", "NAM106"])

    out = capsys.readouterr().out
    assert "NAM106" in out
    assert "NAM104" not in out


def test_ignore_from_both_places_adds_up(tmp_path: Path, monkeypatch) -> None:
    project(tmp_path, monkeypatch, 'ignore = ["NAM104"]')

    assert main(["check", "src", "--ignore", "NAM106"]) == EXIT_CLEAN


def test_exclude_skips_a_matching_directory(tmp_path: Path, monkeypatch) -> None:
    project(tmp_path, monkeypatch, 'exclude = ["src"]')

    assert main(["check", "."]) == EXIT_CLEAN


def test_a_file_named_on_the_command_line_is_never_excluded(
    tmp_path: Path, monkeypatch
) -> None:
    project(tmp_path, monkeypatch, 'exclude = ["src"]')

    assert main(["check", "src/app.py"]) == EXIT_FINDINGS


def test_output_format_comes_from_the_settings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'output-format = "concise"')

    main(["check", "src"])

    assert capsys.readouterr().out.startswith("src/app.py:4:1: NAM106")


def test_an_unknown_key_is_an_error(tmp_path: Path, monkeypatch, capsys) -> None:
    """A typo must never pass for a setting that was applied."""
    project(tmp_path, monkeypatch, 'selct = ["NAM104"]')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "unknown key 'selct'" in capsys.readouterr().err


def test_an_unknown_output_format_is_an_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'output-format = "pretty"')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "output-format" in capsys.readouterr().err


def test_an_unknown_code_in_the_settings_is_an_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'ignore = ["NAM999"]')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_per_file_ignores_skip_a_code_in_matching_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'per-file-ignores = { "src/*" = ["NAM106"] }')

    main(["check", "src"])

    out = capsys.readouterr().out
    assert "NAM104" in out
    assert "NAM106" not in out


def test_patterns_are_relative_to_the_project_root(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """`src/*` must mean the same when namelint runs from inside `src`."""
    project(tmp_path, monkeypatch, 'per-file-ignores = { "src/*" = ["NAM106"] }')
    monkeypatch.chdir(tmp_path / "src")

    main(["check", "."])

    assert "NAM106" not in capsys.readouterr().out


def test_an_unknown_code_in_per_file_ignores_is_an_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, 'per-file-ignores = { "src/*" = ["NAM999"] }')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "NAM999" in capsys.readouterr().err


def test_force_exclude_applies_to_a_named_file(tmp_path: Path, monkeypatch) -> None:
    project(tmp_path, monkeypatch, 'exclude = ["src"]')

    assert main(["check", "--force-exclude", "src/app.py"]) == EXIT_CLEAN


GIT = shutil.which("git")
needs_git = pytest.mark.skipif(GIT is None, reason="needs git")


def git_project(tmp_path: Path, monkeypatch, settings: str) -> None:
    project(tmp_path, monkeypatch, settings)
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "app.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / ".gitignore").write_text("generated/\n", encoding="utf-8")
    assert GIT is not None
    subprocess.run([GIT, "init", "-q", str(tmp_path)], check=True)  # noqa: S603 (fixed arguments, no shell)


@needs_git
def test_files_git_ignores_are_skipped(tmp_path: Path, monkeypatch, capsys) -> None:
    git_project(tmp_path, monkeypatch, "")

    main(["check", "."])

    out = capsys.readouterr().out
    assert "src/app.py" in out  # untracked, yet not ignored
    assert "generated" not in out


@needs_git
def test_respect_gitignore_can_be_turned_off(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    git_project(tmp_path, monkeypatch, "respect-gitignore = false")

    main(["check", "."])

    assert "generated/app.py" in capsys.readouterr().out


def test_per_file_ignores_must_be_a_table(tmp_path: Path, monkeypatch, capsys) -> None:
    project(tmp_path, monkeypatch, 'per-file-ignores = ["src/*"]')

    assert main(["check", "src"]) == EXIT_ERROR
    assert "per-file-ignores must be a table" in capsys.readouterr().err
