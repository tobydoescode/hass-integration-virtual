"""Tests for the Virtual config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.virtual.const import (
    CONF_BRIGHTNESS,
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_CUSTOM_CONNECTION_TYPE,
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
    CONNECTION_TYPE_CUSTOM,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
)


async def test_config_flow_creates_empty_virtual_device(hass: HomeAssistant) -> None:
    """Create a virtual device without entities."""
    with patch(
        "custom_components.virtual.config_flow.generate_device_id",
        return_value="virtual_1",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_NAME: "Test Device",
                CONF_DEVICE_ID: "",
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            },
        )

    assert result["type"] == "form"
    assert result["step_id"] == "entity_menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_entity": False},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Test Device"
    assert result["data"] == {
        CONF_NAME: "Test Device",
        CONF_DEVICE_ID: "virtual_1",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_ENTITIES: [],
    }


async def test_config_flow_adds_switch_entity(hass: HomeAssistant) -> None:
    """Add a switch entity during initial setup."""
    with patch(
        "custom_components.virtual.config_flow.generate_device_id",
        return_value="virtual_2",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_NAME: "Test Device",
                CONF_DEVICE_ID: "",
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"add_entity": True},
        )
        assert result["step_id"] == "add_entity_type"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH},
        )
        assert result["step_id"] == "add_entity"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Main Power",
                CONF_KEY: "",
                CONF_ICON: "mdi:power",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "switch",
                CONF_INITIAL_VALUE: True,
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"add_entity": False},
        )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES] == [
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
            CONF_NAME: "Main Power",
            CONF_KEY: "main_power",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "switch",
            CONF_INITIAL_VALUE: True,
        }
    ]


async def test_config_flow_adds_sensor_entity(hass: HomeAssistant) -> None:
    """Add a numeric sensor entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_entity": True},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Temperature",
            CONF_KEY: "",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_VALUE_TYPE: "number",
            CONF_INITIAL_VALUE: "21.5",
            CONF_NATIVE_UNIT_OF_MEASUREMENT: "C",
            CONF_STATE_CLASS: "measurement",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_entity": False},
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES] == [
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR,
            CONF_NAME: "Temperature",
            CONF_KEY: "temperature",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_VALUE_TYPE: "number",
            CONF_INITIAL_VALUE: 21.5,
            CONF_NATIVE_UNIT_OF_MEASUREMENT: "C",
            CONF_STATE_CLASS: "measurement",
        }
    ]


async def test_config_flow_rejects_duplicate_device_id(hass: HomeAssistant) -> None:
    """Reject a device id that already belongs to another config entry."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Existing",
        data={CONF_DEVICE_ID: "virtual_existing", CONF_ENTITIES: []},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Duplicate",
            CONF_DEVICE_ID: "virtual_existing",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "duplicate_device_id"}


async def test_config_flow_rejects_duplicate_entity_key_across_types(
    hass: HomeAssistant,
) -> None:
    """Reject duplicate entity keys across entity types."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Temperature",
            CONF_KEY: "duplicate",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_VALUE_TYPE: "string",
            CONF_INITIAL_VALUE: "warm",
            CONF_NATIVE_UNIT_OF_MEASUREMENT: "",
            CONF_STATE_CLASS: "",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Number",
            CONF_KEY: "duplicate",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: 1,
            "min": 0,
            "max": 10,
            "step": 1,
            "mode": "auto",
            CONF_NATIVE_UNIT_OF_MEASUREMENT: "",
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "add_entity"
    assert result["errors"] == {"base": "duplicate_entity_key"}


async def test_config_flow_normalizes_mac_connection(hass: HomeAssistant) -> None:
    """Store MAC connections in normalized form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "MAC Device",
            CONF_DEVICE_ID: "virtual_mac",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "AABBCCDDEEFF",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_entity": False},
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_CONNECTION_VALUE] == "aa:bb:cc:dd:ee:ff"


async def test_config_flow_rejects_invalid_mac_connection(hass: HomeAssistant) -> None:
    """Reject invalid MAC connection values."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "MAC Device",
            CONF_DEVICE_ID: "virtual_mac",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "invalid",
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_mac"}


