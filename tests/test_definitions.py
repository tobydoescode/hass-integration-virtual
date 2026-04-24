"""Tests for virtual integration definition helpers."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from custom_components.virtual.const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_DEVICE_ID,
    CONF_SWITCHES,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
)
from custom_components.virtual.models import (
    VirtualValidationError,
    build_device_info,
    generate_device_id,
    generate_switch_key,
    normalize_connection,
    validate_unique_switch_key,
)


def test_generate_device_id_uses_virtual_prefix() -> None:
    """Generate an opaque virtual device id."""
    device_id = generate_device_id()

    assert device_id.startswith("virtual_")
    assert len(device_id) > len("virtual_")


def test_generate_switch_key_slugs_name_and_avoids_collisions() -> None:
    """Generate readable switch keys with suffixes for collisions."""
    existing = {"test_switch", "test_switch_2"}

    assert generate_switch_key("Test Switch", existing) == "test_switch_3"


def test_generate_switch_key_uses_fallback_for_empty_names() -> None:
    """Generate a useful switch key when a name has no slug characters."""
    assert generate_switch_key("!!!", set()) == "switch"


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


def test_validate_unique_switch_key_rejects_duplicates() -> None:
    """Duplicate switch keys in one device are rejected."""
    with pytest.raises(VirtualValidationError):
        validate_unique_switch_key("test", [{"key": "test"}])


def test_build_device_info_includes_identifier_and_mac_connection() -> None:
    """Device info contains virtual identifier and optional MAC connection."""
    info = build_device_info(
        {
            CONF_NAME: "Virtual Device",
            CONF_DEVICE_ID: "virtual_test",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
            CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
            CONF_SWITCHES: [],
        }
    )

    assert info["identifiers"] == {("virtual", "virtual_test")}
    assert info["connections"] == {(CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff")}
    assert info["name"] == "Virtual Device"
    assert info["manufacturer"] == "Virtual"
