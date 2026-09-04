"""EcoNet sensors - tank/hot-water/health, humidity, running state, wifi."""

import logging
from typing import Any, Callable

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import KIND_THERMOSTAT, KIND_WATER_HEATER, STATE_ON
from uc_intg_econet.device import EconetDevice

_LOG = logging.getLogger(__name__)


class EconetSensor(SensorEntity):
    """A single equipment metric backed by a getter reading the live equipment."""

    def __init__(
        self,
        device_config: EconetConfig,
        device: EconetDevice,
        serial: str,
        sub_id: str,
        label: str,
        getter: Callable[[Any], Any],
        unit: str,
        numeric: bool,
    ) -> None:
        self._device = device
        self._serial = serial
        self._getter = getter
        self._numeric = numeric
        super().__init__(
            f"sensor.{device_config.identifier}.{serial}.{sub_id}",
            label,
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: -1 if numeric else ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: unit},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        equipment = self._device.get_equipment(self._serial)
        if self._device.state != STATE_ON or equipment is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        value = self._getter(equipment)
        if value is None:
            value = 0 if self._numeric else "Unknown"
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: value})


def create_sensors(device_config: EconetConfig, device: EconetDevice) -> list[SensorEntity]:
    entities: list[SensorEntity] = []
    for meta in device_config.equipment:
        serial = meta["serial"]
        name = meta.get("name", "EcoNet")
        kind = meta.get("kind")
        if kind == KIND_WATER_HEATER:
            if meta.get("has_hot_water_avail"):
                entities.append(EconetSensor(
                    device_config, device, serial, "hot_water", f"{name} Hot Water",
                    lambda e: getattr(e, "tank_hot_water_availability", None), "%", True))
            if meta.get("has_tank_health"):
                entities.append(EconetSensor(
                    device_config, device, serial, "tank_health", f"{name} Tank Health",
                    lambda e: getattr(e, "tank_health", None), "%", True))
            if meta.get("has_compressor_health"):
                entities.append(EconetSensor(
                    device_config, device, serial, "compressor_health", f"{name} Compressor Health",
                    lambda e: getattr(e, "compressor_health", None), "%", True))
            entities.append(EconetSensor(
                device_config, device, serial, "running", f"{name} Status",
                lambda e: getattr(e, "running_state", None) or "Idle", "", False))
        elif kind == KIND_THERMOSTAT:
            if meta.get("has_humidity"):
                entities.append(EconetSensor(
                    device_config, device, serial, "humidity", f"{name} Humidity",
                    lambda e: getattr(e, "humidity", None), "%", True))
            entities.append(EconetSensor(
                device_config, device, serial, "running", f"{name} Status",
                lambda e: getattr(e, "running_state", None) or "Idle", "", False))
        entities.append(EconetSensor(
            device_config, device, serial, "wifi", f"{name} WiFi Signal",
            lambda e: getattr(e, "wifi_signal", None), "dB", True))
    return entities
