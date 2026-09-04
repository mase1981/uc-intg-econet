"""Rheem EcoNet device - one cloud account exposing all its equipment."""

import asyncio
import logging
from typing import Any

from pyeconet.equipment.thermostat import (
    ThermostatFanMode,
    ThermostatOperationMode,
)
from pyeconet.equipment.water_heater import WaterHeaterOperationMode
from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_econet.client import EconetClient
from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import POLL_INTERVAL, STATE_ON, STATE_UNAVAILABLE

_LOG = logging.getLogger(__name__)


class EconetDevice(PollingDevice):
    """One Rheem EcoNet account."""

    def __init__(self, device_config: EconetConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: EconetClient | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._state: str = STATE_UNAVAILABLE
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return "econet-cloud"

    @property
    def log_id(self) -> str:
        return f"{self.name} (EcoNet)"

    @property
    def state(self) -> str:
        return self._state

    def get_equipment(self, serial: str) -> Any:
        if self._client is None:
            return None
        return self._client.get(serial)

    async def establish_connection(self) -> EconetClient:
        async with self._connect_lock:
            self._loop = asyncio.get_running_loop()
            if self._client is None:
                client = EconetClient(self._device_config.email, self._device_config.password)
                await client.connect()
                client.subscribe(self._on_push)
                self._client = client
            self._state = STATE_ON
            return self._client

    def _on_push(self) -> None:
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self.push_update)

    async def poll_device(self) -> None:
        if self._client is None:
            return
        try:
            async with self._connect_lock:
                await self._client.refresh()
            self.push_update()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != STATE_UNAVAILABLE:
                self._state = STATE_UNAVAILABLE
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                self._client.close()
                self._client = None
        self._state = STATE_UNAVAILABLE
        await super().disconnect()

    # -- water-heater commands ----------------------------------------
    def wh_set_setpoint(self, serial: str, temperature: int) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_set_point(int(temperature))
        self.push_update()
        return True

    def wh_set_mode(self, serial: str, mode_name: str) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_mode(WaterHeaterOperationMode[mode_name])
        self.push_update()
        return True

    def wh_set_away(self, serial: str, away: bool) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_away_mode(away)
        self.push_update()
        return True

    # -- thermostat commands ------------------------------------------
    def thermo_set_mode(self, serial: str, mode_name: str) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_mode(ThermostatOperationMode[mode_name])
        self.push_update()
        return True

    def thermo_set_setpoint(self, serial: str, temperature: int) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_set_point(int(temperature), None, None)
        self.push_update()
        return True

    def thermo_set_setpoint_range(self, serial: str, low: int, high: int) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_set_point(None, int(high), int(low))
        self.push_update()
        return True

    def thermo_set_fan_mode(self, serial: str, mode_name: str) -> bool:
        equipment = self.get_equipment(serial)
        if equipment is None:
            return False
        equipment.set_fan_mode(ThermostatFanMode[mode_name])
        self.push_update()
        return True
