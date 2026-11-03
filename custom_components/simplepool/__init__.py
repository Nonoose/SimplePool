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

async def _ensure_lovelace_resource(hass):
    resources = hass.data["lovelace"]["resources"]
    url = f"{CARD_URL}?v={VERSION}"
    existing = await resources.async_items()
    if not any(r["url"] == url for r in existing):
        await resources.async_create_item(
            {
                "res_type": "module",
                "url": url,
            }
        )

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Sert la carte Lovelace et la charge automatiquement dans l'interface."""
    path = Path(__file__).parent / "www" / CARD_FILENAME
    await _ensure_lovelace_resource(hass)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(path), True)]
    )
    
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
