"""Config flow for the Virtual integration."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import voluptuous as vol
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorStateClass
from homeassistant.components.text import TextMode
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

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
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_TIME,
    SUPPORTED_ENTITY_TYPES,
)
from .models import (
    VirtualValidationError,
    coerce_entity_value,
    entity_unique_id,
    generate_device_id,
    generate_entity_key,
    normalize_connection,
    validate_entity_definition,
    validate_unique_entity_key,
)

CONF_ACTION = "action"
CONF_ADD_ENTITY = "add_entity"
CONF_CONFIRM = "confirm"
CONF_ENTITY_KEYS = "entity_keys"

ACTION_EDIT_DEVICE = "edit_device"
ACTION_ADD_ENTITY = "add_entity"
ACTION_EDIT_ENTITY = "edit_entity"
ACTION_REMOVE_ENTITY = "remove_entity"

CONNECTION_TYPES = [CONNECTION_TYPE_NONE, CONNECTION_TYPE_MAC, CONNECTION_TYPE_CUSTOM]
ENTITY_CATEGORIES = ["", "config", "diagnostic"]
VALUE_TYPES = ["string", "number"]
NUMBER_MODES = [mode.value for mode in NumberMode]
TEXT_MODES = [mode.value for mode in TextMode]
SENSOR_STATE_CLASSES = ["", *[state_class.value for state_class in SensorStateClass]]
OPTIONS_ACTIONS = [
    ACTION_EDIT_DEVICE,
    ACTION_ADD_ENTITY,
    ACTION_EDIT_ENTITY,
    ACTION_REMOVE_ENTITY,
]


def _device_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return schema for device details."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Optional(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
            vol.Required(
                CONF_CONNECTION_TYPE,
                default=defaults.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_NONE),
            ): vol.In(CONNECTION_TYPES),
            vol.Optional(
                CONF_CONNECTION_VALUE,
                default=defaults.get(CONF_CONNECTION_VALUE, ""),
            ): str,
            vol.Optional(
                CONF_CUSTOM_CONNECTION_TYPE,
                default=defaults.get(CONF_CUSTOM_CONNECTION_TYPE, ""),
            ): str,
        }
    )


def _entity_type_schema() -> vol.Schema:
    """Return schema for choosing an entity type."""
    return vol.Schema({vol.Required(CONF_ENTITY_TYPE): vol.In(SUPPORTED_ENTITY_TYPES)})


def _entity_schema(
    entity_type: str,
    defaults: dict[str, Any] | None = None,
    *,
    include_key: bool = True,
) -> vol.Schema:
    """Return schema for entity details."""
    defaults = defaults or {}
    fields: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
    }
    if include_key:
        fields[vol.Optional(CONF_KEY, default=defaults.get(CONF_KEY, ""))] = str
    fields.update(
        {
            vol.Optional(CONF_ICON, default=defaults.get(CONF_ICON, "")): str,
            vol.Optional(
                CONF_ENTITY_CATEGORY,
                default=defaults.get(CONF_ENTITY_CATEGORY, ""),
            ): vol.In(ENTITY_CATEGORIES),
            vol.Optional(CONF_DEVICE_CLASS, default=defaults.get(CONF_DEVICE_CLASS, "")): str,
        }
    )

    if entity_type in {ENTITY_TYPE_SWITCH, ENTITY_TYPE_BINARY_SENSOR}:
        fields[
            vol.Required(
                CONF_INITIAL_VALUE,
                default=defaults.get(CONF_INITIAL_VALUE, False),
            )
        ] = bool
    elif entity_type == ENTITY_TYPE_SENSOR:
        fields.update(
            {
                vol.Required(
                    CONF_VALUE_TYPE,
                    default=defaults.get(CONF_VALUE_TYPE, "string"),
                ): vol.In(VALUE_TYPES),
                vol.Required(CONF_INITIAL_VALUE, default=defaults.get(CONF_INITIAL_VALUE, "")): str,
                vol.Optional(
                    CONF_NATIVE_UNIT_OF_MEASUREMENT,
                    default=defaults.get(CONF_NATIVE_UNIT_OF_MEASUREMENT, ""),
                ): str,
                vol.Optional(
                    CONF_STATE_CLASS,
                    default=defaults.get(CONF_STATE_CLASS, ""),
                ): vol.In(SENSOR_STATE_CLASSES),
            }
        )
    elif entity_type == ENTITY_TYPE_LIGHT:
        fields.update(
            {
                vol.Required(
                    CONF_INITIAL_VALUE,
                    default=defaults.get(CONF_INITIAL_VALUE, False),
                ): bool,
                vol.Optional(CONF_BRIGHTNESS, default=defaults.get(CONF_BRIGHTNESS, "")): str,
            }
        )
    elif entity_type == ENTITY_TYPE_NUMBER:
        fields.update(
            {
                vol.Required(
                    CONF_INITIAL_VALUE,
                    default=defaults.get(CONF_INITIAL_VALUE, 0),
                ): vol.Coerce(float),
                vol.Required(CONF_MIN, default=defaults.get(CONF_MIN, 0)): vol.Coerce(float),
                vol.Required(CONF_MAX, default=defaults.get(CONF_MAX, 100)): vol.Coerce(float),
                vol.Required(CONF_STEP, default=defaults.get(CONF_STEP, 1)): vol.Coerce(float),
                vol.Optional(
                    CONF_NATIVE_UNIT_OF_MEASUREMENT,
                    default=defaults.get(CONF_NATIVE_UNIT_OF_MEASUREMENT, ""),
                ): str,
                vol.Required(
                    CONF_MODE,
                    default=defaults.get(CONF_MODE, NumberMode.AUTO.value),
                ): vol.In(NUMBER_MODES),
            }
        )
    elif entity_type == ENTITY_TYPE_SELECT:
        fields.update(
            {
                vol.Required(CONF_OPTIONS, default=_options_default(defaults)): str,
                vol.Required(CONF_INITIAL_VALUE, default=defaults.get(CONF_INITIAL_VALUE, "")): str,
            }
        )
    elif entity_type == ENTITY_TYPE_TEXT:
        fields.update(
            {
                vol.Required(CONF_INITIAL_VALUE, default=defaults.get(CONF_INITIAL_VALUE, "")): str,
                vol.Required(CONF_MIN, default=defaults.get(CONF_MIN, 0)): vol.Coerce(int),
                vol.Required(CONF_MAX, default=defaults.get(CONF_MAX, 255)): vol.Coerce(int),
                vol.Required(
                    CONF_MODE,
                    default=defaults.get(CONF_MODE, TextMode.TEXT.value),
                ): vol.In(TEXT_MODES),
            }
        )
    elif entity_type in {ENTITY_TYPE_DATE, ENTITY_TYPE_DATETIME, ENTITY_TYPE_TIME}:
        fields[vol.Required(CONF_INITIAL_VALUE, default=defaults.get(CONF_INITIAL_VALUE, ""))] = str

    return vol.Schema(fields)


class VirtualConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device: dict[str, Any] = {}
        self._entities: list[dict[str, Any]] = []
        self._selected_entity_type: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle virtual device details."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = (user_input.get(CONF_DEVICE_ID) or "").strip() or generate_device_id()
            if self._device_id_exists(device_id):
                errors["base"] = "duplicate_device_id"
            else:
                try:
                    connection = normalize_connection(
                        user_input[CONF_CONNECTION_TYPE],
                        user_input.get(CONF_CONNECTION_VALUE),
                        user_input.get(CONF_CUSTOM_CONNECTION_TYPE),
                    )
                except VirtualValidationError as err:
                    errors["base"] = str(err)
                else:
                    self._device = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_ID: device_id,
                        **connection,
                    }
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()
                    return await self.async_step_entity_menu()

        return self.async_show_form(step_id="user", data_schema=_device_schema(), errors=errors)

    async def async_step_entity_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask whether to add another entity."""
        if user_input is not None:
            if user_input[CONF_ADD_ENTITY]:
                return await self.async_step_add_entity_type()
            return self.async_create_entry(
                title=self._device[CONF_NAME],
                data={**self._device, CONF_ENTITIES: self._entities},
            )

        return self.async_show_form(
            step_id="entity_menu",
            data_schema=vol.Schema({vol.Required(CONF_ADD_ENTITY, default=False): bool}),
        )

    async def async_step_add_entity_type(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the entity type to add."""
        if user_input is not None:
            self._selected_entity_type = user_input[CONF_ENTITY_TYPE]
            return await self.async_step_add_entity()

        return self.async_show_form(step_id="add_entity_type", data_schema=_entity_type_schema())

    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add an entity to the virtual device."""
        entity_type = self._selected_entity_type
        if entity_type is None:
            return await self.async_step_add_entity_type()

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                entity = _entity_from_input(
                    entity_type,
                    user_input,
                    self._entities,
                )
            except VirtualValidationError as err:
                errors["base"] = str(err)
            else:
                self._entities.append(entity)
                self._selected_entity_type = None
                return await self.async_step_entity_menu()

        return self.async_show_form(
            step_id="add_entity",
            data_schema=_entity_schema(entity_type),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return VirtualOptionsFlow(config_entry)

    def _device_id_exists(self, device_id: str) -> bool:
        """Return true if another config entry already uses the device id."""
        return any(
            entry.data.get(CONF_DEVICE_ID) == device_id for entry in self._async_current_entries()
        )


class VirtualOptionsFlow(OptionsFlow):
    """Handle options for Virtual."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._selected_entity_key: str | None = None
        self._selected_entity_type: str | None = None
        self._selected_remove_keys: list[str] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose an options action."""
        if user_input is not None:
            action = user_input[CONF_ACTION]
            if action == ACTION_EDIT_DEVICE:
                return await self.async_step_edit_device()
            if action == ACTION_ADD_ENTITY:
                return await self.async_step_add_entity_type()
            if action == ACTION_EDIT_ENTITY:
                return await self.async_step_select_entity()
            if action == ACTION_REMOVE_ENTITY:
                return await self.async_step_remove_entity()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_ACTION): vol.In(OPTIONS_ACTIONS)}),
        )

    async def async_step_edit_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit device metadata."""
        errors: dict[str, str] = {}
        current = self._config_entry.data
        if user_input is not None:
            try:
                connection = normalize_connection(
                    user_input[CONF_CONNECTION_TYPE],
                    user_input.get(CONF_CONNECTION_VALUE),
                    user_input.get(CONF_CUSTOM_CONNECTION_TYPE),
                )
            except VirtualValidationError as err:
                errors["base"] = str(err)
            else:
                new_data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_DEVICE_ID: current[CONF_DEVICE_ID],
                    **connection,
                    CONF_ENTITIES: current.get(CONF_ENTITIES, []),
                }
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    title=user_input[CONF_NAME],
                    data=new_data,
                )
                return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="edit_device",
            data_schema=_device_schema(current),
            errors=errors,
        )

    async def async_step_add_entity_type(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the entity type to add."""
        if user_input is not None:
            self._selected_entity_type = user_input[CONF_ENTITY_TYPE]
            return await self.async_step_add_entity()

        return self.async_show_form(step_id="add_entity_type", data_schema=_entity_type_schema())

    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add an entity to an existing virtual device."""
        entity_type = self._selected_entity_type
        if entity_type is None:
            return await self.async_step_add_entity_type()

        errors: dict[str, str] = {}
        current = self._config_entry.data
        entities = list(current.get(CONF_ENTITIES, []))
        if user_input is not None:
            try:
                entity = _entity_from_input(entity_type, user_input, entities)
            except VirtualValidationError as err:
                errors["base"] = str(err)
            else:
                entities.append(entity)
                self._update_entry_data({**current, CONF_ENTITIES: entities})
                self._selected_entity_type = None
                return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="add_entity",
            data_schema=_entity_schema(entity_type),
            errors=errors,
        )

    async def async_step_select_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select an entity to edit."""
        entities = self._config_entry.data.get(CONF_ENTITIES, [])
        key_options = [entity[CONF_KEY] for entity in entities]
        if user_input is not None:
            self._selected_entity_key = user_input[CONF_KEY]
            return await self.async_step_edit_entity()

        return self.async_show_form(
            step_id="select_entity",
            data_schema=vol.Schema({vol.Required(CONF_KEY): vol.In(key_options)}),
        )

    async def async_step_edit_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit entity metadata and type-specific fields."""
        current = self._config_entry.data
        entities = list(current.get(CONF_ENTITIES, []))
        entity = self._entity_by_key(self._selected_entity_key)
        entity_type = entity[CONF_ENTITY_TYPE]

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                other_entities = [
                    candidate for candidate in entities if candidate[CONF_KEY] != entity[CONF_KEY]
                ]
                updated = _entity_from_input(
                    entity_type,
                    user_input,
                    other_entities,
                    key_override=entity[CONF_KEY],
                )
            except VirtualValidationError as err:
                errors["base"] = str(err)
            else:
                updated_entities = [
                    updated if existing[CONF_KEY] == entity[CONF_KEY] else existing
                    for existing in entities
                ]
                self._update_entry_data({**current, CONF_ENTITIES: updated_entities})
                return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="edit_entity",
            data_schema=_entity_schema(entity_type, entity, include_key=False),
            errors=errors,
        )

    async def async_step_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select entities to remove."""
        entities = self._config_entry.data.get(CONF_ENTITIES, [])
        key_options = [entity[CONF_KEY] for entity in entities]
        if user_input is not None:
            self._selected_remove_keys = list(user_input[CONF_ENTITY_KEYS])
            return await self.async_step_confirm_remove_entity()

        return self.async_show_form(
            step_id="remove_entity",
            data_schema=vol.Schema(
                {vol.Required(CONF_ENTITY_KEYS): vol.All(list, [vol.In(key_options)])}
            ),
        )

    async def async_step_confirm_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm hard removal of entities."""
        if user_input is not None:
            if user_input[CONF_CONFIRM]:
                self._remove_entities(self._selected_remove_keys)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm_remove_entity",
            data_schema=vol.Schema({vol.Required(CONF_CONFIRM, default=False): bool}),
        )

    def _entity_by_key(self, key: str | None) -> dict[str, Any]:
        """Return an entity definition by key."""
        for entity in self._config_entry.data.get(CONF_ENTITIES, []):
            if entity[CONF_KEY] == key:
                return entity
        raise VirtualValidationError("unknown_entity")

    def _remove_entities(self, keys: list[str]) -> None:
        """Remove entity definitions and matching entity registry entries."""
        current = self._config_entry.data
        remove_keys = set(keys)
        entity_registry = er.async_get(self.hass)
        for entity in current.get(CONF_ENTITIES, []):
            if entity[CONF_KEY] not in remove_keys:
                continue
            unique_id = entity_unique_id(current[CONF_DEVICE_ID], entity[CONF_KEY])
            if entity_id := entity_registry.async_get_entity_id(
                Platform(entity[CONF_ENTITY_TYPE]),
                DOMAIN,
                unique_id,
            ):
                entity_registry.async_remove(entity_id)

        entities = [
            entity
            for entity in current.get(CONF_ENTITIES, [])
            if entity[CONF_KEY] not in remove_keys
        ]
        self._update_entry_data({**current, CONF_ENTITIES: entities})

    def _update_entry_data(self, data: dict[str, Any]) -> None:
        """Update the config entry data."""
        self.hass.config_entries.async_update_entry(self._config_entry, data=data)


def _entity_from_input(  # noqa: C901
    entity_type: str,
    user_input: dict[str, Any],
    existing_entities: list[dict[str, Any]],
    *,
    key_override: str | None = None,
) -> dict[str, Any]:
    """Build an entity definition from flow input."""
    key = key_override or (user_input.get(CONF_KEY) or "").strip()
    if not key:
        key = generate_entity_key(
            user_input[CONF_NAME],
            {entity[CONF_KEY] for entity in existing_entities},
        )
    validate_unique_entity_key(key, existing_entities)

    entity: dict[str, Any] = {
        CONF_ENTITY_TYPE: entity_type,
        CONF_NAME: user_input[CONF_NAME],
        CONF_KEY: key,
        CONF_ICON: user_input.get(CONF_ICON, ""),
        CONF_ENTITY_CATEGORY: user_input.get(CONF_ENTITY_CATEGORY, ""),
        CONF_DEVICE_CLASS: user_input.get(CONF_DEVICE_CLASS, ""),
    }

    if entity_type in {ENTITY_TYPE_SWITCH, ENTITY_TYPE_BINARY_SENSOR}:
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_SENSOR:
        entity[CONF_VALUE_TYPE] = user_input[CONF_VALUE_TYPE]
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
        entity[CONF_NATIVE_UNIT_OF_MEASUREMENT] = user_input.get(
            CONF_NATIVE_UNIT_OF_MEASUREMENT, ""
        )
        entity[CONF_STATE_CLASS] = user_input.get(CONF_STATE_CLASS, "")
    elif entity_type == ENTITY_TYPE_LIGHT:
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
        brightness = user_input.get(CONF_BRIGHTNESS, "")
        if brightness != "":
            brightness_int = int(brightness)
            if brightness_int < 1 or brightness_int > 255:
                raise VirtualValidationError("invalid_brightness")
            entity[CONF_BRIGHTNESS] = brightness_int
    elif entity_type == ENTITY_TYPE_NUMBER:
        entity[CONF_MIN] = float(user_input[CONF_MIN])
        entity[CONF_MAX] = float(user_input[CONF_MAX])
        entity[CONF_STEP] = float(user_input[CONF_STEP])
        if entity[CONF_MIN] > entity[CONF_MAX] or entity[CONF_STEP] <= 0:
            raise VirtualValidationError("invalid_number")
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
        entity[CONF_NATIVE_UNIT_OF_MEASUREMENT] = user_input.get(
            CONF_NATIVE_UNIT_OF_MEASUREMENT, ""
        )
        entity[CONF_MODE] = user_input[CONF_MODE]
    elif entity_type == ENTITY_TYPE_SELECT:
        entity[CONF_OPTIONS] = _parse_options(user_input[CONF_OPTIONS])
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
    elif entity_type == ENTITY_TYPE_TEXT:
        entity[CONF_MIN] = int(user_input[CONF_MIN])
        entity[CONF_MAX] = int(user_input[CONF_MAX])
        if entity[CONF_MIN] > entity[CONF_MAX]:
            raise VirtualValidationError("invalid_text")
        entity[CONF_INITIAL_VALUE] = coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
        entity[CONF_MODE] = user_input[CONF_MODE]
    elif entity_type in (ENTITY_TYPE_DATE, ENTITY_TYPE_TIME, ENTITY_TYPE_DATETIME):
        entity[CONF_INITIAL_VALUE] = _iso(
            coerce_entity_value(entity, user_input[CONF_INITIAL_VALUE])
        )

    validate_entity_definition(entity)
    return entity


def _parse_options(value: str | list[str]) -> list[str]:
    """Parse select options from comma-separated text or a list."""
    if isinstance(value, list):
        options = [str(option).strip() for option in value]
    else:
        options = [option.strip() for option in value.split(",")]
    options = [option for option in options if option]
    if not options:
        raise VirtualValidationError("invalid_options")
    return options


def _options_default(defaults: dict[str, Any]) -> str:
    """Return select options default for forms."""
    options = defaults.get(CONF_OPTIONS, "")
    if isinstance(options, list):
        return ", ".join(options)
    return str(options)


def _iso(value: date | datetime | time) -> str:
    """Return ISO text for date-like values."""
    return value.isoformat()
