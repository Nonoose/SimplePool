"""Intégration SimplePool."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import CARD_FILENAME, CARD_URL, DOMAIN, VERSION
from .controller import PoolController

PLATFORMS = [
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type PiscineConfigEntry = ConfigEntry[PoolController]

import logging

_LOGGER = logging.getLogger(__name__)


async def _ensure_lovelace_resource(hass: HomeAssistant) -> None:
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    if not isinstance(resources, ResourceStorageCollection):
        _LOGGER.warning(
            "Lovelace en mode YAML ou indisponible : ajoute manuellement la ressource %s (module)",
            CARD_URL,
        )
        return

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    url = f"{CARD_URL}?v={VERSION}"
    for item in resources.async_items():
        if item["url"].split("?")[0] == CARD_URL:
            if item["url"] != url:
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url}
                )
            return

    await resources.async_create_item({"res_type": "module", "url": url})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    path = Path(__file__).parent / "www" / CARD_FILENAME
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(path), True)]
    )
    await _ensure_lovelace_resource(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PiscineConfigEntry) -> bool:
    ctrl = PoolController(hass, entry)
    entry.runtime_data = ctrl
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Les entités ont restauré leur état : on peut piloter la pompe.
    ctrl.async_start()
    entry.async_on_unload(ctrl.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PiscineConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: PiscineConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
