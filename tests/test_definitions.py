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
    CONF_INITIAL_VALUE,
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


# ---------------------------------------------------------------------------
# validate_device_definition – entities not a list (models.py L95)
# ---------------------------------------------------------------------------
def test_validate_device_definition_rejects_entities_not_a_list() -> None:
    """Entities must be a list."""
    from custom_components.virtual.models import validate_device_definition

    device = {
        CONF_NAME: "Dev",
        CONF_DEVICE_ID: "virtual_d",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_ENTITIES: "not-a-list",
    }
    with pytest.raises(VirtualValidationError, match="invalid_entities"):
        validate_device_definition(device)


# ---------------------------------------------------------------------------
# validate_device_definition – entity not a dict (models.py L100)
# ---------------------------------------------------------------------------
def test_validate_device_definition_rejects_entity_not_a_dict() -> None:
    """Each entity must be a dict."""
    from custom_components.virtual.models import validate_device_definition

    device = {
        CONF_NAME: "Dev",
        CONF_DEVICE_ID: "virtual_d",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        CONF_ENTITIES: ["not-a-dict"],
    }
    with pytest.raises(VirtualValidationError, match="invalid_entity"):
        validate_device_definition(device)


# ---------------------------------------------------------------------------
# validate_entity_definition – invalid entity type (models.py L112)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_rejects_invalid_entity_type() -> None:
    """Invalid entity type is rejected."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_entity_type"):
        validate_entity_definition({CONF_ENTITY_TYPE: "invalid", CONF_NAME: "X", CONF_KEY: "x"})


# ---------------------------------------------------------------------------
# validate_entity_definition – optional key not a string (models.py L125)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_rejects_non_string_optional_field() -> None:
    """Optional metadata fields must be strings."""
    from custom_components.virtual.const import CONF_ICON
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_entity"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "S",
                CONF_KEY: "s",
                CONF_ICON: 123,
                CONF_INITIAL_VALUE: False,
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – light brightness (models.py L131)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_validates_light_brightness() -> None:
    """Light brightness is validated when present."""
    from custom_components.virtual.const import CONF_BRIGHTNESS, ENTITY_TYPE_LIGHT
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_brightness"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT,
                CONF_NAME: "L",
                CONF_KEY: "l",
                CONF_INITIAL_VALUE: True,
                CONF_BRIGHTNESS: 300,
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – sensor invalid value_type (models.py L135)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_rejects_invalid_sensor_value_type() -> None:
    """Sensor entities must have a valid value_type."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_value_type"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR,
                CONF_NAME: "S",
                CONF_KEY: "s",
                CONF_VALUE_TYPE: "invalid",
                CONF_INITIAL_VALUE: "x",
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – number entity (models.py L138-145)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_validates_number_entity() -> None:
    """Number entity with min > max is rejected."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_number"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
                CONF_NAME: "N",
                CONF_KEY: "n",
                CONF_INITIAL_VALUE: 5,
                CONF_MIN: 10,
                CONF_MAX: 0,
                CONF_STEP: 1,
            }
        )


def test_validate_entity_definition_validates_number_step_zero() -> None:
    """Number entity with step <= 0 is rejected."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_number"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
                CONF_NAME: "N",
                CONF_KEY: "n",
                CONF_INITIAL_VALUE: 5,
                CONF_MIN: 0,
                CONF_MAX: 10,
                CONF_STEP: 0,
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – select invalid options (models.py L155)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_rejects_invalid_select_options() -> None:
    """Select entities must have non-empty list of string options."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_options"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "S",
                CONF_KEY: "s",
                CONF_OPTIONS: [],
                CONF_INITIAL_VALUE: "x",
            }
        )


def test_validate_entity_definition_rejects_non_string_select_options() -> None:
    """Select options must all be non-empty strings."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_options"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "S",
                CONF_KEY: "s",
                CONF_OPTIONS: [123],
                CONF_INITIAL_VALUE: "x",
            }
        )


