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
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_KEY,
    CONF_SWITCHES,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
)


async def test_config_flow_creates_empty_virtual_device(hass: HomeAssistant) -> None:
    """Create a virtual device without switches."""
    with patch("custom_components.virtual.config_flow.generate_device_id", return_value="virtual_1"):
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
    assert result["step_id"] == "switch_menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_switch": False},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Test Device"
    assert result["data"] == {
        CONF_NAME: "Test Device",
        CONF_DEVICE_ID: "virtual_1",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_SWITCHES: [],
    }


async def test_config_flow_adds_multiple_switches(hass: HomeAssistant) -> None:
    """Add multiple switches during initial setup."""
    with patch("custom_components.virtual.config_flow.generate_device_id", return_value="virtual_2"):
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
            user_input={"add_switch": True},
        )
        assert result["step_id"] == "add_switch"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Main Power",
                CONF_KEY: "",
                CONF_ICON: "mdi:power",
                CONF_ENTITY_CATEGORY: "",
                CONF_DEVICE_CLASS: "switch",
            },
        )
        assert result["step_id"] == "switch_menu"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"add_switch": True},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Outlet",
                CONF_KEY: "outlet",
                CONF_ICON: "",
                CONF_ENTITY_CATEGORY: "config",
                CONF_DEVICE_CLASS: "outlet",
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"add_switch": False},
        )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_SWITCHES] == [
        {
            CONF_NAME: "Main Power",
            CONF_KEY: "main_power",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "switch",
        },
        {
            CONF_NAME: "Outlet",
            CONF_KEY: "outlet",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "config",
            CONF_DEVICE_CLASS: "outlet",
        },
    ]


async def test_config_flow_rejects_duplicate_device_id(hass: HomeAssistant) -> None:
    """Reject a device id that already belongs to another config entry."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Existing",
        data={CONF_DEVICE_ID: "virtual_existing", CONF_SWITCHES: []},
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


async def test_config_flow_rejects_duplicate_switch_key(hass: HomeAssistant) -> None:
    """Reject duplicate switch keys in one device."""
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
        user_input={"add_switch": True},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "First",
            CONF_KEY: "duplicate",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"add_switch": True},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Second",
            CONF_KEY: "duplicate",
            CONF_ICON: "",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "",
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "add_switch"
    assert result["errors"] == {"base": "duplicate_switch_key"}


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
        user_input={"add_switch": False},
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


async def test_options_flow_adds_switch(hass: HomeAssistant) -> None:
    """Add a switch to an existing virtual device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_SWITCHES: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "add_switch"},
    )
    assert result["step_id"] == "add_switch"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Added",
            CONF_KEY: "",
            CONF_ICON: "mdi:toggle-switch",
            CONF_ENTITY_CATEGORY: "diagnostic",
            CONF_DEVICE_CLASS: "switch",
        },
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_SWITCHES] == [
        {
            CONF_NAME: "Added",
            CONF_KEY: "added",
            CONF_ICON: "mdi:toggle-switch",
            CONF_ENTITY_CATEGORY: "diagnostic",
            CONF_DEVICE_CLASS: "switch",
        }
    ]


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
            CONF_SWITCHES: [],
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


async def test_options_flow_edits_switch_metadata(hass: HomeAssistant) -> None:
    """Edit switch metadata while keeping the switch key immutable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_SWITCHES: [
                {
                    CONF_NAME: "Original",
                    CONF_KEY: "main_power",
                    CONF_ICON: "",
                    CONF_ENTITY_CATEGORY: "",
                    CONF_DEVICE_CLASS: "",
                }
            ],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"action": "edit_switch"},
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
            CONF_DEVICE_CLASS: "outlet",
        },
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_SWITCHES] == [
        {
            CONF_NAME: "Updated",
            CONF_KEY: "main_power",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "config",
            CONF_DEVICE_CLASS: "outlet",
        }
    ]


async def test_options_flow_hard_removes_switch_entity(hass: HomeAssistant) -> None:
    """Remove a switch from config entry data and the entity registry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Virtual Device",
        data={
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
            CONF_SWITCHES: [
                {
                    CONF_NAME: "Main Power",
                    CONF_KEY: "main_power",
                    CONF_ICON: "",
                    CONF_ENTITY_CATEGORY: "",
                    CONF_DEVICE_CLASS: "",
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
        user_input={"action": "remove_switch"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"switch_keys": ["main_power"]},
    )
    assert result["step_id"] == "confirm_remove_switch"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"confirm": True},
    )

    assert result["type"] == "create_entry"
    assert entry.data[CONF_SWITCHES] == []
    assert er.async_get(hass).async_get("switch.main_power") is None
