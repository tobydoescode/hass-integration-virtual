"""Datetime platform for the Virtual integration."""

from __future__ import annotations

from datetime import datetime as dt_datetime
from typing import Any

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INITIAL_VALUE
from .entity import VirtualEntityBase, coerce_restored_state
from .models import coerce_entity_value, entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual datetimes from a config entry."""
    async_add_entities(
        VirtualDateTime(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.DATETIME)
    )


class VirtualDateTime(VirtualEntityBase, RestoreEntity, DateTimeEntity):
    """A virtual datetime."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual datetime."""
        super().__init__(device, definition)
        self._attr_native_value = coerce_entity_value(definition, definition[CONF_INITIAL_VALUE])

    async def async_added_to_hass(self) -> None:
        """Restore the previous datetime state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if (
            value := coerce_restored_state(self._definition, self.entity_id, last_state.state)
        ) is not None:
            self._attr_native_value = value

    async def async_set_value(self, value: dt_datetime) -> None:
        """Set datetime value."""
        self._attr_native_value = coerce_entity_value(self._definition, value)
        self.async_write_ha_state()

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set datetime state from the virtual.set_state service."""
        self._attr_native_value = coerce_entity_value(self._definition, value)
        self.async_write_ha_state()
