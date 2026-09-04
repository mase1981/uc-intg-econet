"""EcoNet water-heater operation-mode selector."""

import logging
from typing import Any

from ucapi import StatusCodes, select
from ucapi_framework import SelectEntity

from uc_intg_econet.config import EconetConfig
from uc_intg_econet.const import KIND_WATER_HEATER, STATE_ON, WH_MODE_LABELS
from uc_intg_econet.device import EconetDevice

_LOG = logging.getLogger(__name__)


class ModeSelect(SelectEntity):
    """Selects the water-heater operation mode (Energy Saver, High Demand, etc.)."""

    def __init__(self, device_config: EconetConfig, device: EconetDevice, meta: dict) -> None:
        self._device = device
        self._serial = meta["serial"]
        self._modes = list(meta.get("modes", []))
        self._label_to_name = {WH_MODE_LABELS.get(m, m.title()): m for m in self._modes}
        super().__init__(
            f"select.{device_config.identifier}.{self._serial}.mode",
            f"{meta.get('name', 'Water Heater')} Mode",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        equipment = self._device.get_equipment(self._serial)
        if self._device.state != STATE_ON or equipment is None:
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return
        current_name = getattr(getattr(equipment, "mode", None), "name", "")
        current_label = WH_MODE_LABELS.get(current_name, current_name.title() if current_name else "")
        self.update(
            {
                select.Attributes.STATE: select.States.ON,
                select.Attributes.OPTIONS: [WH_MODE_LABELS.get(m, m.title()) for m in self._modes],
                select.Attributes.CURRENT_OPTION: current_label,
            }
        )

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        if cmd_id == select.Commands.SELECT_OPTION:
            option = params.get("option", "") if params else ""
            name = self._label_to_name.get(option)
            if name is None:
                return StatusCodes.BAD_REQUEST
            try:
                if self._device.wh_set_mode(self._serial, name):
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.error("[%s] Mode select error: %s", entity.id, err)
                return StatusCodes.SERVER_ERROR
        return StatusCodes.NOT_IMPLEMENTED


def create_selects(device_config: EconetConfig, device: EconetDevice) -> list[SelectEntity]:
    return [
        ModeSelect(device_config, device, meta)
        for meta in device_config.equipment
        if meta.get("kind") == KIND_WATER_HEATER and meta.get("modes")
    ]
