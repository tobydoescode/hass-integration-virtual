"""YAML import/export helpers for the Virtual integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import load_yaml, save_yaml

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_TYPE,
    CONF_KEY,
    CONNECTION_TYPE_NONE,
    DOMAIN,
)

YAML_FILE_NAME = "virtual.yaml"
YAML_DEVICES = "devices"

_LOGGER = logging.getLogger(__name__)


async def async_load_yaml_devices(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Load virtual device definitions from YAML."""
    path = hass.config.path(YAML_FILE_NAME)
    if not await hass.async_add_executor_job(_path_exists, path):
        return []

    data = await hass.async_add_executor_job(load_yaml, path)
    if data is None:
        return []
    if not isinstance(data, dict):
        raise ValueError(f"{YAML_FILE_NAME} must contain a mapping")

    devices = data.get(YAML_DEVICES, [])
    if not isinstance(devices, list):
        raise ValueError(f"{YAML_DEVICES} must be a list")

    return [_normalize_device(device) for device in devices]


async def async_export_entries_to_yaml(hass: HomeAssistant, devices: list[dict[str, Any]]) -> None:
    """Write virtual device definitions to YAML."""
    path = hass.config.path(YAML_FILE_NAME)
    await hass.async_add_executor_job(save_yaml, path, {YAML_DEVICES: devices})


async def async_export_config_entries_to_yaml(hass: HomeAssistant) -> None:
    """Export all Virtual config entries to YAML."""
    devices = [dict(entry.data) for entry in hass.config_entries.async_entries(DOMAIN)]
    await async_export_entries_to_yaml(hass, devices)


async def async_import_yaml_to_entries(
    hass: HomeAssistant, *, reload_entries: bool = True
) -> list[ConfigEntry]:
    """Import YAML devices into Virtual config entries."""
    if not await hass.async_add_executor_job(_path_exists, hass.config.path(YAML_FILE_NAME)):
        return []

    devices = await async_load_yaml_devices(hass)
    changed_entries: list[ConfigEntry] = []
    yaml_device_ids = {device[CONF_DEVICE_ID] for device in devices}

    for entry in hass.config_entries.async_entries(DOMAIN):
        device_id = entry.data.get(CONF_DEVICE_ID)
        if device_id not in yaml_device_ids:
            _LOGGER.warning("Virtual device %s is not managed by virtual.yaml", device_id)

    for device in devices:
        entry = _entry_for_device_id(hass, device[CONF_DEVICE_ID])
        if entry is None:
            entry = _create_import_entry(device)
            await hass.config_entries.async_add(entry)
            changed_entries.append(entry)
            continue

        merged_device = _merge_device(entry.data, device)
        if entry.data != merged_device or entry.title != merged_device[CONF_NAME]:
            hass.config_entries.async_update_entry(
                entry,
                title=merged_device[CONF_NAME],
                data=merged_device,
                unique_id=merged_device[CONF_DEVICE_ID],
            )
            changed_entries.append(entry)

    if reload_entries:
        for entry in changed_entries:
            await hass.config_entries.async_reload(entry.entry_id)

    return changed_entries


def _path_exists(path: str) -> bool:
    """Return true when path exists."""
    from pathlib import Path

    return Path(path).exists()


def _entry_for_device_id(hass: HomeAssistant, device_id: str) -> ConfigEntry | None:
    """Return an existing Virtual entry with the given device id."""
    if entry := hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, device_id):
        return entry
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_DEVICE_ID) == device_id:
            return entry
    return None


def _merge_device(existing_device: dict[str, Any], yaml_device: dict[str, Any]) -> dict[str, Any]:
    """Merge YAML-managed entities with existing entities absent from YAML."""
    merged = dict(yaml_device)
    yaml_entities = list(yaml_device.get(CONF_ENTITIES, []))
    yaml_entity_keys = {entity[CONF_KEY] for entity in yaml_entities}
    unmanaged_entities = [
        entity
        for entity in existing_device.get(CONF_ENTITIES, [])
        if entity.get(CONF_KEY) not in yaml_entity_keys
    ]
    for entity in unmanaged_entities:
        _LOGGER.warning(
            "Virtual entity %s/%s is not managed by virtual.yaml",
            yaml_device[CONF_DEVICE_ID],
            entity.get(CONF_KEY),
        )
    merged[CONF_ENTITIES] = [*yaml_entities, *unmanaged_entities]
    return merged


def _create_import_entry(device: dict[str, Any]) -> ConfigEntry:
    """Create a config entry for a YAML device."""
    now = datetime.now(UTC)
    return ConfigEntry(
        created_at=now,
        data=device,
        discovery_keys=MappingProxyType({}),
        domain=DOMAIN,
        minor_version=1,
        modified_at=now,
        options={},
        source=SOURCE_IMPORT,
        subentries_data=[],
        title=device[CONF_NAME],
        unique_id=device[CONF_DEVICE_ID],
        version=1,
    )


def _normalize_device(device: Any) -> dict[str, Any]:
    """Validate and normalize one YAML device definition."""
    if not isinstance(device, dict):
        raise ValueError("Each YAML device must be a mapping")
    if not isinstance(device.get(CONF_NAME), str) or not device[CONF_NAME]:
        raise ValueError("Each YAML device must define a name")
    if not isinstance(device.get(CONF_DEVICE_ID), str) or not device[CONF_DEVICE_ID]:
        raise ValueError("Each YAML device must define a device_id")

    normalized = dict(device)
    normalized.setdefault(CONF_CONNECTION_TYPE, CONNECTION_TYPE_NONE)
    entities = normalized.setdefault(CONF_ENTITIES, [])
    if not isinstance(entities, list):
        raise ValueError("Device entities must be a list")
    for entity in entities:
        _validate_entity(entity)
    return normalized


def _validate_entity(entity: Any) -> None:
    """Validate the required entity YAML shape."""
    if not isinstance(entity, dict):
        raise ValueError("Each YAML entity must be a mapping")
    if not isinstance(entity.get(CONF_ENTITY_TYPE), str) or not entity[CONF_ENTITY_TYPE]:
        raise ValueError("Each YAML entity must define a type")
    if not isinstance(entity.get(CONF_NAME), str) or not entity[CONF_NAME]:
        raise ValueError("Each YAML entity must define a name")
    if not isinstance(entity.get(CONF_KEY), str) or not entity[CONF_KEY]:
        raise ValueError("Each YAML entity must define a key")
