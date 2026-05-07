"""Tests for the Virtual integration init module."""

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
