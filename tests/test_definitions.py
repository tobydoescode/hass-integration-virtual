"""Tests for virtual integration definition helpers."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from custom_components.virtual.const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_TYPE,
    CONF_KEY,
    CONF_MAX,
    CONF_MIN,
    CONF_OPTIONS,
    CONF_STEP,
    CONF_VALUE_TYPE,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
)
from custom_components.virtual.models import (
    VirtualValidationError,
    build_device_info,
    coerce_entity_value,
    entities_for_platform,
    entity_unique_id,
    generate_device_id,
    generate_entity_key,
    normalize_connection,
    validate_unique_entity_key,
)


def test_generate_device_id_uses_virtual_prefix() -> None:
    """Generate an opaque virtual device id."""
    device_id = generate_device_id()

    assert device_id.startswith("virtual_")
    assert len(device_id) > len("virtual_")


def test_generate_entity_key_slugs_name_and_avoids_collisions() -> None:
    """Generate readable entity keys with suffixes for collisions."""
    assert generate_entity_key("Test Entity", {"test_entity", "test_entity_2"}) == ("test_entity_3")


def test_generate_entity_key_uses_fallback_for_empty_names() -> None:
    """Generate a useful entity key when a name has no slug characters."""
    assert generate_entity_key("!!!", set()) == "switch"


def test_validate_unique_entity_key_rejects_duplicate_across_types() -> None:
    """Duplicate entity keys are rejected across all entity types."""
    with pytest.raises(VirtualValidationError):
        validate_unique_entity_key(
            "temperature",
            [{CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_KEY: "temperature"}],
        )


def test_entities_for_platform_filters_by_type() -> None:
    """Return only entity definitions for a platform."""
    device = {
        CONF_ENTITIES: [
            {CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH, CONF_KEY: "power"},
            {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_KEY: "temperature"},
        ]
    }

    assert entities_for_platform(device, Platform.SWITCH) == [
        {CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH, CONF_KEY: "power"}
    ]


def test_entity_unique_id_uses_device_id_and_key() -> None:
    """Entity unique IDs use device ID and entity key."""
    assert entity_unique_id("virtual_device", "temperature") == "virtual_device_temperature"


def test_coerce_boolean_value() -> None:
    """Boolean entity values are coerced from common inputs."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR}

    assert coerce_entity_value(definition, "true") is True
    assert coerce_entity_value(definition, False) is False


def test_coerce_sensor_number_value() -> None:
    """Numeric sensors coerce values to floats."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_VALUE_TYPE: "number"}

    assert coerce_entity_value(definition, "21.5") == 21.5


def test_coerce_sensor_string_value() -> None:
    """String sensors coerce values to strings."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_VALUE_TYPE: "string"}

    assert coerce_entity_value(definition, 21.5) == "21.5"


def test_coerce_number_rejects_out_of_range() -> None:
    """Number values must stay inside min/max."""
    definition = {
        CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
        CONF_MIN: 0,
        CONF_MAX: 10,
        CONF_STEP: 1,
    }

    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, 11)


def test_coerce_select_rejects_unknown_option() -> None:
    """Select values must be one of the configured options."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT, CONF_OPTIONS: ["a", "b"]}

    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, "c")


def test_coerce_text_rejects_invalid_length() -> None:
    """Text values must obey min/max lengths."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT, CONF_MIN: 2, CONF_MAX: 4}

    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, "abcde")


def test_coerce_date_time_datetime_values() -> None:
    """Date-like values are parsed from ISO strings."""
    assert str(coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_DATE}, "2026-04-25")) == (
        "2026-04-25"
    )
    assert str(coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_TIME}, "13:45:00")) == (
        "13:45:00"
    )
    assert (
        coerce_entity_value(
            {CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME}, "2026-04-25T13:45:00+00:00"
        ).isoformat()
        == "2026-04-25T13:45:00+00:00"
    )


def test_normalize_none_connection() -> None:
    """Connection type none stores no connection value."""
    assert normalize_connection(CONNECTION_TYPE_NONE, "", "") == {
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE
    }


def test_normalize_mac_connection() -> None:
    """MAC addresses are normalized to lowercase colon-separated form."""
    assert normalize_connection(CONNECTION_TYPE_MAC, "AABB.CCDD.EEFF", "") == {
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
        CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
    }


def test_normalize_mac_connection_rejects_invalid_mac() -> None:
    """Invalid MAC addresses raise a validation error."""
    with pytest.raises(VirtualValidationError):
        normalize_connection(CONNECTION_TYPE_MAC, "not-a-mac", "")


def test_build_device_info_includes_identifier_and_mac_connection() -> None:
    """Device info contains virtual identifier and optional MAC connection."""
    info = build_device_info(
        {
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_test",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
            CONF_ENTITIES: [],
        }
    )

    assert info["identifiers"] == {("virtual", "virtual_test")}
    assert info["connections"] == {(CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff")}
    assert info["name"] == "Virtual Device"
    assert info["manufacturer"] == "Virtual"
