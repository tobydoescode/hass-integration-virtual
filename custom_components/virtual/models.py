"""Definition helpers for the Virtual integration."""

from __future__ import annotations

from datetime import date, datetime, time
import re
from typing import Any
from uuid import uuid4

from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from slugify import slugify

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_CUSTOM_CONNECTION_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_TYPE,
    CONF_KEY,
    CONF_MAX,
    CONF_MIN,
    CONF_OPTIONS,
    CONF_VALUE_TYPE,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
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
    return generate_entity_key(name, existing_keys)


def generate_entity_key(name: str, existing_keys: set[str]) -> str:
    """Generate a readable entity key that does not collide."""
    base = slugify(name, separator="_") or "switch"
    key = base
    suffix = 2
    while key in existing_keys:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def validate_unique_switch_key(key: str, switches: list[dict[str, Any]]) -> None:
    """Validate that a switch key is not already used in this device."""
    validate_unique_entity_key(key, switches)


def validate_unique_entity_key(key: str, entities: list[dict[str, Any]]) -> None:
    """Validate that an entity key is not already used in this device."""
    if any(entity.get(CONF_KEY) == key for entity in entities):
        raise VirtualValidationError("duplicate_entity_key")


def entities_for_platform(device: dict[str, Any], platform: Platform) -> list[dict[str, Any]]:
    """Return entity definitions for a Home Assistant platform."""
    return [
        entity
        for entity in device.get(CONF_ENTITIES, [])
        if entity.get(CONF_ENTITY_TYPE) == platform.value
    ]


def entity_unique_id(device_id: str, entity_key: str) -> str:
    """Return the unique id for an entity."""
    return f"{device_id}_{entity_key}"


def coerce_entity_value(definition: dict[str, Any], value: Any) -> Any:
    """Coerce a value according to an entity definition."""
    entity_type = definition[CONF_ENTITY_TYPE]
    if entity_type in {ENTITY_TYPE_SWITCH, ENTITY_TYPE_BINARY_SENSOR, ENTITY_TYPE_LIGHT}:
        return _coerce_bool(value)
    if entity_type == ENTITY_TYPE_SENSOR:
        if definition.get(CONF_VALUE_TYPE) == "number":
            return _coerce_float(value)
        return str(value)
    if entity_type == ENTITY_TYPE_NUMBER:
        number = _coerce_float(value)
        minimum = _coerce_float(definition.get(CONF_MIN, number))
        maximum = _coerce_float(definition.get(CONF_MAX, number))
        if number < minimum or number > maximum:
            raise VirtualValidationError("invalid_number")
        return number
    if entity_type == ENTITY_TYPE_SELECT:
        option = str(value)
        if option not in definition.get(CONF_OPTIONS, []):
            raise VirtualValidationError("invalid_option")
        return option
    if entity_type == ENTITY_TYPE_TEXT:
        text = str(value)
        minimum = int(definition.get(CONF_MIN, 0))
        maximum = int(definition.get(CONF_MAX, len(text)))
        if len(text) < minimum or len(text) > maximum:
            raise VirtualValidationError("invalid_text")
        return text
    if entity_type == ENTITY_TYPE_DATE:
        return value if isinstance(value, date) and not isinstance(value, datetime) else date.fromisoformat(str(value))
    if entity_type == ENTITY_TYPE_TIME:
        return value if isinstance(value, time) else time.fromisoformat(str(value))
    if entity_type == ENTITY_TYPE_DATETIME:
        return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return value


def _coerce_float(value: Any) -> float:
    """Coerce a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError) as err:
        raise VirtualValidationError("invalid_number") from err


def _coerce_bool(value: Any) -> bool:
    """Coerce common boolean inputs."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "on", "yes", "1"}:
            return True
        if lowered in {"false", "off", "no", "0"}:
            return False
    raise VirtualValidationError("invalid_boolean")


def _validate_old_duplicate_switch_key(key: str, switches: list[dict[str, Any]]) -> None:
    """Validate switch keys for compatibility with old error tests."""
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
