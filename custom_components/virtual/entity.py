"""Shared virtual entity helpers."""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_NAME

from .const import (
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_KEY,
)
from .models import build_device_info, entity_unique_id


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

    async def async_set_virtual_state(self, value: Any) -> None:
        """Set state from the virtual.set_state service."""
        raise NotImplementedError
