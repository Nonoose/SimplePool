"""Entité de base."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, VERSION
from .controller import PoolController


class PiscineEntity(Entity):
    """Entité liée au contrôleur de filtration."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _piscine_domain: str = ""

    def __init__(self, ctrl: PoolController, key: str, name: str, icon: str) -> None:
        self.ctrl = ctrl
        self._key = key
        self._attr_unique_id = f"{ctrl.entry.entry_id}_{key}"
        self._attr_name = f"Piscine : {name}"
        self._attr_icon = icon
        # Identifiant fixe, utilisé par la carte : <domaine>.piscine_<clé>
        self.entity_id = f"{self._piscine_domain}.piscine_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ctrl.entry.entry_id)},
            name="Piscine",
            manufacturer="SimplePool",
            model="Pilotage de la filtration",
            sw_version=VERSION,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.ctrl.signal, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
