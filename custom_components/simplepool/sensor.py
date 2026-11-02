"""Capteurs calculés : durée conseillée et turnover."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PiscineEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    ctrl = entry.runtime_data
    async_add_entities(
        [
            DureeConseilleeSensor(ctrl, "duree_conseillee", "Durée conseillée", "mdi:timer-sand"),
            TurnoverSensor(ctrl, "turnover", "Turnover", "mdi:water-sync"),
        ]
    )


class DureeConseilleeSensor(PiscineEntity, SensorEntity):
    """Température de l'eau ÷ 2."""

    _piscine_domain = "sensor"
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        return self.ctrl.recommended_hours

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "temperature_eau": self.ctrl.water_temp,
            "filtration_programmee": self.ctrl.filtration_hours,
        }


class TurnoverSensor(PiscineEntity, SensorEntity):
    """Part du volume filtrée par jour."""

    _piscine_domain = "sensor"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        return self.ctrl.turnover
