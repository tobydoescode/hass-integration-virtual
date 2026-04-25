"""Binary sensor platform for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INITIAL_VALUE
from .entity import VirtualEntityBase
from .models import coerce_entity_value, entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual binary sensors from a config entry."""
    async_add_entities(
        VirtualBinarySensor(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.BINARY_SENSOR)
    )


class VirtualBinarySensor(VirtualEntityBase, RestoreEntity, BinarySensorEntity):
    """A virtual binary sensor."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual binary sensor."""
        super().__init__(device, definition)
        self._attr_is_on = bool(definition.get(CONF_INITIAL_VALUE, False))

    async def async_added_to_hass(self) -> None:
        """Restore the previous binary sensor state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set binary sensor state from the virtual.set_state service."""
        self._attr_is_on = coerce_entity_value(self._definition, value)
        self.async_write_ha_state()