def test_validate_entity_definition_rejects_non_list_select_options() -> None:
    """Select options must be a list."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_options"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "S",
                CONF_KEY: "s",
                CONF_OPTIONS: "not-a-list",
                CONF_INITIAL_VALUE: "x",
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – text entity (models.py L157-167)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_validates_text_entity() -> None:
    """Text entity with min > max is rejected."""
    from custom_components.virtual.const import CONF_MODE
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_text"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT,
                CONF_NAME: "T",
                CONF_KEY: "t",
                CONF_INITIAL_VALUE: "hi",
                CONF_MIN: 10,
                CONF_MAX: 5,
                CONF_MODE: "text",
            }
        )


def test_validate_entity_definition_rejects_text_non_int_min() -> None:
    """Text entity with non-integer min is rejected."""
    from custom_components.virtual.const import CONF_MODE
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_text"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT,
                CONF_NAME: "T",
                CONF_KEY: "t",
                CONF_INITIAL_VALUE: "hi",
                CONF_MIN: "nope",
                CONF_MAX: 5,
                CONF_MODE: "text",
            }
        )


# ---------------------------------------------------------------------------
# validate_entity_definition – date/datetime/time entities (models.py L168-170)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_validates_date_entity() -> None:
    """Date entity with valid initial_value passes validation."""
    from custom_components.virtual.models import validate_entity_definition

    # Should not raise
    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_DATE,
            CONF_NAME: "D",
            CONF_KEY: "d",
            CONF_INITIAL_VALUE: "2026-01-01",
        }
    )


def test_validate_entity_definition_validates_datetime_entity() -> None:
    """Datetime entity with valid initial_value passes validation."""
    from custom_components.virtual.models import validate_entity_definition

    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME,
            CONF_NAME: "DT",
            CONF_KEY: "dt",
            CONF_INITIAL_VALUE: "2026-01-01T00:00:00+00:00",
        }
    )


def test_validate_entity_definition_validates_time_entity() -> None:
    """Time entity with valid initial_value passes validation."""
    from custom_components.virtual.models import validate_entity_definition

    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_TIME,
            CONF_NAME: "T",
            CONF_KEY: "t",
            CONF_INITIAL_VALUE: "12:00:00",
        }
    )


# ---------------------------------------------------------------------------
# validate_entity_definition – button entity (models.py L171-172)
# ---------------------------------------------------------------------------
def test_validate_entity_definition_accepts_button_entity() -> None:
    """Button entities pass validation without additional fields."""
    from custom_components.virtual.const import ENTITY_TYPE_BUTTON
    from custom_components.virtual.models import validate_entity_definition

    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_BUTTON,
            CONF_NAME: "B",
            CONF_KEY: "b",
        }
    )


# ---------------------------------------------------------------------------
# coerce_entity_value – date already a date object (models.py L219)
# ---------------------------------------------------------------------------
def test_coerce_date_value_accepts_date_object() -> None:
    """Date values that are already date objects pass through."""
    from datetime import date

    result = coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_DATE}, date(2026, 1, 1))
    assert result == date(2026, 1, 1)


# ---------------------------------------------------------------------------
# coerce_entity_value – datetime already a datetime object (models.py L225)
# ---------------------------------------------------------------------------
def test_coerce_datetime_value_accepts_datetime_object() -> None:
    """Datetime values that are already datetime objects pass through."""
    from datetime import datetime, timezone

    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME}, dt)
    assert result == dt


# ---------------------------------------------------------------------------
# coerce_entity_value – time already a time object (models.py L231)
# ---------------------------------------------------------------------------
def test_coerce_time_value_accepts_time_object() -> None:
    """Time values that are already time objects pass through."""
    from datetime import time

    t = time(12, 30, 0)
    result = coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_TIME}, t)
    assert result == t


# ---------------------------------------------------------------------------
# _validate_brightness – non-numeric value (models.py L242-247)
# ---------------------------------------------------------------------------
def test_validate_brightness_rejects_non_numeric() -> None:
    """Brightness must be a valid integer."""
    from custom_components.virtual.models import _validate_brightness

    with pytest.raises(VirtualValidationError, match="invalid_brightness"):
        _validate_brightness("not-a-number")


def test_validate_brightness_rejects_zero() -> None:
    """Brightness must be at least 1."""
    from custom_components.virtual.models import _validate_brightness

    with pytest.raises(VirtualValidationError, match="invalid_brightness"):
        _validate_brightness(0)


def test_validate_brightness_rejects_over_255() -> None:
    """Brightness must be at most 255."""
    from custom_components.virtual.models import _validate_brightness

    with pytest.raises(VirtualValidationError, match="invalid_brightness"):
        _validate_brightness(256)


# ---------------------------------------------------------------------------
# _coerce_float – non-numeric value (models.py L254-255)
# ---------------------------------------------------------------------------
def test_coerce_float_rejects_non_numeric() -> None:
    """Non-numeric values raise a validation error."""
    from custom_components.virtual.models import _coerce_float

    with pytest.raises(VirtualValidationError, match="invalid_number"):
        _coerce_float("not-a-number")


# ---------------------------------------------------------------------------
# _coerce_bool – false strings and invalid value (models.py L266-268)
# ---------------------------------------------------------------------------
def test_coerce_bool_recognizes_false_strings() -> None:
    """False-like strings are coerced to False."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR}

    for value in ("false", "off", "no", "0"):
        assert coerce_entity_value(definition, value) is False


