"""Tests for the Virtual config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
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
    CONF_NATIVE_UNIT_OF_MEASUREMENT,
    CONF_STATE_CLASS,
    CONF_VALUE_TYPE,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
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
