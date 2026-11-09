"""`namelint init` and `namelint allow`: writing the allowlist.

`init` adds an empty table. With `--accept-existing`, and always for
`allow`, the linter runs and what it found is recorded as accepted. The
file they write must load back with `tomllib`, and every line outside the
`[tool.namelint.allow]` table must survive untouched.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from namelint import config
from namelint.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main

SOURCE = (
    "class User:\n"
    "    def user_name(self):\n        return self.first\n"
    "def set_shape(lines):\n    return lines\n"
)
PROJECT = '[project]\nname = "app"\n\n[tool.ruff]\nline-length = 88\n'


def project(tmp_path: Path, monkeypatch, pyproject: str | None = PROJECT) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(SOURCE, encoding="utf-8")
    if pyproject is not None:
        (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path / "pyproject.toml"


def allow_table(config: Path) -> dict:
    return tomllib.loads(config.read_text(encoding="utf-8"))["tool"]["namelint"][
        "allow"
    ]


def test_init_adds_an_empty_table_and_accepts_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    config = project(tmp_path, monkeypatch)

    assert main(["init"]) == EXIT_CLEAN

    assert allow_table(config) == {}
    assert main(["check", "src"]) == EXIT_FINDINGS


def test_init_writes_every_setting_at_its_default(tmp_path: Path, monkeypatch) -> None:
    """What `init` writes must read back as what no table at all means."""
    config_path = project(tmp_path, monkeypatch)

    main(["init"])

    assert config.load(config_path) == config.Settings(allow={}, root=tmp_path)


def test_init_refuses_an_existing_namelint_table(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, PROJECT + "\n[tool.namelint]\nignore = []\n")

    assert main(["init"]) == EXIT_ERROR
    assert "already has [tool.namelint]" in capsys.readouterr().err


def test_init_accept_existing_records_every_finding(
    tmp_path: Path, monkeypatch
) -> None:
    config = project(tmp_path, monkeypatch)

    assert main(["init", "--accept-existing", "src"]) == EXIT_CLEAN

    assert allow_table(config) == {
        "NAM104": ["set_shape"],
        "NAM108": ["User.user_name"],
    }
    assert main(["check", "src"]) == EXIT_CLEAN


def test_init_keeps_the_rest_of_the_file(tmp_path: Path, monkeypatch) -> None:
    config = project(tmp_path, monkeypatch)

    main(["init", "--accept-existing", "src"])

    assert config.read_text(encoding="utf-8").startswith(PROJECT)


def test_init_creates_pyproject_when_there_is_none(tmp_path: Path, monkeypatch) -> None:
    config = project(tmp_path, monkeypatch, pyproject=None)

    assert main(["init"]) == EXIT_CLEAN

    assert allow_table(config) == {}


def test_accept_existing_defaults_to_the_current_directory(
    tmp_path: Path, monkeypatch
) -> None:
    config = project(tmp_path, monkeypatch)

    main(["init", "--accept-existing"])

    assert "NAM104" in allow_table(config)


def test_init_refuses_an_existing_allowlist(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, PROJECT + "\n[tool.namelint.allow]\n")

    assert main(["init"]) == EXIT_ERROR
    assert "namelint allow" in capsys.readouterr().err


def test_allow_adds_to_existing_entries(tmp_path: Path, monkeypatch) -> None:
    config = project(
        tmp_path,
        monkeypatch,
        '[tool.namelint.allow]\nNAM104 = ["close_to_*"]\n\n[tool.ruff]\nline-length = 88\n',
    )

    assert main(["allow", "src"]) == EXIT_CLEAN

    text = config.read_text(encoding="utf-8")
    assert allow_table(config) == {
        "NAM104": ["close_to_*", "set_shape"],
        "NAM108": ["User.user_name"],
    }
    assert text.endswith("[tool.ruff]\nline-length = 88\n")


def test_allow_twice_changes_nothing(tmp_path: Path, monkeypatch) -> None:
    config = project(tmp_path, monkeypatch)
    main(["allow", "src"])
    first = config.read_text(encoding="utf-8")

    main(["allow", "src"])

    assert config.read_text(encoding="utf-8") == first


def test_allow_records_only_the_selected_code(tmp_path: Path, monkeypatch) -> None:
    config = project(tmp_path, monkeypatch)

    main(["allow", "--select", "NAM108", "src"])

    assert allow_table(config) == {"NAM108": ["User.user_name"]}
    assert main(["check", "src"]) == EXIT_FINDINGS


def test_allow_refuses_an_allowlist_it_cannot_rewrite(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project(tmp_path, monkeypatch, '[tool.namelint]\nallow = { NAM104 = ["x"] }\n')

    assert main(["allow", "src"]) == EXIT_ERROR
    assert "edit it by hand" in capsys.readouterr().err


def test_entries_are_sorted_for_stable_diffs(tmp_path: Path, monkeypatch) -> None:
    config = project(tmp_path, monkeypatch)
    names = ["set_e", "set_d", "set_c", "set_b", "set_a"]
    (tmp_path / "src" / "app.py").write_text(
        "".join(f"def {name}():\n    return 1\n" for name in names), encoding="utf-8"
    )

    main(["init", "--accept-existing", "src"])

    assert allow_table(config) == {"NAM104": sorted(names)}


def test_escaped_entries_survive_a_rewrite(tmp_path: Path, monkeypatch) -> None:
    """`"a\\\\b"` is the pattern a-backslash-b; written back unescaped it
    would become a-backspace-b."""
    config = project(
        tmp_path, monkeypatch, '[tool.namelint.allow]\nNAM104 = ["a\\\\b"]\n'
    )

    main(["allow", "src"])

    assert "a\\b" in allow_table(config)["NAM104"]


def test_prune_removes_entries_that_match_nothing(tmp_path: Path, monkeypatch) -> None:
    config_path = project(
        tmp_path,
        monkeypatch,
        '[tool.namelint.allow]\nNAM104 = ["set_shape", "gone_function"]\n'
        'NAM105 = ["also_gone"]\n',
    )

    main(["allow", "--prune", "src"])

    assert allow_table(config_path) == {
        "NAM104": ["set_shape"],
        "NAM108": ["User.user_name"],
    }


def test_prune_keeps_the_entries_of_a_code_that_did_not_run(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = project(
        tmp_path, monkeypatch, '[tool.namelint.allow]\nNAM108 = ["Old.stale"]\n'
    )

    main(["allow", "--prune", "--select", "NAM104", "src"])

    assert allow_table(config_path) == {
        "NAM104": ["set_shape"],
        "NAM108": ["Old.stale"],
    }


def test_prune_keeps_a_wildcard_that_still_matches(tmp_path: Path, monkeypatch) -> None:
    config_path = project(
        tmp_path, monkeypatch, '[tool.namelint.allow]\nNAM104 = ["set_*"]\n'
    )

    main(["allow", "--prune", "--select", "NAM104", "src"])

    assert allow_table(config_path) == {"NAM104": ["set_*"]}
