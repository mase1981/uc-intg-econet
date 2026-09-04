"""Integration driver for Rheem EcoNet accounts."""

from ucapi_framework import BaseIntegrationDriver

from uc_intg_econet.climate import create_climates
from uc_intg_econet.config import EconetConfig
from uc_intg_econet.device import EconetDevice
from uc_intg_econet.select import create_selects
from uc_intg_econet.sensor import create_sensors
from uc_intg_econet.switch import create_switches


class EconetDriver(BaseIntegrationDriver[EconetDevice, EconetConfig]):
    """Builds the entity set for each Rheem EcoNet account."""

    def __init__(self) -> None:
        super().__init__(
            device_class=EconetDevice,
            entity_classes=[
                create_climates,
                create_selects,
                create_switches,
                create_sensors,
            ],
            driver_id="uc_intg_econet",
        )
