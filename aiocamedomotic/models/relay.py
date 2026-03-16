# Copyright 2024 - GitHub user: fredericks1982

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
CAME Domotic relay entity models and control functionality.

This module implements the classes for working with generic relays in a CAME
Domotic system. Generic relays are simple on/off switches that can be
controlled remotely. They provide binary state control without brightness,
color, or position capabilities.

.. note::
    The relay API commands (``relays_list_req``, ``relay_activation_req``)
    are documented in the CAME API specification but have not been verified
    against a real server. Behaviour may differ across firmware versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..auth import Auth
from ..const import _CommandName
from ..utils import (
    LOGGER,
    EntityValidator,
)
from .base import CameEntity


class RelayStatus(Enum):
    """Status of a relay.

    Allowed values are:
        - OFF (0)
        - ON (1)
    """

    OFF = 0
    ON = 1
    UNKNOWN = -1


@dataclass
class Relay(CameEntity):
    """
    Relay entity in the CameDomotic API.

    Represents a generic relay (simple on/off switch) in the CAME Domotic
    system. Provides properties to read relay attributes and a method to
    control relay state.

    Raises:
        ValueError: If ``name`` or ``act_id`` keys are missing from the
            input data or the auth argument is not an instance of the
            expected ``Auth`` class.
    """

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "act_id"],
            typed_keys={"act_id": int},
        )
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def act_id(self) -> int:
        """ID of the relay."""
        return self.raw_data["act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index of the relay."""
        return self.raw_data["floor_ind"]

    @property
    def name(self) -> str:
        """Name of the relay."""
        return self.raw_data["name"]

    @property
    def room_ind(self) -> int:
        """Room index of the relay."""
        return self.raw_data["room_ind"]

    @property
    def status(self) -> RelayStatus:
        """Status of the relay. Allowed values are OFF (0) and ON (1)."""
        try:
            return RelayStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown relay status '%s' encountered for relay '%s' (ID: %s). "
                "Returning RelayStatus.UNKNOWN. Please report this "
                "to the library developers.",
                self.raw_data.get("status"),
                self.name,
                self.act_id,
            )
            return RelayStatus.UNKNOWN

    async def async_set_status(self, status: RelayStatus) -> None:
        """Control the relay.

        Args:
            status (RelayStatus): Desired relay status (ON or OFF).

        Raises:
            ValueError: If ``status`` is ``RelayStatus.UNKNOWN``.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if status == RelayStatus.UNKNOWN:
            raise ValueError("Cannot set relay status to UNKNOWN")

        await self.auth.async_get_valid_client_id()
        LOGGER.debug(
            "User authenticated, sending 'relay_activation_req' command to the API."
        )

        payload = {
            "act_id": self.act_id,
            "cmd_name": _CommandName.RELAY_ACTIVATION.value,
            "wanted_status": status.value,
        }
        await self.auth.async_send_command(payload)

        # Update the status of the relay if everything went as expected
        self.raw_data["status"] = status.value

        LOGGER.info(
            "Relay '%s' (ID: %s) set to %s",
            self.name,
            self.act_id,
            status.name,
        )
