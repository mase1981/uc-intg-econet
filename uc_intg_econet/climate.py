"""EcoNet climate entities - water heater and thermostat."""

import logging
from typing import Any

from ucapi import StatusCodes, climate
from ucapi_framework import ClimateEntity

from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import (
    FAN_MODE_LABELS,
    KIND_THERMOSTAT,
    KIND_WATER_HEATER,
    STATE_ON,
    TEMPERATURE_UNIT,
)
from uc_intg_econet.device import EconetDevice

_LOG = logging.getLogger(__name__)


class WaterHeaterClimate(ClimateEntity):
    """A Rheem water heater as a heat-only climate entity with a target setpoint."""

    def __init__(self, device_config: EconetConfig, device: EconetDevice, meta: dict) -> None:
        self._device = device
        self._serial = meta["serial"]
        self._modes = list(meta.get("modes", []))
        options = {
            climate.Options.TEMPERATURE_UNIT: TEMPERATURE_UNIT,
            climate.Options.TARGET_TEMPERATURE_STEP: 1,
            climate.Options.MIN_TEMPERATURE: meta.get("min_setpoint", 0),
            climate.Options.MAX_TEMPERATURE: meta.get("max_setpoint", 0),
        }
        super().__init__(
            f"climate.{device_config.identifier}.{self._serial}",
            meta.get("name", "Water Heater"),
            [
                climate.Features.ON_OFF,
                climate.Features.HEAT,
                climate.Features.CURRENT_TEMPERATURE,
                climate.Features.TARGET_TEMPERATURE,
            ],
            {climate.Attributes.STATE: climate.States.UNKNOWN},
            options=options,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    def _first_heating_mode(self, equipment: Any) -> str | None:
        current = getattr(getattr(equipment, "mode", None), "name", None)
        if current and current != "OFF":
            return current
        return next((m for m in self._modes if m != "OFF"), None)

    async def sync_state(self) -> None:
        equipment = self._device.get_equipment(self._serial)
        if self._device.state != STATE_ON or equipment is None:
            self.update({climate.Attributes.STATE: climate.States.UNAVAILABLE})
            return
        enabled = getattr(equipment, "enabled", None)
        state = climate.States.OFF if enabled is False else climate.States.HEAT
        set_point = getattr(equipment, "set_point", 0) or 0
        self.update(
            {
                climate.Attributes.STATE: state,
                climate.Attributes.TARGET_TEMPERATURE: set_point,
                climate.Attributes.CURRENT_TEMPERATURE: set_point,
            }
        )

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        params = params or {}
        try:
            if cmd_id == climate.Commands.OFF or (
                cmd_id == climate.Commands.HVAC_MODE and str(params.get("hvac_mode", "")).upper() == "OFF"
            ):
                return self._result(self._device.wh_set_mode(self._serial, "OFF"))
            if cmd_id == climate.Commands.ON or (
                cmd_id == climate.Commands.HVAC_MODE and str(params.get("hvac_mode", "")).upper() == "HEAT"
            ):
                equipment = self._device.get_equipment(self._serial)
                mode = self._first_heating_mode(equipment) if equipment else None
                if mode is None:
                    return StatusCodes.NOT_IMPLEMENTED
                return self._result(self._device.wh_set_mode(self._serial, mode))
            if cmd_id == climate.Commands.TARGET_TEMPERATURE:
                return self._result(self._device.wh_set_setpoint(self._serial, int(params.get("temperature", 0))))
            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Water heater command error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

    @staticmethod
    def _result(ok: bool) -> StatusCodes:
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR


_THERMO_STATE = {
    "OFF": climate.States.OFF,
    "HEATING": climate.States.HEAT,
    "COOLING": climate.States.COOL,
    "AUTO": climate.States.AUTO,
    "FAN_ONLY": climate.States.FAN,
    "EMERGENCY_HEAT": climate.States.HEAT,
}

_HVAC_TO_MODE = {
    "OFF": "OFF",
    "HEAT": "HEATING",
    "COOL": "COOLING",
    "AUTO": "AUTO",
    "FAN": "FAN_ONLY",
}


class ThermostatClimate(ClimateEntity):
    """A Rheem EcoNet thermostat as a full HVAC climate entity."""

    def __init__(self, device_config: EconetConfig, device: EconetDevice, meta: dict) -> None:
        self._device = device
        self._serial = meta["serial"]
        self._hvac_modes = list(meta.get("hvac_modes", []))
        self._fan_modes = list(meta.get("fan_modes", []))
        self._supports_fan = bool(meta.get("supports_fan_mode")) and bool(self._fan_modes)

        features = [
            climate.Features.ON_OFF,
            climate.Features.CURRENT_TEMPERATURE,
            climate.Features.TARGET_TEMPERATURE,
        ]
        if "HEATING" in self._hvac_modes or "EMERGENCY_HEAT" in self._hvac_modes:
            features.append(climate.Features.HEAT)
        if "COOLING" in self._hvac_modes:
            features.append(climate.Features.COOL)
        if "AUTO" in self._hvac_modes:
            features.append(climate.Features.TARGET_TEMPERATURE_RANGE)
        if self._supports_fan:
            features.append(climate.Features.FAN)

        options = {
            climate.Options.TEMPERATURE_UNIT: TEMPERATURE_UNIT,
            climate.Options.TARGET_TEMPERATURE_STEP: 1,
            climate.Options.MIN_TEMPERATURE: meta.get("min_setpoint", 0),
            climate.Options.MAX_TEMPERATURE: meta.get("max_setpoint", 0),
        }
        if self._supports_fan:
            options[climate.Options.FAN_MODES] = [FAN_MODE_LABELS.get(m, m.title()) for m in self._fan_modes]

        super().__init__(
            f"climate.{device_config.identifier}.{self._serial}",
            meta.get("name", "Thermostat"),
            features,
            {climate.Attributes.STATE: climate.States.UNKNOWN},
            options=options,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        equipment = self._device.get_equipment(self._serial)
        if self._device.state != STATE_ON or equipment is None:
            self.update({climate.Attributes.STATE: climate.States.UNAVAILABLE})
            return
        mode_name = getattr(getattr(equipment, "mode", None), "name", "OFF")
        attrs: dict[str, Any] = {climate.Attributes.STATE: _THERMO_STATE.get(mode_name, climate.States.UNKNOWN)}
        attrs[climate.Attributes.CURRENT_TEMPERATURE] = getattr(equipment, "set_point", 0) or 0
        cool = getattr(equipment, "cool_set_point", None)
        heat = getattr(equipment, "heat_set_point", None)
        if mode_name == "COOLING" and cool is not None:
            attrs[climate.Attributes.TARGET_TEMPERATURE] = cool
        elif mode_name in ("HEATING", "EMERGENCY_HEAT") and heat is not None:
            attrs[climate.Attributes.TARGET_TEMPERATURE] = heat
        elif mode_name == "AUTO":
            if cool is not None:
                attrs[climate.Attributes.TARGET_TEMPERATURE_HIGH] = cool
            if heat is not None:
                attrs[climate.Attributes.TARGET_TEMPERATURE_LOW] = heat
        if self._supports_fan:
            fan = getattr(getattr(equipment, "fan_mode", None), "name", None)
            if fan is not None:
                attrs[climate.Attributes.FAN_MODE] = FAN_MODE_LABELS.get(fan, fan.title())
        self.update(attrs)

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        params = params or {}
        try:
            if cmd_id == climate.Commands.OFF:
                return self._result(self._device.thermo_set_mode(self._serial, "OFF"))
            if cmd_id == climate.Commands.ON:
                mode = next((m for m in self._hvac_modes if m != "OFF"), None)
                if mode is None:
                    return StatusCodes.NOT_IMPLEMENTED
                return self._result(self._device.thermo_set_mode(self._serial, mode))
            if cmd_id == climate.Commands.HVAC_MODE:
                mode = _HVAC_TO_MODE.get(str(params.get("hvac_mode", "")).upper())
                if mode is None:
                    return StatusCodes.NOT_IMPLEMENTED
                return self._result(self._device.thermo_set_mode(self._serial, mode))
            if cmd_id == climate.Commands.TARGET_TEMPERATURE:
                return self._result(self._device.thermo_set_setpoint(self._serial, int(params.get("temperature", 0))))
            if cmd_id == climate.Commands.TARGET_TEMPERATURE_RANGE:
                low = int(params.get("temperature_low", 0))
                high = int(params.get("temperature_high", 0))
                return self._result(self._device.thermo_set_setpoint_range(self._serial, low, high))
            if cmd_id == climate.Commands.FAN_MODE:
                label = str(params.get("fan_mode") or params.get("enum") or "")
                name = next((m for m in self._fan_modes if FAN_MODE_LABELS.get(m, m.title()) == label), None)
                if name is None:
                    return StatusCodes.BAD_REQUEST
                return self._result(self._device.thermo_set_fan_mode(self._serial, name))
            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Thermostat command error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

    @staticmethod
    def _result(ok: bool) -> StatusCodes:
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR


def create_climates(device_config: EconetConfig, device: EconetDevice) -> list[ClimateEntity]:
    entities: list[ClimateEntity] = []
    for meta in device_config.equipment:
        if meta.get("kind") == KIND_WATER_HEATER:
            entities.append(WaterHeaterClimate(device_config, device, meta))
        elif meta.get("kind") == KIND_THERMOSTAT:
            entities.append(ThermostatClimate(device_config, device, meta))
    return entities
