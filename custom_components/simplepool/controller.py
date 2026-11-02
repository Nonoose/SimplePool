"""Logique de pilotage de la filtration (remplace le package YAML)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AIR,
    CONF_PUMP,
    CONF_WATER,
    DEFAULT_PLAGES,
    MODE_BOOST,
    MODE_HORS_GEL,
    MODE_PROGRAMMATION,
    NUM_BOOST_DUREE,
    NUM_DEBIT,
    NUM_SEUIL_GEL,
    NUM_VOLUME,
    NUMBERS,
    PLAGE_1_DEBUT,
    PLAGE_1_DUREE,
    PLAGE_2_DEBUT,
    PLAGE_2_DUREE,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


def parse_hhmm(value: str | None) -> float:
    """Convertit « 08h30 » en 8.5."""
    try:
        heures, minutes = str(value).split("h")
        return int(heures) + int(minutes) / 60
    except (ValueError, TypeError):
        return 0.0


def in_slot(x: float, start: float, duration: float) -> bool:
    """Vrai si l'heure x (0-24) est dans la plage (gère le passage de minuit)."""
    return duration > 0 and ((x - start) % 24) < duration


class PoolController:
    """Etat et logique de la filtration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        conf = entry.options or entry.data
        self.hass = hass
        self.entry = entry
        self.pump: str = conf[CONF_PUMP]
        self.water: str | None = conf.get(CONF_WATER) or None
        self.air: str | None = conf.get(CONF_AIR) or None
        self.signal = f"{SIGNAL_UPDATE}_{entry.entry_id}"

        self.programmation = False
        self.hors_gel = False
        self.boost = False
        self.boost_end: datetime | None = None
        self.gel = False
        self.plages: dict[str, str] = dict(DEFAULT_PLAGES)
        self.numbers: dict[str, float] = {k: float(v[6]) for k, v in NUMBERS.items()}

        self.desired: bool | None = None
        self._ready = False
        self._unsubs: list[Callable[[], None]] = []
        self._boost_unsub: Callable[[], None] | None = None

    # ------------------------------------------------------------------ lectures
    def _float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    @property
    def water_temp(self) -> float | None:
        return self._float(self.water)

    @property
    def air_temp(self) -> float | None:
        return self._float(self.air)

    def slots(self) -> list[tuple[float, float]]:
        return [
            (parse_hhmm(self.plages[PLAGE_1_DEBUT]), parse_hhmm(self.plages[PLAGE_1_DUREE])),
            (parse_hhmm(self.plages[PLAGE_2_DEBUT]), parse_hhmm(self.plages[PLAGE_2_DUREE])),
        ]

    def scheduled_now(self) -> bool:
        now = dt_util.now()
        hour = now.hour + now.minute / 60
        return any(in_slot(hour, s, d) for s, d in self.slots())

    @property
    def filtration_hours(self) -> float:
        """Heures programmées par jour (chevauchements comptés une fois)."""
        slots = self.slots()
        return sum(
            0.25 for q in range(96) if any(in_slot(q / 4 + 0.125, s, d) for s, d in slots)
        )

    @property
    def recommended_hours(self) -> float | None:
        """Règle « température de l'eau ÷ 2 », 4 h sous 12 °C, arrondie à 30 min."""
        temp = self.water_temp
        if temp is None:
            return None
        hours = 4.0 if temp < 12 else temp / 2
        return min(math.ceil(hours * 2) / 2, 24.0)

    @property
    def turnover(self) -> int | None:
        volume = self.numbers[NUM_VOLUME]
        if volume <= 0:
            return None
        return round(self.numbers[NUM_DEBIT] * self.filtration_hours / volume * 100)

    def compute_desired(self) -> bool:
        return self.boost or self.gel or (self.programmation and self.scheduled_now())

    def _update_gel(self) -> None:
        temp = self.air_temp
        seuil = self.numbers[NUM_SEUIL_GEL]
        if not self.hors_gel or temp is None:
            self.gel = False
        elif self.gel:
            self.gel = temp < seuil + 1  # hystérésis : arrêt à seuil + 1 °C
        else:
            self.gel = temp < seuil

    # --------------------------------------------------------------- pilotage
    async def async_evaluate(self, force: bool = False) -> None:
        if not self._ready:
            return
        self._update_gel()
        desired = self.compute_desired()
        if force or desired != self.desired:
            self.desired = desired if await self._async_apply(desired) else None
        self.async_notify()

    async def _async_apply(self, desired: bool) -> bool:
        state = self.hass.states.get(self.pump)
        if state is None or state.state not in (STATE_ON, STATE_OFF):
            _LOGGER.debug("Pompe %s indisponible, nouvel essai plus tard", self.pump)
            return False
        target = STATE_ON if desired else STATE_OFF
        if state.state != target:
            await self.hass.services.async_call(
                "homeassistant",
                "turn_on" if desired else "turn_off",
                {"entity_id": self.pump},
                blocking=False,
            )
        return True

    @callback
    def async_notify(self) -> None:
        async_dispatcher_send(self.hass, self.signal)

    # ---------------------------------------------------------------- setters
    async def async_set_mode(self, key: str, value: bool) -> None:
        if key == MODE_PROGRAMMATION:
            self.programmation = value
            self.hors_gel = False  # relance ou arrêt : le hors gel se coupe
            if not value:
                self._set_boost(False)  # arrêt : tout s'arrête
        elif key == MODE_HORS_GEL:
            self.hors_gel = value
            self.gel = False
            if value:
                self.programmation = False
                self._set_boost(False)
        elif key == MODE_BOOST:
            self._set_boost(value)
        await self.async_evaluate(force=True)

    async def async_set_plage(self, key: str, option: str) -> None:
        self.plages[key] = option
        await self.async_evaluate()

    async def async_set_number(self, key: str, value: float) -> None:
        self.numbers[key] = float(value)
        await self.async_evaluate()

    @callback
    def _set_boost(self, value: bool) -> None:
        if self._boost_unsub:
            self._boost_unsub()
            self._boost_unsub = None
        self.boost = value
        if value:
            self.boost_end = dt_util.utcnow() + timedelta(hours=self.numbers[NUM_BOOST_DUREE])
            self._schedule_boost_end()
        else:
            self.boost_end = None

    @callback
    def _schedule_boost_end(self) -> None:
        if self.boost_end is not None:
            self._boost_unsub = async_track_point_in_time(
                self.hass, self._async_boost_finished, self.boost_end
            )

    async def _async_boost_finished(self, _now: datetime) -> None:
        self._boost_unsub = None
        self.boost = False
        self.boost_end = None
        await self.async_evaluate(force=True)

    # ------------------------------------------------------------ restauration
    @callback
    def restore_mode(self, key: str, is_on: bool, end: str | None = None) -> None:
        if key == MODE_BOOST:
            end_dt = dt_util.parse_datetime(end) if end else None
            if is_on and end_dt and end_dt > dt_util.utcnow():
                self.boost = True
                self.boost_end = end_dt
                self._schedule_boost_end()
            else:
                self.boost = False
        elif key == MODE_PROGRAMMATION:
            self.programmation = is_on
        elif key == MODE_HORS_GEL:
            self.hors_gel = is_on and not self.programmation

    # ------------------------------------------------------------- cycle de vie
    @callback
    def async_start(self) -> None:
        self._ready = True
        tracked = [e for e in (self.pump, self.water, self.air) if e]
        self._unsubs.append(
            async_track_state_change_event(self.hass, tracked, self._async_on_state)
        )
        self._unsubs.append(
            async_track_time_change(self.hass, self._async_on_tick, second=0)
        )
        self.entry.async_create_background_task(
            self.hass, self.async_evaluate(force=True), "simplepool_start"
        )

    @callback
    def async_stop(self) -> None:
        self._ready = False
        while self._unsubs:
            self._unsubs.pop()()
        if self._boost_unsub:
            self._boost_unsub()
            self._boost_unsub = None

    async def _async_on_state(self, event: Event) -> None:
        if event.data["entity_id"] == self.pump and self.desired is not None:
            self.async_notify()
            return
        await self.async_evaluate()

    async def _async_on_tick(self, _now: datetime) -> None:
        await self.async_evaluate()
