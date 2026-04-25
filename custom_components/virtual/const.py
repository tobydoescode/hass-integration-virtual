"""Constants for the Virtual integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "virtual"
MANUFACTURER = "Virtual"

PLATFORMS = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
    Platform.DATE,
    Platform.DATETIME,
    Platform.TIME,
]

CONF_DEVICE_ID = "device_id"
CONF_ENTITIES = "entities"
CONF_ENTITY_TYPE = "type"
CONF_SWITCHES = "switches"
CONF_KEY = "key"
CONF_ICON = "icon"
CONF_ENTITY_CATEGORY = "entity_category"
CONF_DEVICE_CLASS = "device_class"
CONF_INITIAL_VALUE = "initial_value"
CONF_VALUE_TYPE = "value_type"
CONF_NATIVE_UNIT_OF_MEASUREMENT = "native_unit_of_measurement"
CONF_STATE_CLASS = "state_class"
CONF_MIN = "min"
CONF_MAX = "max"
CONF_STEP = "step"
CONF_MODE = "mode"
CONF_OPTIONS = "options"
CONF_BRIGHTNESS = "brightness"
CONF_CONNECTION_TYPE = "connection_type"
CONF_CONNECTION_VALUE = "connection_value"
CONF_CUSTOM_CONNECTION_TYPE = "custom_connection_type"

SERVICE_SET_STATE = "set_state"
ATTR_VALUE = "value"

ENTITY_TYPE_SWITCH = Platform.SWITCH.value
ENTITY_TYPE_BINARY_SENSOR = Platform.BINARY_SENSOR.value
ENTITY_TYPE_SENSOR = Platform.SENSOR.value
ENTITY_TYPE_BUTTON = Platform.BUTTON.value
ENTITY_TYPE_LIGHT = Platform.LIGHT.value
ENTITY_TYPE_NUMBER = Platform.NUMBER.value
ENTITY_TYPE_SELECT = Platform.SELECT.value
ENTITY_TYPE_TEXT = Platform.TEXT.value
ENTITY_TYPE_DATE = Platform.DATE.value
ENTITY_TYPE_DATETIME = Platform.DATETIME.value
ENTITY_TYPE_TIME = Platform.TIME.value

SUPPORTED_ENTITY_TYPES = [
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_BUTTON,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_TIME,
]

CONNECTION_TYPE_NONE = "none"
CONNECTION_TYPE_MAC = "mac"
CONNECTION_TYPE_CUSTOM = "custom"
