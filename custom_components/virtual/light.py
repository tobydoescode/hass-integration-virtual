"""Light platform for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_BRIGHTNESS, CONF_INITIAL_VALUE
from .entity import VirtualEntityBase, coerce_restored_state
from .models import coerce_entity_value, entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual lights from a config entry."""
    async_add_entities(
        VirtualLight(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.LIGHT)
    )


class VirtualLight(VirtualEntityBase, RestoreEntity, LightEntity):
    """A virtual light."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual light."""
        super().__init__(device, definition)
        self._attr_is_on = bool(definition.get(CONF_INITIAL_VALUE, False))
        self._attr_brightness = definition.get(CONF_BRIGHTNESS)
        color_mode = ColorMode.BRIGHTNESS if self._attr_brightness is not None else ColorMode.ONOFF
        self._attr_supported_color_modes = {color_mode}
        self._attr_color_mode = color_mode

    async def async_added_to_hass(self) -> None:
        """Restore the previous light state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if (
            value := coerce_restored_state(self._definition, self.entity_id, last_state.state)
        ) is not None:
            self._attr_is_on = value
        if ATTR_BRIGHTNESS in last_state.attributes:
            self._attr_brightness = last_state.attributes[ATTR_BRIGHTNESS]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set light state from the virtual.set_state service."""
        self._attr_is_on = coerce_entity_value(self._definition, value)
        self.async_write_ha_state()
