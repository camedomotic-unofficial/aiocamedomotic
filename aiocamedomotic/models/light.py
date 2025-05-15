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
CAME Domotic light entity models and control functionality.

This module implements the classes for working with lights in a CAME Domotic
system, supporting both standard on/off lights (STEP_STEP type) and dimmable
lights (DIMMER type). It provides properties to access light attributes and
methods to control light state, including on/off functionality and brightness
control for dimmable lights.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from ..auth import Auth
from ..utils import (
    EntityValidator,
    LOGGER,
)

from .base import CameEntity


class LightStatus(Enum):
    """Status of a light.

    Allowed values are:
        - OFF (0)
        - ON (1)
    """

    OFF = 0
    ON = 1


class LightType(Enum):
    """Type of a light.

    Allowed values are:
        - STEP_STEP (normal lights)
        - DIMMER (dimmable lights)
    """

    STEP_STEP = "STEP_STEP"
    DIMMER = "DIMMER"
    UNKNOWN = "UNKNOWN_LIGHT_TYPE"


@dataclass
class Light(CameEntity):
    """
    Light entity in the CameDomotic API.

    Raises:
        ValueError: If `name` or `act_id` keys are missing from the input data the auth
            argument is not an instance of the expected `Auth` class.
    """

    raw_data: dict
    auth: Auth

    def __post_init__(self):
        EntityValidator.validate_data(self.raw_data, required_keys=["name", "act_id"])
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def act_id(self) -> int:
        """ID of the light."""
        return self.raw_data["act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index of the light."""
        return self.raw_data["floor_ind"]

    @property
    def name(self) -> str:
        """Name of the light."""
        return self.raw_data["name"]

    @property
    def room_ind(self) -> int:
        """Room index of the light."""
        return self.raw_data["room_ind"]

    @property
    def status(self) -> LightStatus:
        """Status of the light. Allowed values are ON (1) and OFF (0)."""
        return LightStatus(self.raw_data["status"])

    @property
    def type(self) -> LightType:
        """
        Light type. Allowed values are "STEP_STEP" (normal lights) and "DIMMER"
        (dimmable lights).

        Raises:
            ValueError: If the light type is not recognized.
        """
        try:
            return LightType(self.raw_data["type"])
        except ValueError:
            LOGGER.warning(
                "Unknown light type '%s' encountered for light '%s' (ID: %s). "
                "Returning LightType.UNKNOWN. Please report this to the library developers.",
                self.raw_data["type"],
                self.name,
                self.act_id,
            )
            return LightType.UNKNOWN

    @property
    def perc(self) -> int:
        """
        Brightness percentage of the light (range 0-100).
        Non dimmable lights will always return 100.
        """
        return self.raw_data.get("perc", 100)

    async def async_set_status(
        self, status: LightStatus, brightness: Optional[int] = None
    ) -> None:
        """Control the light.

        Args:
            status (LightStatus): Status of the light.
            brightness (Optional[int]): Brightness percentage of the light (range
                0-100). If the brightness is not provided, it will stay unchanged.
                This argument is ignored for non-dimmable lights.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        # Early exit for non-dimmable lights receiving a brightness value
        if self.type != LightType.DIMMER:
            LOGGER.debug(
                "Light '%s' (type: %s) is not dimmable or type is unknown. "
                "Ignoring brightness setting.",
                self.name,
                self.type.name,
            )
            brightness = None  # Ignore brightness since it's not applicable

        if self.type == LightType.UNKNOWN:
            LOGGER.warning(
                "Attempting to set status for light '%s' (ID: %s) with UNKNOWN type. "
                "Command might fail or have unintended effects.",
                self.name,
                self.act_id,
            )

        client_id = await self.auth.async_get_valid_client_id()
        LOGGER.debug(
            "User authenticated, sending 'light_switch_req' command to the API."
        )
        payload = self._prepare_light_payload(status, brightness, client_id)
        await self.auth.async_send_command(payload)

        # Update the status of the light if everything went as expected
        self.raw_data["status"] = status.value
        if brightness is not None:
            self.raw_data["perc"] = max(0, min(brightness, 100))

    def _prepare_light_payload(
        self, status: LightStatus, brightness: Optional[int], client_id: str
    ) -> Dict:
        """Prepare the payload for the light control API call."""
        payload = {
            "sl_appl_msg": {
                "act_id": self.act_id,
                "client": client_id,
                "cmd_name": "light_switch_req",
                "cseq": self.auth.cseq + 1,
                "wanted_status": status.value,
            },
            "sl_appl_msg_type": "domo",
            "sl_client_id": client_id,
            "sl_cmd": "sl_data_req",
        }

        if brightness is not None and isinstance(brightness, int):
            payload["sl_appl_msg"]["perc"] = max(  # type: ignore
                0, min(brightness, 100)
            )  # Normalize and add brightness

        return payload
