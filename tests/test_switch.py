"""Tests for virtual switch entities."""

from __future__ import annotations

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import StoredState
from homeassistant.helpers.restore_state import async_get as async_get_restore_state
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual.const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_INITIAL_VALUE,
    CONF_KEY,
    CONNECTION_TYPE_MAC,
    DOMAIN,
    ENTITY_TYPE_SWITCH,
)


def _entry_data() -> dict:
    """Return config entry data with one switch."""
    return {
        CONF_NAME: "Virtual Device",
        CONF_DEVICE_ID: "virtual_device",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
        CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
        CONF_ENTITIES: [
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "Main Power",
                CONF_KEY: "main_power",
                CONF_ICON: "mdi:power",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "switch",
                CONF_INITIAL_VALUE: False,
            }
        ],
    }


async def test_switch_setup_creates_entity_and_device(hass: HomeAssistant) -> None:
    """Set up a switch entity with unique id and device info."""
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=_entry_data())
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.main_power")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes["icon"] == "mdi:power"

    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get("switch.main_power")
    assert entity_entry is not None
    assert entity_entry.unique_id == "virtual_device_main_power"

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "virtual_device")},
        connections={(dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff")},
    )
    assert device_entry is not None
    assert device_entry.name == "Virtual Device"


async def test_switch_turns_on_and_off(hass: HomeAssistant) -> None:
    """Turn a virtual switch on and off."""
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.main_power"},
        blocking=True,
    )
    assert hass.states.get("switch.main_power").state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.main_power"},
        blocking=True,
    )
    assert hass.states.get("switch.main_power").state == STATE_OFF


async def test_switch_uses_initial_value_without_restored_state(hass: HomeAssistant) -> None:
    """Use configured initial value when no restored state exists."""
    data = _entry_data()
    data[CONF_ENTITIES][0][CONF_INITIAL_VALUE] = True
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=data)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("switch.main_power").state == STATE_ON


async def test_switch_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore switch state from Home Assistant restore state."""
    async_get_restore_state(hass).last_states["switch.main_power"] = StoredState(
        State("switch.main_power", STATE_ON),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=_entry_data())
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("switch.main_power").state == STATE_ON
