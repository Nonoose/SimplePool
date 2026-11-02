"""Capteurs binaires : gel détecté, pompe planifiée."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
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
            GelSensor(ctrl, "gel_detecte", "Gel détecté", "mdi:snowflake-alert"),
            PlanifieeSensor(ctrl, "pompe_planifiee", "Pompe planifiée", "mdi:pump"),
        ]
    )


class GelSensor(PiscineEntity, BinarySensorEntity):
    """Vrai quand le hors gel fait tourner la pompe."""

    _piscine_domain = "binary_sensor"

    @property
    def is_on(self) -> bool:
        return self.ctrl.gel

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"temperature_air": self.ctrl.air_temp}


class PlanifieeSensor(PiscineEntity, BinarySensorEntity):
    """Etat voulu de la pompe. Ses attributs servent aussi à la carte."""

    _piscine_domain = "binary_sensor"

    @property
    def is_on(self) -> bool:
        return self.ctrl.compute_desired()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "pump_entity": self.ctrl.pump,
            "water_temp_entity": self.ctrl.water,
            "air_temp_entity": self.ctrl.air,
        }
