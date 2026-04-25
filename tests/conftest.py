"""Pytest configuration for the Virtual integration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture(autouse=True)
def clean_virtual_yaml(hass: object) -> None:
    """Remove YAML storage between tests."""
    Path(hass.config.path("virtual.yaml")).unlink(missing_ok=True)
