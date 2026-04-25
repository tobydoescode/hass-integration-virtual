"""The Virtual integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import ATTR_VALUE, DOMAIN, PLATFORMS, SERVICE_SET_STATE
from .entity import virtual_entity_registry
from .yaml_storage import (
    async_export_config_entries_to_yaml,
    async_import_yaml_to_entries,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_EXPORT_YAML = "export_yaml"
SERVICE_IMPORT_YAML = "import_yaml"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Virtual integration."""
    hass.async_create_task(_async_import_yaml_after_setup(hass))
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STATE,
        _async_set_state_service,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.ensure_list,
                vol.Required(ATTR_VALUE): object,
            }
        ),
    )
    hass.services.async_register(DOMAIN, SERVICE_IMPORT_YAML, _async_import_yaml_service)
    hass.services.async_register(DOMAIN, SERVICE_EXPORT_YAML, _async_export_yaml_service)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Virtual from a config entry."""
    await async_import_yaml_to_entries(hass, reload_entries=False)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when config entry data changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_import_yaml_after_setup(hass: HomeAssistant) -> None:
    """Import YAML after component setup has completed."""
    try:
        await async_import_yaml_to_entries(hass, reload_entries=False)
    except Exception:
        _LOGGER.exception("Error importing virtual.yaml")


async def _async_set_state_service(call: ServiceCall) -> None:
    """Set the state of a virtual entity."""
    registry = virtual_entity_registry(call.hass)
    entity_ids = call.data[ATTR_ENTITY_ID]
    value: Any = call.data[ATTR_VALUE]
    for entity_id in entity_ids:
        entity = registry.get(entity_id)
        if entity is None:
            raise HomeAssistantError(f"{entity_id} is not a virtual entity")
        try:
            await entity.async_set_virtual_state(value)
        except Exception as err:
            raise HomeAssistantError(str(err)) from err


async def _async_import_yaml_service(call: ServiceCall) -> None:
    """Import virtual devices from YAML."""
    try:
        await async_import_yaml_to_entries(call.hass)
    except Exception as err:
        raise HomeAssistantError(str(err)) from err


async def _async_export_yaml_service(call: ServiceCall) -> None:
    """Export virtual devices to YAML."""
    try:
        await async_export_config_entries_to_yaml(call.hass)
    except Exception as err:
        raise HomeAssistantError(str(err)) from err
