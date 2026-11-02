"""Assistant de configuration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_AIR, CONF_PUMP, CONF_WATER, DOMAIN


def _schema(current: dict[str, Any]) -> vol.Schema:
    temp = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
    )
    return vol.Schema(
        {
            vol.Required(
                CONF_PUMP, description={"suggested_value": current.get(CONF_PUMP)}
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch", "input_boolean", "light"])
            ),
            vol.Optional(
                CONF_WATER, description={"suggested_value": current.get(CONF_WATER)}
            ): temp,
            vol.Optional(
                CONF_AIR, description={"suggested_value": current.get(CONF_AIR)}
            ): temp,
        }
    )


class PiscineConfigFlow(ConfigFlow, domain=DOMAIN):
    """Création de l'intégration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="SimplePool", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PiscineOptionsFlow()


class PiscineOptionsFlow(OptionsFlow):
    """Modification des entités utilisées."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options or self.config_entry.data
        return self.async_show_form(step_id="init", data_schema=_schema(dict(current)))
