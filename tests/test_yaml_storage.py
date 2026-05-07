"""Tests for Virtual YAML import/export helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual import async_setup
from custom_components.virtual.const import (
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_TYPE,
    CONF_INITIAL_VALUE,
    CONF_KEY,
    CONF_OPTIONS,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SWITCH,
)
from custom_components.virtual.yaml_storage import (
    YAML_FILE_NAME,
    async_export_entries_to_yaml,
    async_import_yaml_to_entries,
    async_load_yaml_devices,
)


def _yaml_device() -> dict:
    """Return a YAML-backed virtual device definition."""
    return {
        CONF_NAME: "YAML Device",
        CONF_DEVICE_ID: "virtual_yaml",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_ENTITIES: [
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "YAML Switch",
                CONF_KEY: "yaml_switch",
                CONF_INITIAL_VALUE: True,
            }
        ],
    }


async def test_load_yaml_devices_returns_empty_when_file_is_missing(
    hass: HomeAssistant,
) -> None:
    """Missing YAML file means no YAML-backed devices."""
    Path(hass.config.path(YAML_FILE_NAME)).unlink(missing_ok=True)

    assert await async_load_yaml_devices(hass) == []


async def test_yaml_export_and_load_round_trips_entry_data(hass: HomeAssistant) -> None:
    """Exported YAML loads back to the same device data."""
    device = _yaml_device()

    await async_export_entries_to_yaml(hass, [device])

    yaml_path = Path(hass.config.path(YAML_FILE_NAME))
    assert yaml_path.exists()
    assert await async_load_yaml_devices(hass) == [device]


async def test_setup_imports_yaml_devices_as_config_entries(hass: HomeAssistant) -> None:
    """Initial integration setup imports YAML devices into config entries."""
    await async_export_entries_to_yaml(hass, [_yaml_device()])

    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].source == SOURCE_IMPORT
    assert entries[0].unique_id == "virtual_yaml"
    assert entries[0].title == "YAML Device"
    assert entries[0].data == _yaml_device()
    assert hass.states.get("switch.yaml_switch") is not None


async def test_yaml_import_updates_existing_entry(hass: HomeAssistant) -> None:
    """Manual YAML import updates an existing virtual entry with the same device id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="YAML Device",
        unique_id="virtual_yaml",
        data=_yaml_device(),
    )
    entry.add_to_hass(hass)

    updated = {
        **_yaml_device(),
        CONF_NAME: "Renamed YAML Device",
    }
    await async_export_entries_to_yaml(hass, [updated])

    changed_entries = await async_import_yaml_to_entries(hass, reload_entries=False)

    assert changed_entries == hass.config_entries.async_entries(DOMAIN)
    assert changed_entries[0].title == "Renamed YAML Device"
    assert changed_entries[0].data == updated


async def test_yaml_import_preserves_entries_absent_from_yaml(hass: HomeAssistant) -> None:
    """YAML import does not remove Home Assistant entries absent from YAML."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="UI Device",
        unique_id="virtual_ui",
        data={
            CONF_NAME: "UI Device",
            CONF_DEVICE_ID: "virtual_ui",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)
    await async_export_entries_to_yaml(hass, [_yaml_device()])

    await async_import_yaml_to_entries(hass, reload_entries=False)

    assert entry in hass.config_entries.async_entries(DOMAIN)
    assert entry.data[CONF_DEVICE_ID] == "virtual_ui"


async def test_yaml_import_warns_about_entries_absent_from_yaml(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """YAML import warns about Virtual entries not managed by YAML."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="UI Device",
        unique_id="virtual_ui",
        data={
            CONF_NAME: "UI Device",
            CONF_DEVICE_ID: "virtual_ui",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)
    await async_export_entries_to_yaml(hass, [_yaml_device()])

    with caplog.at_level(logging.WARNING, logger="custom_components.virtual.yaml_storage"):
        await async_import_yaml_to_entries(hass, reload_entries=False)

    assert "Virtual device virtual_ui is not managed by virtual.yaml" in caplog.text


