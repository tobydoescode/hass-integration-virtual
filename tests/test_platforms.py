"""Tests for virtual entity platforms."""

from __future__ import annotations

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SERVICE_TURN_ON,
)
from homeassistant.components.light import (
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_NAME, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import StoredState
from homeassistant.helpers.restore_state import async_get as async_get_restore_state
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual.const import (
    CONF_BRIGHTNESS,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_INITIAL_VALUE,
    CONF_KEY,
    CONF_MAX,
    CONF_MIN,
    CONF_MODE,
    CONF_NATIVE_UNIT_OF_MEASUREMENT,
    CONF_OPTIONS,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_VALUE_TYPE,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_BUTTON,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
)


def all_platform_entry_data() -> dict:
    """Return a config entry with every supported non-switch platform."""
    return {
        CONF_NAME: "Virtual Device",
        CONF_DEVICE_ID: "virtual_device",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_ENTITIES: [
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR,
                CONF_NAME: "Motion",
                CONF_KEY: "motion",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "motion",
                CONF_INITIAL_VALUE: True,
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR,
                CONF_NAME: "Temperature",
                CONF_KEY: "temperature",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "temperature",
                CONF_VALUE_TYPE: "number",
                CONF_INITIAL_VALUE: 21.5,
                CONF_NATIVE_UNIT_OF_MEASUREMENT: "C",
                CONF_STATE_CLASS: "measurement",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_BUTTON,
                CONF_NAME: "Reset",
                CONF_KEY: "reset",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT,
                CONF_NAME: "Lamp",
                CONF_KEY: "lamp",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: True,
                CONF_BRIGHTNESS: 128,
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
                CONF_NAME: "Level",
                CONF_KEY: "level",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: 5.0,
                CONF_MIN: 0.0,
                CONF_MAX: 10.0,
                CONF_STEP: 1.0,
                CONF_NATIVE_UNIT_OF_MEASUREMENT: "",
                CONF_MODE: "slider",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "Mode",
                CONF_KEY: "mode",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_OPTIONS: ["auto", "heat", "cool"],
                CONF_INITIAL_VALUE: "heat",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT,
                CONF_NAME: "Message",
                CONF_KEY: "message",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: "hello",
                CONF_MIN: 0,
                CONF_MAX: 20,
                CONF_MODE: "text",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_DATE,
                CONF_NAME: "Date",
                CONF_KEY: "date",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: "2026-04-25",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME,
                CONF_NAME: "Date Time",
                CONF_KEY: "date_time",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: "2026-04-25T13:45:00+00:00",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TIME,
                CONF_NAME: "Time",
                CONF_KEY: "time",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "",
                CONF_INITIAL_VALUE: "13:45:00",
            },
        ],
    }


async def test_platforms_setup_entities(hass: HomeAssistant) -> None:
    """Set up every supported non-switch platform."""
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expected_states = {
        "binary_sensor.motion": STATE_ON,
        "sensor.temperature": "21.5",
        "button.reset": None,
        "light.lamp": STATE_ON,
        "number.level": "5.0",
        "select.mode": "heat",
        "text.message": "hello",
        "date.date": "2026-04-25",
        "datetime.date_time": "2026-04-25T13:45:00+00:00",
        "time.time": "13:45:00",
    }
    registry = er.async_get(hass)
    for entity_id, expected in expected_states.items():
        state = hass.states.get(entity_id)
        assert state is not None, entity_id
        if expected is not None:
            assert state.state == expected
        registry_entry = registry.async_get(entity_id)
        assert registry_entry is not None
        assert registry_entry.unique_id.startswith("virtual_device_")

    assert hass.states.get("light.lamp").attributes[ATTR_BRIGHTNESS] == 128


async def test_light_and_button_native_services(hass: HomeAssistant) -> None:
    """Exercise native light and button services."""
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.lamp", ATTR_BRIGHTNESS: 200},
        blocking=True,
    )
    assert hass.states.get("light.lamp").attributes[ATTR_BRIGHTNESS] == 200

    assert "last_pressed" not in hass.states.get("button.reset").attributes
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.reset"},
        blocking=True,
    )
    assert "last_pressed" in hass.states.get("button.reset").attributes


