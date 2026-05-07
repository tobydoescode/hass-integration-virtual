"""Tests for translation coverage."""

from __future__ import annotations

import json
from pathlib import Path


def test_options_flow_translations_cover_all_steps() -> None:
    """Options flow steps have labels in the bundled translation files."""
    strings = json.loads(Path("custom_components/virtual/strings.json").read_text())
    translations = json.loads(Path("custom_components/virtual/translations/en.json").read_text())

    expected_steps = {
        "init",
        "edit_device",
        "add_entity_type",
        "add_entity",
        "select_entity",
        "edit_entity",
        "remove_entity",
        "confirm_remove_entity",
    }

    assert expected_steps <= set(strings["options"]["step"])
    assert expected_steps <= set(translations["options"]["step"])
