"""Select platform for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INITIAL_VALUE, CONF_OPTIONS
from .entity import VirtualEntityBase, coerce_restored_state
from .models import coerce_entity_value, entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual selects from a config entry."""
    async_add_entities(
        VirtualSelect(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.SELECT)
    )


class VirtualSelect(VirtualEntityBase, RestoreEntity, SelectEntity):
    """A virtual select."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual select."""
        super().__init__(device, definition)
        self._attr_options = definition[CONF_OPTIONS]
        self._attr_current_option = coerce_entity_value(definition, definition[CONF_INITIAL_VALUE])

    async def async_added_to_hass(self) -> None:
        """Restore the previous select state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if (
            value := coerce_restored_state(self._definition, self.entity_id, last_state.state)
        ) is not None:
            self._attr_current_option = value

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        self._attr_current_option = coerce_entity_value(self._definition, option)
        self.async_write_ha_state()

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set select state from the virtual.set_state service."""
        await self.async_select_option(str(value))
