"""Shared virtual entity helpers."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_KEY,
)
from .models import build_device_info, coerce_entity_value, entity_unique_id

_LOGGER = logging.getLogger(__name__)

DATA_ENTITY_REGISTRY = "entity_registry"


def virtual_entity_registry(hass: HomeAssistant) -> dict[str, VirtualEntityBase]:
    """Return the runtime virtual entity registry."""
    from .const import DOMAIN

    return hass.data.setdefault(DOMAIN, {}).setdefault(DATA_ENTITY_REGISTRY, {})


class VirtualEntityBase:
    """Common attributes for virtual entities."""

    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize common virtual entity attributes."""
        self._device = device
        self._definition = definition
        self._attr_name = definition[CONF_NAME]
        self._attr_unique_id = entity_unique_id(device[CONF_DEVICE_ID], definition[CONF_KEY])
        self.internal_integration_suggested_object_id = definition[CONF_KEY]
        self._attr_icon = definition.get(CONF_ICON) or None
        self._attr_entity_category = definition.get(CONF_ENTITY_CATEGORY) or None
        self._attr_device_class = definition.get(CONF_DEVICE_CLASS) or None
        self._attr_device_info = build_device_info(device)

    async def async_added_to_hass(self) -> None:
        """Register the entity for virtual services."""
        await super().async_added_to_hass()
        virtual_entity_registry(self.hass)[self.entity_id] = self

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the entity from virtual services."""
        virtual_entity_registry(self.hass).pop(self.entity_id, None)
        await super().async_will_remove_from_hass()

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set state from the virtual.set_state service."""
        raise NotImplementedError


def coerce_restored_state(
    definition: dict[str, Any], entity_id: str, restored_state: str
) -> Any | None:
    """Coerce a restored state, returning None when it should be ignored."""
    if restored_state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
        return None
    try:
        return coerce_entity_value(definition, restored_state)
    except Exception as err:
        _LOGGER.warning(
            "Ignoring invalid restored state for %s: %s",
            entity_id,
            err,
        )
        return None