async def test_options_flow_adds_entity(hass: HomeAssistant) -> None:
    """Add an entity to an existing virtual device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "add_entity"},
    )
    assert result["step_id"] == "add_entity_type"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Added",
            CONF_KEY: "",
            CONF_ICON: "mdi:toggle-switch",
            CONF_ENTITY_CATEGORY: "diagnostic",
            CONF_DEVICE_CLASS: "switch",
            CONF_INITIAL_VALUE: False,
        },
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_ENTITIES][0][CONF_KEY] == "added"


async def test_options_flow_adds_entity_and_reload_creates_state(
    hass: HomeAssistant,
) -> None:
    """Adding an entity through options reloads the entry and creates its state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "add_entity"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Added",
            CONF_KEY: "",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: True,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert hass.states.get("switch.added").state == "on"


async def test_options_flow_edits_device_metadata(hass: HomeAssistant) -> None:
    """Edit device name and connection."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "edit_device"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Renamed Device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_CONNECTION_VALUE: "",
        },
    )

    assert result["type"] == "create_entry"
    assert entry.title == "Renamed Device"
    assert entry.data[CONF_NAME] == "Renamed Device"
    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_NONE
    assert CONF_CONNECTION_VALUE not in entry.data


async def test_options_flow_edits_entity_metadata(hass: HomeAssistant) -> None:
    """Edit entity metadata while keeping key and type immutable."""
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
                    CONF_NAME: "Original",
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

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "edit_entity"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_KEY: "main_power"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Updated",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "config",
            CONF_DEVICE_CLASS: "switch",
            CONF_INITIAL_VALUE: True,
        },
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_ENTITIES] == [
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
            CONF_NAME: "Updated",
            CONF_KEY: "main_power",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "config",
            CONF_DEVICE_CLASS: "switch",
            CONF_INITIAL_VALUE: True,
        }
    ]


async def test_options_flow_hard_removes_entity(hass: HomeAssistant) -> None:
    """Remove an entity from config entry data and the entity registry."""
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
    assert er.async_get(hass).async_get("switch.main_power") is not None

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "remove_entity"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entity_keys": ["main_power"]},
    )
    assert result["step_id"] == "confirm_remove_entity"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"confirm": True},
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_ENTITIES] == []
    assert er.async_get(hass).async_get("switch.main_power") is None


async def test_options_flow_removes_entity_and_reload_removes_state(
    hass: HomeAssistant,
) -> None:
    """Removing an entity through options reloads the entry and removes its state."""
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

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "remove_entity"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entity_keys": ["main_power"]},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"confirm": True},
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert hass.states.get("switch.main_power") is None


# ---------------------------------------------------------------------------
# Config flow – light entity (config_flow.py L172, L587-594)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_light_entity(hass: HomeAssistant) -> None:
    """Add a light entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_light_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Lamp",
            CONF_KEY: "lamp",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: True,
            CONF_BRIGHTNESS: "128",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    entity = result["data"][CONF_ENTITIES][0]
    assert entity[CONF_ENTITY_TYPE] == ENTITY_TYPE_LIGHT
    assert entity[CONF_BRIGHTNESS] == 128


# ---------------------------------------------------------------------------
# Config flow – select entity (config_flow.py L201-207, L606-608)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_select_entity(hass: HomeAssistant) -> None:
    """Add a select entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_select_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Mode",
            CONF_KEY: "mode",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_OPTIONS: "auto, heat, cool",
            CONF_INITIAL_VALUE: "auto",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    entity = result["data"][CONF_ENTITIES][0]
    assert entity[CONF_OPTIONS] == ["auto", "heat", "cool"]
    assert entity[CONF_INITIAL_VALUE] == "auto"


# ---------------------------------------------------------------------------
# Config flow – text entity (config_flow.py L208-219, L609-615)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_text_entity(hass: HomeAssistant) -> None:
    """Add a text entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_text_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Message",
            CONF_KEY: "msg",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: "hello",
            CONF_MIN: 0,
            CONF_MAX: 255,
            CONF_MODE: "text",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    entity = result["data"][CONF_ENTITIES][0]
    assert entity[CONF_ENTITY_TYPE] == ENTITY_TYPE_TEXT
    assert entity[CONF_MIN] == 0
    assert entity[CONF_MAX] == 255
    assert entity[CONF_MODE] == "text"


# ---------------------------------------------------------------------------
# Config flow – date/datetime/time entities (config_flow.py L220-221, L616-619)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_date_entity(hass: HomeAssistant) -> None:
    """Add a date entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_date_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_DATE}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Date",
            CONF_KEY: "date",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: "2026-05-06",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES][0][CONF_INITIAL_VALUE] == "2026-05-06"


async def test_config_flow_adds_time_entity(hass: HomeAssistant) -> None:
    """Add a time entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_time_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_TIME}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Time",
            CONF_KEY: "time",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: "14:30:00",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES][0][CONF_INITIAL_VALUE] == "14:30:00"


