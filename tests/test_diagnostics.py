"""Tests for the Virtual integration diagnostics."""

from __future__ import annotations

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
)
from custom_components.virtual.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_returns_config_and_entity_info(hass: HomeAssistant) -> None:
    """Diagnostics returns device config and entity metadata."""
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

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config"]["device_id"] == "virtual_device"
    assert result["config"]["entity_count"] == 1
    assert len(result["entities"]) == 1
    assert result["entities"][0]["type"] == ENTITY_TYPE_SWITCH
    assert result["entities"][0]["key"] == "main_power"
    assert "switch.main_power" in result["registered_virtual_entities"]


async def test_diagnostics_empty_device(hass: HomeAssistant) -> None:
    """Diagnostics for a device with no entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Empty Device",
        data={
            CONF_NAME: "Empty Device",
            CONF_DEVICE_ID: "virtual_empty",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config"]["entity_count"] == 0
    assert result["entities"] == []
