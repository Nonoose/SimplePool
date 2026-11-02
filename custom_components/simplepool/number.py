"""Réglages du bassin et de la pompe."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import NUMBERS
from .entity import PiscineEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    ctrl = entry.runtime_data
    async_add_entities(PiscineNumber(ctrl, key, *spec) for key, spec in NUMBERS.items())


class PiscineNumber(PiscineEntity, NumberEntity, RestoreEntity):
    """Valeur numérique réglable."""

    _piscine_domain = "number"
    _attr_mode = NumberMode.BOX

    def __init__(self, ctrl, key, name, icon, vmin, vmax, step, unit, default) -> None:
        super().__init__(ctrl, key, name, icon)
        self._attr_native_min_value = vmin
        self._attr_native_max_value = vmax
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float:
        return self.ctrl.numbers[self._key]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is None:
            return
        try:
            value = float(last.state)
        except ValueError:
            return
        if self._attr_native_min_value <= value <= self._attr_native_max_value:
            self.ctrl.numbers[self._key] = value

    async def async_set_native_value(self, value: float) -> None:
        await self.ctrl.async_set_number(self._key, value)