async def test_config_flow_adds_datetime_entity(hass: HomeAssistant) -> None:
    """Add a datetime entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_datetime_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "DateTime",
            CONF_KEY: "dt",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: "2026-05-06T14:30:00+00:00",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES][0][CONF_INITIAL_VALUE] == "2026-05-06T14:30:00+00:00"


# ---------------------------------------------------------------------------
# Config flow – number entity (config_flow.py L595-605)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_number_entity(hass: HomeAssistant) -> None:
    """Add a number entity during initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_number_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
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
            CONF_MODE: "auto",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    entity = result["data"][CONF_ENTITIES][0]
    assert entity[CONF_MIN] == 0.0
    assert entity[CONF_MAX] == 10.0


# ---------------------------------------------------------------------------
# Config flow – add_entity step with no selected entity type (L298)
# ---------------------------------------------------------------------------
async def test_config_flow_add_entity_redirects_when_no_entity_type(
    hass: HomeAssistant,
) -> None:
    """add_entity redirects to add_entity_type when no type is selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_redirect_dev",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    # At add_entity_type step, select type -> leads to add_entity
    assert result["step_id"] == "add_entity_type"


# ---------------------------------------------------------------------------
# Options flow – edit_device connection validation error (L375-376)
# ---------------------------------------------------------------------------
async def test_options_flow_edit_device_rejects_invalid_connection(
    hass: HomeAssistant,
) -> None:
    """Edit device with invalid connection shows error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"action": "edit_device"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "invalid-mac",
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "edit_device"
    assert result["errors"] == {"base": "invalid_mac"}


# ---------------------------------------------------------------------------
# Options flow – add_entity with no entity_type selected (L413)
# ---------------------------------------------------------------------------
async def test_options_flow_add_entity_redirects_when_no_type(
    hass: HomeAssistant,
) -> None:
    """Options add_entity redirects to add_entity_type when no type is set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"action": "add_entity"}
    )
    assert result["step_id"] == "add_entity_type"


# ---------------------------------------------------------------------------
# Options flow – add_entity validation error (L421-422)
# ---------------------------------------------------------------------------
async def test_options_flow_add_entity_shows_error_on_validation_failure(
    hass: HomeAssistant,
) -> None:
    """Options add_entity shows error when entity validation fails."""
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
                    CONF_NAME: "Existing",
                    CONF_KEY: "existing",
                    CONF_ICON: "",
                    CONF_ENTITY_CATEGORY: "",
                    CONF_DEVICE_CLASS: "",
                    CONF_INITIAL_VALUE: False,
                }
            ],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"action": "add_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH}
    )
    # Submit with duplicate key
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Dup",
            CONF_KEY: "existing",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: False,
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "add_entity"
    assert result["errors"] == {"base": "duplicate_entity_key"}


# ---------------------------------------------------------------------------
# Options flow – edit_entity validation error (L471-472)
# ---------------------------------------------------------------------------
async def test_options_flow_edit_entity_shows_error_on_validation_failure(
    hass: HomeAssistant,
) -> None:
    """Options edit_entity shows error when entity validation fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_ENTITIES: [
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
                    CONF_MODE: "auto",
                }
            ],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"action": "edit_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_KEY: "level"}
    )
    # Submit with min > max to trigger VirtualValidationError
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Updated",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: 5.0,
            CONF_MIN: 100.0,
            CONF_MAX: 0.0,
            CONF_STEP: 1.0,
            CONF_NATIVE_UNIT_OF_MEASUREMENT: "",
            CONF_MODE: "auto",
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "edit_entity"
    assert "base" in result["errors"]


# ---------------------------------------------------------------------------
# Options flow – confirm remove_entity with confirm=False
# ---------------------------------------------------------------------------
async def test_options_flow_cancel_remove_entity(hass: HomeAssistant) -> None:
    """Cancel entity removal when confirm is False."""
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

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"action": "remove_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"entity_keys": ["power"]}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"confirm": False}
    )
    assert result["type"] == "create_entry"
    # Entity should still exist
    assert len(entry.data[CONF_ENTITIES]) == 1


