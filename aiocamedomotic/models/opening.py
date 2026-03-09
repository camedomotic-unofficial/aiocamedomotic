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
CAME Domotic opening entity models and control functionality.

This module implements the classes for working with openings in a CAME Domotic
system, supporting various types of openings like shutters, awnings, and gates.
It provides properties to access opening attributes and methods to control
opening state, including open, close, and stop functionality.
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
from .base import CameEntity, ServerInfo


class OpeningStatus(Enum):
    """Status of an opening.

    Allowed values are:
        - STOPPED (0)
        - OPENING (1)
        - CLOSING (2)
        - SLAT_OPEN (3)
        - SLAT_CLOSE (4)
    """

    STOPPED = 0
    OPENING = 1
    CLOSING = 2
    SLAT_OPEN = 3
    SLAT_CLOSE = 4
    UNKNOWN = -1


class OpeningType(Enum):
    """Type of an opening.

    Allowed values are:
        - SHUTTER (0)
    """

    SHUTTER = 0
    UNKNOWN = -1


## Other types as guessed by AI chatbot, not tested yet.
## If uncommented, update the docstring above and the unit test too.
#    AWNING = 1
#    VENETIAN_BLIND = 2
#    GATE = 3


@dataclass
class Opening(CameEntity):
    """
    Opening entity in the CameDomotic API.

    Raises:
        ValueError: If `name` or `open_act_id` keys are missing from the input data
            or the auth argument is not an instance of the expected `Auth` class.
    """

    raw_data: dict[str, Any]
    auth: Auth
    server_info: ServerInfo | None = None

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "open_act_id", "close_act_id"],
            typed_keys={"open_act_id": int, "close_act_id": int},
        )
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def unique_id(self) -> str | None:
        """Stable unique identifier for this opening entity."""
        if self.server_info is None:
            return None
        return f"{self.server_info.keycode}_opening_{self.open_act_id}"

    @property
    def name(self) -> str:
        """Name of the opening."""
        return self.raw_data["name"]

    @property
    def status(self) -> OpeningStatus:
        """Current status of the opening. Allowed values: STOPPED (0), OPENING (1),
        CLOSING (2), SLAT_OPEN (3) and SLAT_CLOSE (4)."""
        try:
            return OpeningStatus(self.raw_data["status"])
        except ValueError:
            LOGGER.warning(
                "Unknown status '%s' encountered for opening '%s' (ID: %s). "
                "Returning OpeningStatus.UNKNOWN. Please report "
                "this to the library developers.",
                self.raw_data["status"],
                self.name,
                self.open_act_id,
            )
            return OpeningStatus.UNKNOWN

    @property
    def type(self) -> OpeningType:
        """
        Opening type.

        Raises:
            ValueError: If the opening type is not recognized.
        """
        try:
            return OpeningType(self.raw_data["type"])
        except ValueError:
            LOGGER.warning(
                "Unknown opening type '%s' encountered for opening '%s' (ID: %s). "
                "Returning OpeningType.UNKNOWN. Please report "
                "this to the library developers.",
                self.raw_data["type"],
                self.name,
                self.open_act_id,
            )
            return OpeningType.UNKNOWN

    @property
    def floor_ind(self) -> int | None:
        """Floor index where the opening is located."""
        return self.raw_data.get("floor_ind")

    @property
    def room_ind(self) -> int | None:
        """Room index where the opening is located."""
        return self.raw_data.get("room_ind")

    @property
    def open_act_id(self) -> int:
        """Actuator ID for opening action."""
        return self.raw_data["open_act_id"]

    @property
    def close_act_id(self) -> int:
        """Actuator ID for closing action."""
        return self.raw_data["close_act_id"]

    @property
    def partial_positions(self) -> list[str]:
        """List of configured partial opening positions, if any."""
        # TODO Check against actual values if it's a list of dict, int or strings
        return self.raw_data.get("partial", [])

    async def async_set_status(self, status: OpeningStatus) -> None:
        """
        Control the opening (open, close, stop, slat open, slat close).

        Args:
            status (OpeningStatus): Status to set for the opening.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        act_id = (
            self.close_act_id
            if status in (OpeningStatus.CLOSING, OpeningStatus.SLAT_CLOSE)
            else self.open_act_id
        )
        LOGGER.debug(
            "Sending cmd 'opening_move_req' for ID %s to status %s.",
            act_id,
            status.name,
        )

        # Using the opening ID (open_act_id) for control commands
        payload = {
            "act_id": act_id,
            "cmd_name": _CommandName.OPENING_MOVE.value,
            "wanted_status": status.value,
        }

        await self.auth.async_send_command(payload)

        # Update the status of the opening if everything went as expected
        self.raw_data["status"] = status.value
        LOGGER.info(
            "Successfully set status of opening '%s' (ID: %s) to %s.",
            self.name,
            self.open_act_id,
            status.name,
        )
