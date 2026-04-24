"""Definition helpers for the Virtual integration."""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from slugify import slugify

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_CUSTOM_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_SWITCHES,
    CONNECTION_TYPE_CUSTOM,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    MANUFACTURER,
)

MAC_HEX_RE = re.compile(r"^[0-9a-f]{12}$")


class VirtualValidationError(ValueError):
    """Raised when a virtual definition is invalid."""


def generate_device_id() -> str:
    """Generate a stable virtual device id."""
    return f"virtual_{uuid4().hex}"


def generate_switch_key(name: str, existing_keys: set[str]) -> str:
    """Generate a readable switch key that does not collide."""
    base = slugify(name, separator="_") or "switch"
    key = base
    suffix = 2
    while key in existing_keys:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def validate_unique_switch_key(key: str, switches: list[dict[str, Any]]) -> None:
    """Validate that a switch key is not already used in this device."""
    if any(switch.get("key") == key for switch in switches):
        raise VirtualValidationError("duplicate_switch_key")


def normalize_connection(
    connection_type: str,
    connection_value: str | None,
    custom_connection_type: str | None,
) -> dict[str, str]:
    """Normalize a connection definition for storage."""
    if connection_type == CONNECTION_TYPE_NONE:
        return {CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE}

    if connection_type == CONNECTION_TYPE_MAC:
        value = _normalize_mac(connection_value or "")
        return {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: value,
        }

    if connection_type == CONNECTION_TYPE_CUSTOM:
        custom_type = (custom_connection_type or "").strip()
        value = (connection_value or "").strip()
        if not custom_type or not value:
            raise VirtualValidationError("invalid_connection")
        return {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CUSTOM,
            CONF_CUSTOM_CONNECTION_TYPE: custom_type,
            CONF_CONNECTION_VALUE: value,
        }

    raise VirtualValidationError("invalid_connection_type")


def build_device_info(device: dict[str, Any]) -> dict[str, Any]:
    """Build Home Assistant device info for a virtual device."""
    device_id = device[CONF_DEVICE_ID]
    info: dict[str, Any] = {
        "identifiers": {(DOMAIN, device_id)},
        "name": device[CONF_NAME],
        "manufacturer": MANUFACTURER,
    }
    connection = connection_tuple(device)
    if connection is not None:
        info["connections"] = {connection}
    return info


def connection_tuple(device: dict[str, Any]) -> tuple[str, str] | None:
    """Return the Home Assistant device registry connection tuple."""
    connection_type = device.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_NONE)
    if connection_type == CONNECTION_TYPE_NONE:
        return None
    if connection_type == CONNECTION_TYPE_MAC:
        return (CONNECTION_NETWORK_MAC, device[CONF_CONNECTION_VALUE])
    if connection_type == CONNECTION_TYPE_CUSTOM:
        return (
            device[CONF_CUSTOM_CONNECTION_TYPE],
            device[CONF_CONNECTION_VALUE],
        )
    return None


def switch_unique_id(device_id: str, switch_key: str) -> str:
    """Return the unique id for a switch."""
    return f"{device_id}_{switch_key}"


def _normalize_mac(value: str) -> str:
    """Normalize MAC addresses to lowercase colon-separated form."""
    compact = re.sub(r"[^0-9a-fA-F]", "", value).lower()
    if not MAC_HEX_RE.match(compact):
        raise VirtualValidationError("invalid_mac")
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2))
