"""Definition helpers for the Virtual integration."""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any
from uuid import uuid4

from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from slugify import slugify

from .const import (
    CONF_BRIGHTNESS,
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_CUSTOM_CONNECTION_TYPE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_TYPE,
    CONF_ICON,
    CONF_INITIAL_VALUE,
    CONF_KEY,
    CONF_MAX,
    CONF_MIN,
    CONF_MODE,
    CONF_NATIVE_UNIT_OF_MEASUREMENT,
    CONF_OPTIONS,
    CONF_STATE_CLASS,
    CONF_STEP,
    CONF_VALUE_TYPE,
    CONNECTION_TYPE_CUSTOM,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_BUTTON,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
    MANUFACTURER,
    SUPPORTED_ENTITY_TYPES,
)

MAC_HEX_RE = re.compile(r"^[0-9a-f]{12}$")


class VirtualValidationError(ValueError):
    """Raised when a virtual definition is invalid."""


def generate_device_id() -> str:
    """Generate a stable virtual device id."""
    return f"virtual_{uuid4().hex}"


def generate_entity_key(name: str, existing_keys: set[str]) -> str:
    """Generate a readable entity key that does not collide."""
    base = slugify(name, separator="_") or "switch"
    key = base
    suffix = 2
    while key in existing_keys:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def validate_unique_entity_key(key: str, entities: list[dict[str, Any]]) -> None:
    """Validate that an entity key is not already used in this device."""
    if any(entity.get(CONF_KEY) == key for entity in entities):
        raise VirtualValidationError("duplicate_entity_key")


def validate_device_definition(device: dict[str, Any]) -> None:
    """Validate a virtual device definition."""
    _validate_non_empty_string(device, CONF_NAME, "invalid_device")
    _validate_non_empty_string(device, CONF_DEVICE_ID, "invalid_device")
    normalize_connection(
        device.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_NONE),
        device.get(CONF_CONNECTION_VALUE),
        device.get(CONF_CUSTOM_CONNECTION_TYPE),
    )

    entities = device.get(CONF_ENTITIES, [])
    if not isinstance(entities, list):
        raise VirtualValidationError("invalid_entities")

    seen_keys: set[str] = set()
    for entity in entities:
        if not isinstance(entity, dict):
            raise VirtualValidationError("invalid_entity")
        key = entity.get(CONF_KEY)
        if key in seen_keys:
            raise VirtualValidationError("duplicate_entity_key")
        seen_keys.add(key)
        validate_entity_definition(entity)


def validate_entity_definition(entity: dict[str, Any]) -> None:
    """Validate a virtual entity definition."""
    entity_type = entity.get(CONF_ENTITY_TYPE)
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise VirtualValidationError("invalid_entity_type")
    _validate_non_empty_string(entity, CONF_NAME, "invalid_entity")
    _validate_non_empty_string(entity, CONF_KEY, "invalid_entity")

    for optional_key in (
        CONF_ICON,
        CONF_ENTITY_CATEGORY,
        CONF_DEVICE_CLASS,
        CONF_NATIVE_UNIT_OF_MEASUREMENT,
        CONF_STATE_CLASS,
        CONF_MODE,
    ):
        if optional_key in entity and not isinstance(entity[optional_key], str):
            raise VirtualValidationError("invalid_entity")

    if entity_type in {ENTITY_TYPE_SWITCH, ENTITY_TYPE_BINARY_SENSOR, ENTITY_TYPE_LIGHT}:
        _require_key(entity, CONF_INITIAL_VALUE)
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
        if entity_type == ENTITY_TYPE_LIGHT and CONF_BRIGHTNESS in entity:
            _validate_brightness(entity[CONF_BRIGHTNESS])
    elif entity_type == ENTITY_TYPE_SENSOR:
        _require_key(entity, CONF_INITIAL_VALUE)
        if entity.get(CONF_VALUE_TYPE) not in {"string", "number"}:
            raise VirtualValidationError("invalid_value_type")
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_NUMBER:
        for key in (CONF_INITIAL_VALUE, CONF_MIN, CONF_MAX, CONF_STEP):
            _require_key(entity, key)
        minimum = _coerce_float(entity[CONF_MIN])
        maximum = _coerce_float(entity[CONF_MAX])
        step = _coerce_float(entity[CONF_STEP])
        if minimum > maximum or step <= 0:
            raise VirtualValidationError("invalid_number")
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_SELECT:
        _require_key(entity, CONF_OPTIONS)
        _require_key(entity, CONF_INITIAL_VALUE)
        options = entity[CONF_OPTIONS]
        if (
            not isinstance(options, list)
            or not options
            or not all(isinstance(option, str) and option for option in options)
        ):
            raise VirtualValidationError("invalid_options")
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_TEXT:
        for key in (CONF_INITIAL_VALUE, CONF_MIN, CONF_MAX, CONF_MODE):
            _require_key(entity, key)
        try:
            minimum = int(entity[CONF_MIN])
            maximum = int(entity[CONF_MAX])
        except (TypeError, ValueError) as err:
            raise VirtualValidationError("invalid_text") from err
        if minimum > maximum:
            raise VirtualValidationError("invalid_text")
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
    elif entity_type in {ENTITY_TYPE_DATE, ENTITY_TYPE_DATETIME, ENTITY_TYPE_TIME}:
        _require_key(entity, CONF_INITIAL_VALUE)
        coerce_entity_value(entity, entity[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_BUTTON:
        return


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
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        return date.fromisoformat(str(value))
    if entity_type == ENTITY_TYPE_TIME:
        return value if isinstance(value, time) else time.fromisoformat(str(value))
    if entity_type == ENTITY_TYPE_DATETIME:
        return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return value


def _require_key(value: dict[str, Any], key: str) -> None:
    """Validate that a definition contains a required key."""
    if key not in value:
        raise VirtualValidationError(f"missing_{key}")


def _validate_non_empty_string(value: dict[str, Any], key: str, error: str) -> None:
    """Validate that a definition key contains a non-empty string."""
    if not isinstance(value.get(key), str) or not value[key]:
        raise VirtualValidationError(error)


def _validate_brightness(value: Any) -> None:
    """Validate light brightness."""
    try:
        brightness = int(value)
    except (TypeError, ValueError) as err:
        raise VirtualValidationError("invalid_brightness") from err
    if brightness < 1 or brightness > 255:
        raise VirtualValidationError("invalid_brightness")


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


def _normalize_mac(value: str) -> str:
    """Normalize MAC addresses to lowercase colon-separated form."""
    compact = re.sub(r"[^0-9a-fA-F]", "", value).lower()
    if not MAC_HEX_RE.match(compact):
        raise VirtualValidationError("invalid_mac")
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2))
