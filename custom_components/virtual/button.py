"""Button platform for the Virtual integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import VirtualEntityBase
from .models import entities_for_platform


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up virtual buttons from a config entry."""
    async_add_entities(
        VirtualButton(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.BUTTON)
    )


class VirtualButton(VirtualEntityBase, ButtonEntity):
    """A virtual button."""

    def __init__(self, device: dict[str, Any], definition: dict[str, Any]) -> None:
        """Initialize the virtual button."""
        super().__init__(device, definition)
        self._last_pressed: str | None = None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self._last_pressed is None:
            return None
        return {"last_pressed": self._last_pressed}

    async def async_press(self) -> None:
        """Press the button."""
        self._last_pressed = datetime.now(UTC).isoformat()
        self.async_write_ha_state()

    async def async_set_virtual_state(self, value: Any) -> None:
        """Reject virtual.set_state for buttons."""
        raise HomeAssistantError("virtual.set_state does not support button entities")
