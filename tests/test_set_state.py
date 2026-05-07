"""Tests for the virtual.set_state service."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
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
    SERVICE_SET_STATE,
)
from tests.test_platforms import all_platform_entry_data


async def _setup_entry(hass: HomeAssistant) -> None:
    """Set up an entry with every supported platform."""
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_set_state_updates_supported_entities(hass: HomeAssistant) -> None:
    """Set state for supported virtual entities."""
    await _setup_entry(hass)

    cases = [
        ("binary_sensor.motion", False, STATE_OFF),
        ("sensor.temperature", 22.5, "22.5"),
        ("light.lamp", False, STATE_OFF),
        ("number.level", 7, "7.0"),
        ("select.mode", "cool", "cool"),
        ("text.message", "updated", "updated"),
        ("date.date", "2026-04-26", "2026-04-26"),
        ("datetime.date_time", "2026-04-26T14:30:00+00:00", "2026-04-26T14:30:00+00:00"),
        ("time.time", "14:30:00", "14:30:00"),
    ]

    for entity_id, value, expected in cases:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_STATE,
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )
        assert hass.states.get(entity_id).state == expected


async def test_set_state_rejects_button(hass: HomeAssistant) -> None:
    """Button entities cannot be updated by virtual.set_state."""
    await _setup_entry(hass)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_STATE,
            {"entity_id": "button.reset", "value": True},
            blocking=True,
        )


async def test_set_state_invalid_value_leaves_state_unchanged(hass: HomeAssistant) -> None:
    """Invalid values fail and leave the current state unchanged."""
    await _setup_entry(hass)

    assert hass.states.get("number.level").state == "5.0"
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_STATE,
            {"entity_id": "number.level", "value": 99},
            blocking=True,
        )
    assert hass.states.get("number.level").state == "5.0"


async def test_set_state_updates_switch(hass: HomeAssistant) -> None:
    """Set state for a virtual switch entity."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Switch Device",
        data={
            CONF_NAME: "Switch Device",
            CONF_DEVICE_ID: "virtual_switch_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [
                {
                    CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                    CONF_NAME: "Power",
                    CONF_KEY: "power",
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

    assert hass.states.get("switch.power").state == STATE_OFF

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_STATE,
        {"entity_id": "switch.power", "value": True},
        blocking=True,
    )
    assert hass.states.get("switch.power").state == STATE_ON


async def test_set_state_updates_number(hass: HomeAssistant) -> None:
    """Set state for a virtual number entity covers async_set_virtual_state."""
    await _setup_entry(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_STATE,
        {"entity_id": "number.level", "value": 3},
        blocking=True,
    )
    assert hass.states.get("number.level").state == "3.0"