# ---------------------------------------------------------------------------
# Config flow – light entity with empty brightness (config_flow.py L590)
# ---------------------------------------------------------------------------
async def test_config_flow_adds_light_entity_without_brightness(
    hass: HomeAssistant,
) -> None:
    """Light entity without brightness uses ONOFF color mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_light_no_b",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Lamp",
            CONF_KEY: "lamp",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: False,
            CONF_BRIGHTNESS: "",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    entity = result["data"][CONF_ENTITIES][0]
    assert CONF_BRIGHTNESS not in entity


# ---------------------------------------------------------------------------
# Config flow – custom connection type
# ---------------------------------------------------------------------------
async def test_config_flow_custom_connection(hass: HomeAssistant) -> None:
    """Custom connection type stores custom type and value."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Custom Device",
            CONF_DEVICE_ID: "virtual_custom",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CUSTOM,
            CONF_CONNECTION_VALUE: "my-value",
            CONF_CUSTOM_CONNECTION_TYPE: "zigbee",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": False}
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_CONNECTION_TYPE] == CONNECTION_TYPE_CUSTOM
    assert result["data"][CONF_CUSTOM_CONNECTION_TYPE] == "zigbee"
    assert result["data"][CONF_CONNECTION_VALUE] == "my-value"


# ---------------------------------------------------------------------------
# _parse_options and _options_default helpers (config_flow.py L625-642)
# ---------------------------------------------------------------------------
def test_parse_options_from_list() -> None:
    """_parse_options accepts a list of strings."""
    from custom_components.virtual.config_flow import _parse_options

    assert _parse_options(["a", "b", "c"]) == ["a", "b", "c"]


def test_parse_options_from_string() -> None:
    """_parse_options splits comma-separated text."""
    from custom_components.virtual.config_flow import _parse_options

    assert _parse_options("a, b, c") == ["a", "b", "c"]


def test_parse_options_rejects_empty() -> None:
    """_parse_options rejects empty options."""
    import pytest as _pytest

    from custom_components.virtual.config_flow import _parse_options
    from custom_components.virtual.models import VirtualValidationError

    with _pytest.raises(VirtualValidationError, match="invalid_options"):
        _parse_options("")


def test_options_default_returns_comma_joined_list() -> None:
    """_options_default joins list options."""
    from custom_components.virtual.config_flow import _options_default

    assert _options_default({CONF_OPTIONS: ["a", "b"]}) == "a, b"


def test_options_default_returns_string() -> None:
    """_options_default returns string options."""
    from custom_components.virtual.config_flow import _options_default

    assert _options_default({CONF_OPTIONS: "a, b"}) == "a, b"


def test_options_default_returns_empty_for_missing() -> None:
    """_options_default returns empty string for missing options."""
    from custom_components.virtual.config_flow import _options_default

    assert _options_default({}) == ""


# ---------------------------------------------------------------------------
# _iso helper (config_flow.py L647)
# ---------------------------------------------------------------------------
def test_iso_formats_date() -> None:
    """_iso returns ISO format for date."""
    from datetime import date

    from custom_components.virtual.config_flow import _iso

    assert _iso(date(2026, 5, 6)) == "2026-05-06"


def test_iso_formats_time() -> None:
    """_iso returns ISO format for time."""
    from datetime import time

    from custom_components.virtual.config_flow import _iso

    assert _iso(time(14, 30, 0)) == "14:30:00"


def test_iso_formats_datetime() -> None:
    """_iso returns ISO format for datetime."""
    from datetime import datetime, timezone

    from custom_components.virtual.config_flow import _iso

    assert _iso(datetime(2026, 5, 6, 14, 30, 0, tzinfo=timezone.utc)) == "2026-05-06T14:30:00+00:00"


# ---------------------------------------------------------------------------
# Config flow – light with invalid brightness (config_flow.py L593)
# ---------------------------------------------------------------------------
async def test_config_flow_rejects_light_with_invalid_brightness(
    hass: HomeAssistant,
) -> None:
    """Light entity with out-of-range brightness shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_bad_bright",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Lamp",
            CONF_KEY: "lamp",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: True,
            CONF_BRIGHTNESS: "300",
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "add_entity"
    assert result["errors"] == {"base": "invalid_brightness"}


# ---------------------------------------------------------------------------
# Config flow – text with min > max (config_flow.py L613)
# ---------------------------------------------------------------------------
async def test_config_flow_rejects_text_with_min_gt_max(
    hass: HomeAssistant,
) -> None:
    """Text entity with min > max shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_bad_text",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"add_entity": True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Message",
            CONF_KEY: "msg",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
            CONF_INITIAL_VALUE: "hello",
            CONF_MIN: 100,
            CONF_MAX: 5,
            CONF_MODE: "text",
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "add_entity"
    assert result["errors"] == {"base": "invalid_text"}
