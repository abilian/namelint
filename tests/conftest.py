"""pytest configuration: markers applied by test directory.

Test Pyramid Structure:
- tests/a_unit/        - Unit tests (fast, isolated, no I/O)
- tests/b_integration/ - Integration tests (component interactions, file I/O)

Run specific test types:
    uv run pytest -m unit              # Run only unit tests
    uv run pytest -m integration       # Run only integration tests
    uv run pytest tests/a_unit/        # Run by directory
"""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):  # noqa: ARG001 — pytest matches hook arguments by name, so `config` cannot be renamed
    """Automatically apply markers based on test directory."""
    for item in items:
        # Get the path relative to tests/
        test_path = Path(item.fspath)
        parts = test_path.parts

        # Apply markers based on directory
        if "a_unit" in parts:
            item.add_marker(pytest.mark.unit)
        elif "b_integration" in parts:
            item.add_marker(pytest.mark.integration)
