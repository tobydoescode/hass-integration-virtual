"""Sensor platform for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INITIAL_VALUE, CONF_NATIVE_UNIT_OF_MEASUREMENT, CONF_STATE_CLASS
from .entity import VirtualEntityBase, coerce_restored_state
from .models import coerce_entity_value, entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual sensors from a config entry."""
    async_add_entities(
        VirtualSensor(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.SENSOR)
    )


class VirtualSensor(VirtualEntityBase, RestoreEntity, SensorEntity):
    """A virtual sensor."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual sensor."""
        super().__init__(device, definition)
        self._attr_native_value = coerce_entity_value(
            definition, definition.get(CONF_INITIAL_VALUE, "")
        )
        self._attr_native_unit_of_measurement = (
            definition.get(CONF_NATIVE_UNIT_OF_MEASUREMENT) or None
        )
        self._attr_state_class = definition.get(CONF_STATE_CLASS) or None

    async def async_added_to_hass(self) -> None:
        """Restore the previous sensor state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if (
            value := coerce_restored_state(self._definition, self.entity_id, last_state.state)
        ) is not None:
            self._attr_native_value = value

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set sensor state from the virtual.set_state service."""
        self._attr_native_value = coerce_entity_value(self._definition, value)
        self.async_write_ha_state()
