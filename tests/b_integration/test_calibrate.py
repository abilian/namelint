"""`tools/calibrate.py`: a namelint failure must never read as "no findings"."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parents[2] / "tools" / "calibrate.py"


def load_calibrate(monkeypatch):
    """Import the script by path; its dataclasses need it in `sys.modules`."""
    spec = importlib.util.spec_from_file_location("calibrate", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "calibrate", module)
    spec.loader.exec_module(module)
    return module


def test_stats_without_a_function_count_is_an_error(monkeypatch) -> None:
    calibrate = load_calibrate(monkeypatch)

    with pytest.raises(calibrate.CalibrationError):
        calibrate.functions_from_stats("")


def test_stats_with_a_function_count_is_read(monkeypatch) -> None:
    calibrate = load_calibrate(monkeypatch)

    assert calibrate.functions_from_stats("functions scanned: 42\n") == 42
