"""Async client for the Rheem EcoNet cloud.

Thin wrapper around :mod:`pyeconet`. Handles login, equipment discovery, the
MQTT subscription (used for both realtime push and publishing control commands),
and extraction of equipment metadata for reboot-safe caching.
"""

import logging
from typing import Any, Callable

from pyeconet import EcoNetApiInterface
from pyeconet.equipment import EquipmentType

from uc_intg_econet.const import KIND_THERMOSTAT, KIND_WATER_HEATER

_LOG = logging.getLogger(__name__)


def _enum_names(values: Any) -> list[str]:
    names = []
    for v in values or []:
        name = getattr(v, "name", None)
        if name and name != "UNKNOWN":
            names.append(name)
    return names


def equipment_metadata(equipment: Any) -> dict:
    """Extract cacheable metadata from a pyeconet equipment object."""
    kind = KIND_WATER_HEATER if equipment.type == EquipmentType.WATER_HEATER else KIND_THERMOSTAT
    meta: dict[str, Any] = {
        "serial": equipment.serial_number,
        "name": equipment.device_name or equipment.serial_number,
        "kind": kind,
        "generic_type": getattr(equipment, "generic_type", "") or "",
    }
    try:
        limits = equipment.set_point_limits or (0, 0)
        meta["min_setpoint"] = int(limits[0])
        meta["max_setpoint"] = int(limits[1])
    except (TypeError, ValueError):
        meta["min_setpoint"], meta["max_setpoint"] = 0, 0

    if kind == KIND_WATER_HEATER:
        meta["modes"] = _enum_names(getattr(equipment, "modes", None))
        meta["supports_away"] = bool(getattr(equipment, "supports_away", False))
        meta["has_tank_health"] = getattr(equipment, "tank_health", None) is not None
        meta["has_hot_water_avail"] = getattr(equipment, "tank_hot_water_availability", None) is not None
        meta["has_compressor_health"] = getattr(equipment, "compressor_health", None) is not None
    else:
        meta["hvac_modes"] = _enum_names(getattr(equipment, "modes", None))
        meta["supports_fan_mode"] = bool(getattr(equipment, "supports_fan_mode", False))
        meta["fan_modes"] = _enum_names(getattr(equipment, "fan_modes", None))
        meta["has_humidity"] = getattr(equipment, "humidity", None) is not None
    return meta


class EconetClient:
    """Cloud client for one Rheem EcoNet account."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._api: EcoNetApiInterface | None = None
        self._equipment: dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        return self._api is not None

    async def connect(self) -> None:
        """Log in and discover equipment. Does not start the MQTT subscription."""
        self._api = await EcoNetApiInterface.login(self._email, self._password)
        result = await self._api.get_equipment_by_type(
            [EquipmentType.WATER_HEATER, EquipmentType.THERMOSTAT]
        )
        self._equipment = {}
        for items in result.values():
            for item in items:
                self._equipment[item.serial_number] = item

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Start the MQTT subscription and register the push callback on each device."""
        if self._api is None:
            return
        for equipment in self._equipment.values():
            equipment.set_update_callback(callback)
        self._api.subscribe()

    async def refresh(self) -> None:
        if self._api is not None:
            await self._api.refresh_equipment()

    def close(self) -> None:
        if self._api is not None:
            try:
                self._api.unsubscribe()
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("unsubscribe failed: %s", err)
        self._api = None
        self._equipment = {}

    def all_metadata(self) -> list[dict]:
        return [equipment_metadata(e) for e in self._equipment.values()]

    def get(self, serial: str) -> Any:
        return self._equipment.get(serial)
