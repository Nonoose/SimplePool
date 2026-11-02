"""Plages de filtration (début et durée, par pas de 30 min)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DUREES, HEURES, PLAGE_1_DEBUT, PLAGE_1_DUREE, PLAGE_2_DEBUT, PLAGE_2_DUREE
from .entity import PiscineEntity

PLAGES = {
    PLAGE_1_DEBUT: ("Plage 1 début", "mdi:clock-start", HEURES),
    PLAGE_1_DUREE: ("Plage 1 durée", "mdi:timer-outline", DUREES),
    PLAGE_2_DEBUT: ("Plage 2 début", "mdi:clock-start", HEURES),
    PLAGE_2_DUREE: ("Plage 2 durée", "mdi:timer-outline", DUREES),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    ctrl = entry.runtime_data
    async_add_entities(
        PiscinePlageSelect(ctrl, key, name, icon, options)
        for key, (name, icon, options) in PLAGES.items()
    )


class PiscinePlageSelect(PiscineEntity, SelectEntity, RestoreEntity):
    """Liste déroulante d'une plage."""

    _piscine_domain = "select"

    def __init__(self, ctrl, key, name, icon, options) -> None:
        super().__init__(ctrl, key, name, icon)
        self._attr_options = list(options)

    @property
    def current_option(self) -> str | None:
        return self.ctrl.plages[self._key]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in self._attr_options:
            self.ctrl.plages[self._key] = last.state

    async def async_select_option(self, option: str) -> None:
        await self.ctrl.async_set_plage(self._key, option)