async def test_invalid_restored_state_falls_back_to_initial_value(hass: HomeAssistant) -> None:
    """Invalid restored values do not prevent entities from being added."""
    async_get_restore_state(hass).last_states["number.level"] = StoredState(
        State("number.level", "99"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("number.level").state == "5.0"


async def test_light_restores_previous_on_state_with_brightness(hass: HomeAssistant) -> None:
    """Restore light on state and brightness from stored state."""
    async_get_restore_state(hass).last_states["light.lamp"] = StoredState(
        State("light.lamp", STATE_ON, {"brightness": 200}),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.lamp")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 200


async def test_light_turn_off(hass: HomeAssistant) -> None:
    """Turn off a virtual light."""
    from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
    from homeassistant.const import SERVICE_TURN_OFF

    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.lamp"},
        blocking=True,
    )
    assert hass.states.get("light.lamp").state == "off"


async def test_date_set_value(hass: HomeAssistant) -> None:
    """Set a virtual date value."""
    from datetime import date as dt_date

    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "date",
        "set_value",
        {ATTR_ENTITY_ID: "date.date", "date": dt_date(2026, 6, 1).isoformat()},
        blocking=True,
    )
    assert hass.states.get("date.date").state == "2026-06-01"


async def test_date_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore date state from stored state."""
    async_get_restore_state(hass).last_states["date.date"] = StoredState(
        State("date.date", "2026-03-15"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("date.date").state == "2026-03-15"


async def test_datetime_set_value(hass: HomeAssistant) -> None:
    """Set a virtual datetime value."""
    from datetime import datetime, timezone

    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    dt_val = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    await hass.services.async_call(
        "datetime",
        "set_value",
        {ATTR_ENTITY_ID: "datetime.date_time", "datetime": dt_val.isoformat()},
        blocking=True,
    )
    assert hass.states.get("datetime.date_time").state == "2026-06-01T10:00:00+00:00"


async def test_datetime_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore datetime state from stored state."""
    async_get_restore_state(hass).last_states["datetime.date_time"] = StoredState(
        State("datetime.date_time", "2026-03-15T08:00:00+00:00"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("datetime.date_time").state == "2026-03-15T08:00:00+00:00"


async def test_time_set_value(hass: HomeAssistant) -> None:
    """Set a virtual time value."""
    from datetime import time as dt_time

    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "time",
        "set_value",
        {ATTR_ENTITY_ID: "time.time", "time": dt_time(16, 0, 0).isoformat()},
        blocking=True,
    )
    assert hass.states.get("time.time").state == "16:00:00"


async def test_time_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore time state from stored state."""
    async_get_restore_state(hass).last_states["time.time"] = StoredState(
        State("time.time", "08:30:00"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("time.time").state == "08:30:00"


async def test_binary_sensor_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore binary sensor state from stored state."""
    from homeassistant.const import STATE_OFF

    async_get_restore_state(hass).last_states["binary_sensor.motion"] = StoredState(
        State("binary_sensor.motion", STATE_OFF),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.motion").state == STATE_OFF


async def test_sensor_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore sensor state from stored state."""
    async_get_restore_state(hass).last_states["sensor.temperature"] = StoredState(
        State("sensor.temperature", "25.0"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.temperature").state == "25.0"


async def test_select_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore select state from stored state."""
    async_get_restore_state(hass).last_states["select.mode"] = StoredState(
        State("select.mode", "cool"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("select.mode").state == "cool"


async def test_text_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore text state from stored state."""
    async_get_restore_state(hass).last_states["text.message"] = StoredState(
        State("text.message", "restored"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("text.message").state == "restored"


async def test_number_restores_previous_state(hass: HomeAssistant) -> None:
    """Restore number state from stored state."""
    async_get_restore_state(hass).last_states["number.level"] = StoredState(
        State("number.level", "7.0"),
        None,
        dt_util.utcnow(),
    )
    entry = MockConfigEntry(domain=DOMAIN, title="Virtual Device", data=all_platform_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("number.level").state == "7.0"
