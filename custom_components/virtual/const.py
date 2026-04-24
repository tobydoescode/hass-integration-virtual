"""Constants for the Virtual integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "virtual"
MANUFACTURER = "Virtual"

PLATFORMS = [Platform.SWITCH]

CONF_DEVICE_ID = "device_id"
CONF_SWITCHES = "switches"
CONF_KEY = "key"
CONF_ICON = "icon"
CONF_ENTITY_CATEGORY = "entity_category"
CONF_DEVICE_CLASS = "device_class"
CONF_CONNECTION_TYPE = "connection_type"
CONF_CONNECTION_VALUE = "connection_value"
CONF_CUSTOM_CONNECTION_TYPE = "custom_connection_type"

CONNECTION_TYPE_NONE = "none"
CONNECTION_TYPE_MAC = "mac"
CONNECTION_TYPE_CUSTOM = "custom"