def test_coerce_bool_rejects_invalid_value() -> None:
    """Non-boolean-like values raise a validation error."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR}

    with pytest.raises(VirtualValidationError, match="invalid_boolean"):
        coerce_entity_value(definition, "maybe")


def test_coerce_bool_rejects_non_string_non_bool() -> None:
    """Non-string, non-bool values raise a validation error."""
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR}

    with pytest.raises(VirtualValidationError, match="invalid_boolean"):
        coerce_entity_value(definition, 42)


# ---------------------------------------------------------------------------
# normalize_connection – custom connection type (models.py L287-298)
# ---------------------------------------------------------------------------
def test_normalize_custom_connection() -> None:
    """Custom connections store type, custom type, and value."""
    from custom_components.virtual.const import (
        CONF_CUSTOM_CONNECTION_TYPE,
        CONNECTION_TYPE_CUSTOM,
    )

    result = normalize_connection(CONNECTION_TYPE_CUSTOM, "my-value", "zigbee")
    assert result == {
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_CUSTOM,
        CONF_CUSTOM_CONNECTION_TYPE: "zigbee",
        CONF_CONNECTION_VALUE: "my-value",
    }


def test_normalize_custom_connection_rejects_empty_custom_type() -> None:
    """Custom connections require a non-empty custom type."""
    from custom_components.virtual.const import CONNECTION_TYPE_CUSTOM

    with pytest.raises(VirtualValidationError, match="invalid_connection"):
        normalize_connection(CONNECTION_TYPE_CUSTOM, "value", "")


def test_normalize_custom_connection_rejects_empty_value() -> None:
    """Custom connections require a non-empty value."""
    from custom_components.virtual.const import CONNECTION_TYPE_CUSTOM

    with pytest.raises(VirtualValidationError, match="invalid_connection"):
        normalize_connection(CONNECTION_TYPE_CUSTOM, "", "zigbee")


def test_normalize_connection_rejects_unknown_type() -> None:
    """Unknown connection types raise a validation error."""
    with pytest.raises(VirtualValidationError, match="invalid_connection_type"):
        normalize_connection("unknown", "value", None)


# ---------------------------------------------------------------------------
# connection_tuple – custom connection (models.py L322-327)
# ---------------------------------------------------------------------------
def test_connection_tuple_custom() -> None:
    """Custom connections return a tuple of (custom_type, value)."""
    from custom_components.virtual.const import (
        CONF_CUSTOM_CONNECTION_TYPE,
        CONNECTION_TYPE_CUSTOM,
    )
    from custom_components.virtual.models import connection_tuple

    device = {
        CONF_NAME: "Dev",
        CONF_DEVICE_ID: "virtual_d",
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_CUSTOM,
        CONF_CUSTOM_CONNECTION_TYPE: "zigbee",
        CONF_CONNECTION_VALUE: "my-value",
        CONF_ENTITIES: [],
    }
    assert connection_tuple(device) == ("zigbee", "my-value")


def test_connection_tuple_unknown_type_returns_none() -> None:
    """Unknown connection types return None."""
    from custom_components.virtual.models import connection_tuple

    device = {
        CONF_NAME: "Dev",
        CONF_DEVICE_ID: "virtual_d",
        CONF_CONNECTION_TYPE: "unknown",
        CONF_ENTITIES: [],
    }
    assert connection_tuple(device) is None


# ---------------------------------------------------------------------------
# coerce_entity_value – unknown entity type fallback (models.py L225)
# ---------------------------------------------------------------------------
def test_coerce_entity_value_unknown_type_returns_raw_value() -> None:
    """Unknown entity types return the raw value."""
    result = coerce_entity_value({CONF_ENTITY_TYPE: "unknown_type"}, "raw")
    assert result == "raw"


# ---------------------------------------------------------------------------
# Additional number validation
# ---------------------------------------------------------------------------
def test_coerce_number_rejects_below_minimum() -> None:
    """Number values below minimum are rejected."""
    definition = {
        CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
        CONF_MIN: 5,
        CONF_MAX: 10,
        CONF_STEP: 1,
    }
    with pytest.raises(VirtualValidationError, match="invalid_number"):
        coerce_entity_value(definition, 4)


def test_validate_entity_definition_valid_number() -> None:
    """Valid number entity passes validation."""
    from custom_components.virtual.models import validate_entity_definition

    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
            CONF_NAME: "N",
            CONF_KEY: "n",
            CONF_INITIAL_VALUE: 5,
            CONF_MIN: 0,
            CONF_MAX: 10,
            CONF_STEP: 1,
        }
    )


def test_validate_entity_definition_valid_text() -> None:
    """Valid text entity passes validation."""
    from custom_components.virtual.const import CONF_MODE
    from custom_components.virtual.models import validate_entity_definition

    validate_entity_definition(
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT,
            CONF_NAME: "T",
            CONF_KEY: "t",
            CONF_INITIAL_VALUE: "hi",
            CONF_MIN: 0,
            CONF_MAX: 10,
            CONF_MODE: "text",
        }
    )


# ---------------------------------------------------------------------------
# _require_key – missing key raises (models.py L231)
# ---------------------------------------------------------------------------
def test_require_key_raises_on_missing_key() -> None:
    """Missing required key in entity definition raises error."""
    from custom_components.virtual.models import validate_entity_definition

    # Switch without initial_value triggers _require_key
    with pytest.raises(VirtualValidationError, match="missing_initial_value"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "S",
                CONF_KEY: "s",
            }
        )


# ---------------------------------------------------------------------------
# _validate_non_empty_string – empty/missing name (models.py L237)
# ---------------------------------------------------------------------------
def test_validate_non_empty_string_rejects_empty_name() -> None:
    """Entity with empty name raises error."""
    from custom_components.virtual.models import validate_entity_definition

    with pytest.raises(VirtualValidationError, match="invalid_entity"):
        validate_entity_definition(
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "",
                CONF_KEY: "s",
                CONF_INITIAL_VALUE: False,
            }
        )
