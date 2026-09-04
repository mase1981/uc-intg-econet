"""Setup flow: log in to a Rheem EcoNet account and cache its equipment."""

import logging
import re
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_econet.client import EconetClient
from uc_intg_econet.config import EconetConfig

_LOG = logging.getLogger(__name__)


class EconetSetupFlow(BaseSetupFlow[EconetConfig]):
    """Collect EcoNet account credentials, validate, and store discovered equipment."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "Rheem EcoNet Account"},
            [
                {
                    "id": "info",
                    "label": {"en": "Rheem EcoNet Account"},
                    "field": {"label": {"value": {"en": (
                        "Enter the email and password for your Rheem EcoNet account (the same "
                        "credentials you use in the EcoNet app). All water heaters and thermostats "
                        "on the account will be added."
                    )}}},
                },
                {"id": "email", "label": {"en": "Email"}, "field": {"text": {"value": ""}}},
                {"id": "password", "label": {"en": "Password"}, "field": {"password": {"value": ""}}},
            ],
        )

    async def query_device(self, input_values: dict[str, Any]) -> EconetConfig:
        email = input_values.get("email", "").strip()
        password = input_values.get("password", "").strip()
        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")

        client = EconetClient(email, password)
        try:
            await client.connect()
            equipment = client.all_metadata()
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise ValueError(
                f"Could not sign in to Rheem EcoNet. Check the email and password. ({err})"
            ) from err
        finally:
            client.close()

        if not equipment:
            raise ValueError("No water heaters or thermostats were found on this EcoNet account.")

        identifier = f"econet_{re.sub(r'[^A-Za-z0-9]', '_', email.lower())}"
        return EconetConfig(
            identifier=identifier,
            name="Rheem EcoNet",
            email=email,
            password=password,
            equipment=equipment,
        )
