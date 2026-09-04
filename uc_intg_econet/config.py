"""Configuration dataclass and manager for the Rheem EcoNet integration.

One config entry represents a single Rheem EcoNet account. The equipment
discovered during setup is cached so entities can be built without a live cloud
connection (reboot-safe); live values flow in through the device on connect.
"""

from dataclasses import dataclass, field

from ucapi_framework import BaseConfigManager


@dataclass
class EconetConfig:
    """Configuration for a single Rheem EcoNet account."""

    identifier: str = ""
    name: str = ""
    email: str = ""
    password: str = ""
    equipment: list[dict] = field(default_factory=list)


class EconetConfigManager(BaseConfigManager[EconetConfig]):
    """Config manager bound to :class:`EconetConfig`."""
