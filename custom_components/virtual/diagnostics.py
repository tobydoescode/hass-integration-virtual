"""Diagnostics support for the Virtual integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_ENTITIES, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entities = entry.data.get(CONF_ENTITIES, [])
    return {
        "config": {
            "device_id": entry.data.get(CONF_DEVICE_ID),
            "entity_count": len(entities),
        },
        "entities": [
            {
                "type": entity.get("type"),
                "key": entity.get("key"),
                "name": entity.get("name"),
            }
            for entity in entities
        ],
        "registered_virtual_entities": list(
            hass.data.get(DOMAIN, {}).get("entity_registry", {}).keys()
        ),
    }
