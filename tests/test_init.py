"""Tests for the Virtual integration init module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual import async_setup
from custom_components.virtual.const import (
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_INITIAL_VALUE,
    CONF_KEY,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_SWITCH,
    SERVICE_SET_STATE,
)


async def test_migrate_entry_returns_true(hass: HomeAssistant) -> None:
    """Migration handler returns True for current version entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Set up and unload a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [
                {
                    CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                    CONF_NAME: "Main Power",
                    CONF_KEY: "main_power",
                    CONF_ICON: "",
                    CONF_ENTITY_CATEGORY: "",
                    CONF_DEVICE_CLASS: "",
                    CONF_INITIAL_VALUE: False,
                }
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("switch.main_power") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_set_state_service_rejects_non_virtual_entity(hass: HomeAssistant) -> None:
    """set_state service raises for non-virtual entity ids."""
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match="is not a virtual entity"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_STATE,
            {"entity_id": "switch.nonexistent", "value": True},
            blocking=True,
        )


async def test_import_yaml_service(hass: HomeAssistant) -> None:
    """import_yaml service imports YAML devices."""
    from custom_components.virtual.yaml_storage import async_export_entries_to_yaml

    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    # Export a device so import has something to work with
    await async_export_entries_to_yaml(
        hass,
        [
            {
                CONF_NAME: "YAML Device",
                CONF_DEVICE_ID: "virtual_yaml_svc",
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
                CONF_ENTITIES: [],
            }
        ],
    )

    await hass.services.async_call(DOMAIN, "import_yaml", {}, blocking=True)
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert any(e.data.get(CONF_DEVICE_ID) == "virtual_yaml_svc" for e in entries)


async def test_import_yaml_service_raises_on_error(hass: HomeAssistant) -> None:
    """import_yaml service wraps exceptions in HomeAssistantError."""
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    # Write invalid YAML content
    Path(hass.config.path("virtual.yaml")).write_text("devices: not-a-list\n")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "import_yaml", {}, blocking=True)


async def test_export_yaml_service(hass: HomeAssistant) -> None:
    """export_yaml service writes config entries to YAML."""
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
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    await hass.services.async_call(DOMAIN, "export_yaml", {}, blocking=True)

    yaml_path = Path(hass.config.path("virtual.yaml"))
    assert yaml_path.exists()
    content = yaml_path.read_text()
    assert "virtual_exp" in content


async def test_export_yaml_service_raises_on_error(hass: HomeAssistant) -> None:
    """export_yaml service wraps exceptions in HomeAssistantError."""
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    with patch(
        "custom_components.virtual.async_export_config_entries_to_yaml",
        side_effect=RuntimeError("write failed"),
    ), pytest.raises(HomeAssistantError, match="write failed"):
        await hass.services.async_call(DOMAIN, "export_yaml", {}, blocking=True)


async def test_yaml_import_after_setup_handles_exception(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """YAML import during setup logs exceptions instead of crashing."""
    # Write invalid YAML so auto-import fails
    Path(hass.config.path("virtual.yaml")).write_text("devices: not-a-list\n")

    import logging

    with caplog.at_level(logging.ERROR, logger="custom_components.virtual"):
        assert await async_setup(hass, {})
        await hass.async_block_till_done()

    assert "Error importing virtual.yaml" in caplog.text


async def test_migrate_entry(hass: HomeAssistant) -> None:
    """Verify the migration handler returns True."""
    from custom_components.virtual import async_migrate_entry

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Device",
        data={
            CONF_NAME: "Device",
            CONF_DEVICE_ID: "virtual_migrate",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
        version=1,
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry) is True
