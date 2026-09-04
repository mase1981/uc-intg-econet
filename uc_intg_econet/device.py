"""Rheem EcoNet device - one cloud account driven by the pyeconet client + MQTT.

Uses ExternalClientDevice because pyeconet manages its own connection and MQTT
push internally. Authentication happens in the connect path (create_client), so
the framework watchdog's reconnect re-logs-in and re-subscribes automatically -
recovery == reconnect. Concurrent connect() calls are serialised (rule 9) so the
framework's double-connect can never orphan a second MQTT client.
"""

import asyncio
import logging
from typing import Any

from pyeconet.equipment.thermostat import (
    ThermostatFanMode,
    ThermostatOperationMode,
)
from pyeconet.equipment.water_heater import WaterHeaterOperationMode
from ucapi_framework import ExternalClientDevice

from uc_intg_econet.client import EconetClient
from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import STATE_ON, STATE_UNAVAILABLE

_LOG = logging.getLogger(__name__)


class EconetDevice(ExternalClientDevice):
    """One Rheem EcoNet account."""

    def __init__(self, device_config: EconetConfig, **kwargs: Any) -> None:
        super().__init__(device_config, **kwargs)
        self._device_config = device_config
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

    # -- ExternalClientDevice interface --------------------------------
    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            await super().disconnect()

    async def create_client(self) -> EconetClient:
        await self.disconnect_client()  # defensive - watchdog bypasses connect()
        client = EconetClient(self._device_config.email, self._device_config.password)
        await client.connect()
        return client

    async def connect_client(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._client.subscribe(self._on_push)
        self._state = STATE_ON

    async def disconnect_client(self) -> None:
        if self._client is not None:
            self._client.close()
        self._state = STATE_UNAVAILABLE

    def check_client_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    def _on_push(self) -> None:
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self.push_update)

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
