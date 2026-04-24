"""Switch platform for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_KEY,
    CONF_SWITCHES,
)
from .models import build_device_info, switch_unique_id


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual switches from a config entry."""
    async_add_entities(
        VirtualSwitch(entry.data, switch) for switch in entry.data.get(CONF_SWITCHES, [])
    )


class VirtualSwitch(RestoreEntity, SwitchEntity):
    """A virtual switch."""

    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual switch."""
        self._device = device
        self._definition = definition
        self._attr_name = definition[CONF_NAME]
        self._attr_unique_id = switch_unique_id(device[CONF_DEVICE_ID], definition[CONF_KEY])
        self.internal_integration_suggested_object_id = definition[CONF_KEY]
        self._attr_icon = definition.get(CONF_ICON) or None
        self._attr_entity_category = definition.get(CONF_ENTITY_CATEGORY) or None
        self._attr_device_class = definition.get(CONF_DEVICE_CLASS) or None
        self._attr_device_info = build_device_info(device)
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Restore the previous switch state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._attr_is_on = False
        self.async_write_ha_state()
