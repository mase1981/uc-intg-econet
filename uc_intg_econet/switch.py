"""EcoNet water-heater away-mode switch."""

import logging
from typing import Any

from ucapi import StatusCodes, switch
from ucapi_framework import SwitchEntity

from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import KIND_WATER_HEATER, STATE_ON
from uc_intg_econet.device import EconetDevice

_LOG = logging.getLogger(__name__)


class AwaySwitch(SwitchEntity):
    """Toggles the water heater's away mode."""

    def __init__(self, device_config: EconetConfig, device: EconetDevice, meta: dict) -> None:
        self._device = device
        self._serial = meta["serial"]
        super().__init__(
            f"switch.{device_config.identifier}.{self._serial}.away",
            f"{meta.get('name', 'Water Heater')} Away",
            [switch.Features.ON_OFF, switch.Features.TOGGLE],
            {switch.Attributes.STATE: switch.States.UNKNOWN},
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        equipment = self._device.get_equipment(self._serial)
        if self._device.state != STATE_ON or equipment is None:
            self.update({switch.Attributes.STATE: switch.States.UNAVAILABLE})
            return
        away = bool(getattr(equipment, "away", False))
        self.update({switch.Attributes.STATE: switch.States.ON if away else switch.States.OFF})

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        try:
            if cmd_id == switch.Commands.ON:
                ok = self._device.wh_set_away(self._serial, True)
            elif cmd_id == switch.Commands.OFF:
                ok = self._device.wh_set_away(self._serial, False)
            elif cmd_id == switch.Commands.TOGGLE:
                equipment = self._device.get_equipment(self._serial)
                current = bool(getattr(equipment, "away", False)) if equipment else False
                ok = self._device.wh_set_away(self._serial, not current)
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Away switch error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR


def create_switches(device_config: EconetConfig, device: EconetDevice) -> list[SwitchEntity]:
    return [
        AwaySwitch(device_config, device, meta)
        for meta in device_config.equipment
        if meta.get("kind") == KIND_WATER_HEATER and meta.get("supports_away")
    ]
