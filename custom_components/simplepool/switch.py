"""Modes : Programmation, Hors gel, Boost."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import MODE_BOOST, MODE_HORS_GEL, MODE_PROGRAMMATION
from .entity import PiscineEntity

MODES = {
    MODE_PROGRAMMATION: ("Programmation", "mdi:calendar-clock"),
    MODE_HORS_GEL: ("Hors gel", "mdi:snowflake-thermometer"),
    MODE_BOOST: ("Boost", "mdi:rocket-launch"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    ctrl = entry.runtime_data
    async_add_entities(
        PiscineModeSwitch(ctrl, key, name, icon) for key, (name, icon) in MODES.items()
    )


class PiscineModeSwitch(PiscineEntity, SwitchEntity, RestoreEntity):
    """Interrupteur de mode."""

    _piscine_domain = "switch"

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.ctrl, self._key))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._key == MODE_BOOST and self.ctrl.boost_end is not None:
            return {"fin": self.ctrl.boost_end.isoformat()}
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.ctrl.restore_mode(
                self._key, last.state == STATE_ON, last.attributes.get("fin")
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.ctrl.async_set_mode(self._key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.ctrl.async_set_mode(self._key, False)