async def test_yaml_import_preserves_and_warns_about_entities_absent_from_yaml(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """YAML import keeps existing entities not managed by YAML."""
    ui_entity = {
        CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
        CONF_NAME: "UI Switch",
        CONF_KEY: "ui_switch",
        CONF_INITIAL_VALUE: False,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="YAML Device",
        unique_id="virtual_yaml",
        data={
            **_yaml_device(),
            CONF_ENTITIES: [_yaml_device()[CONF_ENTITIES][0], ui_entity],
        },
    )
    entry.add_to_hass(hass)
    yaml_device = {
        **_yaml_device(),
        CONF_ENTITIES: [
            {
                **_yaml_device()[CONF_ENTITIES][0],
                CONF_INITIAL_VALUE: False,
            }
        ],
    }
    await async_export_entries_to_yaml(hass, [yaml_device])

    with caplog.at_level(logging.WARNING, logger="custom_components.virtual.yaml_storage"):
        await async_import_yaml_to_entries(hass, reload_entries=False)

    assert entry.data[CONF_ENTITIES] == [yaml_device[CONF_ENTITIES][0], ui_entity]
    assert "Virtual entity virtual_yaml/ui_switch is not managed by virtual.yaml" in caplog.text


async def test_entry_setup_imports_yaml_before_platform_setup(hass: HomeAssistant) -> None:
    """Reloading or setting up an entry imports YAML before entities are created."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Old YAML Device",
        unique_id="virtual_yaml",
        data={
            CONF_NAME: "Old YAML Device",
            CONF_DEVICE_ID: "virtual_yaml",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)
    await async_export_entries_to_yaml(hass, [_yaml_device()])

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.title == "YAML Device"
    assert entry.data == _yaml_device()
    assert hass.states.get("switch.yaml_switch") is not None


async def test_manual_yaml_import_reloads_added_entity_state(
    hass: HomeAssistant,
) -> None:
    """Manual YAML import reloads changed entries so added entities appear."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="YAML Device",
        unique_id="virtual_yaml",
        data={**_yaml_device(), CONF_ENTITIES: []},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("switch.yaml_switch") is None
    await async_export_entries_to_yaml(hass, [_yaml_device()])

    await async_import_yaml_to_entries(hass)
    await hass.async_block_till_done()

    assert hass.states.get("switch.yaml_switch").state == "on"


async def test_load_yaml_devices_rejects_invalid_shape(hass: HomeAssistant) -> None:
    """Invalid YAML structure raises a validation error."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text("devices: not-a-list\n")

    with pytest.raises(ValueError, match="devices"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_devices_rejects_duplicate_device_ids(hass: HomeAssistant) -> None:
    """YAML devices must have unique device IDs."""
    await async_export_entries_to_yaml(hass, [_yaml_device(), _yaml_device()])

    with pytest.raises(ValueError, match="duplicate_device_id"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_devices_rejects_duplicate_entity_keys(hass: HomeAssistant) -> None:
    """YAML entity keys must be unique within a device."""
    device = _yaml_device()
    device[CONF_ENTITIES].append({**device[CONF_ENTITIES][0], CONF_NAME: "Duplicate"})
    await async_export_entries_to_yaml(hass, [device])

    with pytest.raises(ValueError, match="duplicate_entity_key"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_devices_rejects_invalid_type_specific_entity(
    hass: HomeAssistant,
) -> None:
    """YAML import validates type-specific entity fields before storage."""
    device = {
        **_yaml_device(),
        CONF_ENTITIES: [
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "Mode",
                CONF_KEY: "mode",
                CONF_OPTIONS: ["auto", "heat"],
                CONF_INITIAL_VALUE: "cool",
            }
        ],
    }
    await async_export_entries_to_yaml(hass, [device])

    with pytest.raises(ValueError, match="invalid_option"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_devices_returns_empty_when_data_is_none(
    hass: HomeAssistant,
) -> None:
    """YAML file with no content returns empty list."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text("")
    assert await async_load_yaml_devices(hass) == []


async def test_load_yaml_devices_rejects_non_mapping_root(
    hass: HomeAssistant,
) -> None:
    """YAML file with non-mapping root raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text("- item\n")
    with pytest.raises(ValueError, match="must contain a mapping"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_non_dict_device(hass: HomeAssistant) -> None:
    """YAML device entry that is not a mapping raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text("devices:\n  - not-a-mapping\n")
    with pytest.raises(ValueError, match="Each YAML device must be a mapping"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_device_without_name(hass: HomeAssistant) -> None:
    """YAML device without name raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - device_id: dev1\n"
    )
    with pytest.raises(ValueError, match="Each YAML device must define a name"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_device_without_device_id(hass: HomeAssistant) -> None:
    """YAML device without device_id raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n"
    )
    with pytest.raises(ValueError, match="Each YAML device must define a device_id"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_entities_not_a_list(hass: HomeAssistant) -> None:
    """YAML device with non-list entities raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n    device_id: dev1\n    entities: not-a-list\n"
    )
    with pytest.raises(ValueError, match="Device entities must be a list"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_non_dict_entity(hass: HomeAssistant) -> None:
    """YAML entity that is not a mapping raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n    device_id: dev1\n    entities:\n      - not-a-mapping\n"
    )
    with pytest.raises(ValueError, match="Each YAML entity must be a mapping"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_entity_without_type(hass: HomeAssistant) -> None:
    """YAML entity without type raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n    device_id: dev1\n    entities:\n      - name: E\n        key: e\n"
    )
    with pytest.raises(ValueError, match="Each YAML entity must define a type"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_entity_without_name(hass: HomeAssistant) -> None:
    """YAML entity without name raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n    device_id: dev1\n    entities:\n      - type: switch\n        key: e\n"
    )
    with pytest.raises(ValueError, match="Each YAML entity must define a name"):
        await async_load_yaml_devices(hass)


async def test_load_yaml_rejects_entity_without_key(hass: HomeAssistant) -> None:
    """YAML entity without key raises."""
    Path(hass.config.path(YAML_FILE_NAME)).write_text(
        "devices:\n  - name: Dev\n    device_id: dev1\n    entities:\n      - type: switch\n        name: E\n"
    )
    with pytest.raises(ValueError, match="Each YAML entity must define a key"):
        await async_load_yaml_devices(hass)


async def test_yaml_import_matches_by_device_id_without_unique_id(
    hass: HomeAssistant,
) -> None:
    """Import matches existing entries by device_id when unique_id is not set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="YAML Device",
        data=_yaml_device(),
    )
    entry.add_to_hass(hass)

    updated = {**_yaml_device(), CONF_NAME: "Updated YAML"}
    await async_export_entries_to_yaml(hass, [updated])

    changed = await async_import_yaml_to_entries(hass, reload_entries=False)
    assert len(changed) == 1
    assert changed[0].title == "Updated YAML"


async def test_export_config_entries_to_yaml(hass: HomeAssistant) -> None:
    """Export all config entries to YAML."""
    from custom_components.virtual.yaml_storage import async_export_config_entries_to_yaml

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Device",
        data={
            CONF_NAME: "Device",
            CONF_DEVICE_ID: "virtual_exp",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    await async_export_config_entries_to_yaml(hass)
    yaml_path = Path(hass.config.path(YAML_FILE_NAME))
    assert yaml_path.exists()
    content = yaml_path.read_text()
    assert "virtual_exp" in content
