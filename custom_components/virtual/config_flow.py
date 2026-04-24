"""Config flow for the Virtual integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_CONNECTION_VALUE,
    CONF_CUSTOM_CONNECTION_TYPE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_KEY,
    CONF_SWITCHES,
    CONNECTION_TYPE_CUSTOM,
    CONNECTION_TYPE_MAC,
    CONNECTION_TYPE_NONE,
    DOMAIN,
)
from .models import (
    VirtualValidationError,
    generate_device_id,
    generate_switch_key,
    normalize_connection,
    validate_unique_switch_key,
)

CONF_ADD_SWITCH = "add_switch"

CONNECTION_TYPES = [CONNECTION_TYPE_NONE, CONNECTION_TYPE_MAC, CONNECTION_TYPE_CUSTOM]
ENTITY_CATEGORIES = ["", "config", "diagnostic"]
SWITCH_DEVICE_CLASSES = ["", *[device_class.value for device_class in SwitchDeviceClass]]


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


def _switch_schema(defaults: dict[str, Any] | None = None, include_key: bool = True) -> vol.Schema:
    """Return schema for switch details."""
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
            vol.Optional(
                CONF_DEVICE_CLASS,
                default=defaults.get(CONF_DEVICE_CLASS, ""),
            ): vol.In(SWITCH_DEVICE_CLASSES),
        }
    )
    return vol.Schema(fields)


class VirtualConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device: dict[str, Any] = {}
        self._switches: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
                    return await self.async_step_switch_menu()

        return self.async_show_form(
            step_id="user",
            data_schema=_device_schema(),
            errors=errors,
        )

    async def async_step_switch_menu(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Ask whether to add another switch."""
        if user_input is not None:
            if user_input[CONF_ADD_SWITCH]:
                return await self.async_step_add_switch()
            return self.async_create_entry(
                title=self._device[CONF_NAME],
                data={**self._device, CONF_SWITCHES: self._switches},
            )

        return self.async_show_form(
            step_id="switch_menu",
            data_schema=vol.Schema({vol.Required(CONF_ADD_SWITCH, default=False): bool}),
        )

    async def async_step_add_switch(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Add a switch to the virtual device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            key = (user_input.get(CONF_KEY) or "").strip()
            if not key:
                key = generate_switch_key(
                    user_input[CONF_NAME],
                    {switch[CONF_KEY] for switch in self._switches},
                )
            try:
                validate_unique_switch_key(key, self._switches)
            except VirtualValidationError as err:
                errors["base"] = str(err)
            else:
                self._switches.append(
                    {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_KEY: key,
                        CONF_ICON: user_input.get(CONF_ICON, ""),
                        CONF_ENTITY_CATEGORY: user_input.get(CONF_ENTITY_CATEGORY, ""),
                        CONF_DEVICE_CLASS: user_input.get(CONF_DEVICE_CLASS, ""),
                    }
                )
                return await self.async_step_switch_menu()

        return self.async_show_form(
            step_id="add_switch",
            data_schema=_switch_schema(),
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
            entry.data.get(CONF_DEVICE_ID) == device_id
            for entry in self._async_current_entries()
        )


class VirtualOptionsFlow(OptionsFlow):
    """Handle options for Virtual."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show a placeholder options flow until options tests drive behavior."""
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
