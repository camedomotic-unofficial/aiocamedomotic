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
system, supporting standard on/off lights (STEP_STEP type), dimmable lights
(DIMMER type), and RGB color lights (RGB type). It provides properties to
access light attributes and methods to control light state, including on/off
functionality, brightness control, and RGB color control.
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


class LightStatus(Enum):
    """Status of a light.

    Allowed values are:
        - OFF (0)
        - ON (1)
        - AUTO (4)
    """

    OFF = 0
    ON = 1
    AUTO = 4
    UNKNOWN = -1


class LightType(Enum):
    """Type of a light.

    Allowed values are:
        - STEP_STEP (normal lights)
        - DIMMER (dimmable lights)
        - RGB (color lights with brightness via HSV V channel)
    """

    STEP_STEP = "STEP_STEP"
    DIMMER = "DIMMER"
    RGB = "RGB"
    UNKNOWN = "UNKNOWN_LIGHT_TYPE"


@dataclass
class Light(CameEntity):
    """
    Light entity in the CameDomotic API.

    Raises:
        ValueError: If `name` or `act_id` keys are missing from the
            input data or the auth argument is not an instance of the
            expected `Auth` class.
    """

    raw_data: dict[str, Any]
    auth: Auth
    server_info: ServerInfo | None = None

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
    def unique_id(self) -> str | None:
        """Stable unique identifier for this light entity."""
        if self.server_info is None:
            return None
        return f"{self.server_info.keycode}_light_{self.act_id}"

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
        """Status of the light. Allowed values are OFF (0), ON (1) and AUTO (4)."""
        try:
            return LightStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown light status '%s' encountered for light '%s' (ID: %s). "
                "Returning LightStatus.UNKNOWN. Please report this "
                "to the library developers.",
                self.raw_data.get("status"),
                self.name,
                self.act_id,
            )
            return LightStatus.UNKNOWN

    @property
    def type(self) -> LightType:
        """
        Light type. Allowed values are "STEP_STEP" (normal lights),
        "DIMMER" (dimmable lights), and "RGB" (color lights).

        Raises:
            ValueError: If the light type is not recognized.
        """
        try:
            return LightType(self.raw_data["type"])
        except ValueError:
            LOGGER.warning(
                "Unknown light type '%s' encountered for light '%s' (ID: %s). "
                "Returning LightType.UNKNOWN. Please report this "
                "to the library developers.",
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

    @property
    def rgb(self) -> list[int] | None:
        """
        RGB color values of the light as [R, G, B], each in range 0-255.
        Returns None for non-RGB lights.
        """
        return self.raw_data.get("rgb")

    async def async_set_status(
        self,
        status: LightStatus,
        brightness: int | None = None,
        rgb: list[int] | None = None,
    ) -> None:
        """Control the light.

        Args:
            status (LightStatus): Status of the light.
            brightness (Optional[int]): Brightness percentage of the light (range
                0-100). If the brightness is not provided, it will stay unchanged.
                This argument is ignored for STEP_STEP lights.
            rgb (Optional[List[int]]): RGB color values as [R, G, B], each in
                range 0-255. If not provided, the color stays unchanged.
                This argument is ignored for non-RGB lights.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        # Ignore brightness for non-dimmable/non-RGB lights
        if self.type not in (LightType.DIMMER, LightType.RGB):
            LOGGER.debug(
                "Light '%s' (type: %s) is not dimmable or type is unknown. "
                "Ignoring brightness setting.",
                self.name,
                self.type.name,
            )
            brightness = None

        # Ignore RGB for non-RGB lights
        if self.type != LightType.RGB and rgb is not None:
            LOGGER.debug(
                "Light '%s' (type: %s) does not support RGB. Ignoring rgb setting.",
                self.name,
                self.type.name,
            )
            rgb = None

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
        payload = self._prepare_light_payload(status, brightness, rgb, client_id)
        await self.auth.async_send_command(payload)

        # Update the status of the light if everything went as expected
        self.raw_data["status"] = status.value
        if brightness is not None:
            self.raw_data["perc"] = max(0, min(brightness, 100))
        if rgb is not None:
            self.raw_data["rgb"] = [max(0, min(v, 255)) for v in rgb]

        LOGGER.info(
            "Light '%s' (ID: %s) set to %s (brightness=%s, rgb=%s)",
            self.name,
            self.act_id,
            status.name,
            brightness,
            rgb,
        )

    def _prepare_light_payload(
        self,
        status: LightStatus,
        brightness: int | None,
        rgb: list[int] | None,
        client_id: str,
    ) -> dict[str, Any]:
        """Prepare the payload for the light control API call."""
        payload = {
            "act_id": self.act_id,
            "cmd_name": _CommandName.LIGHT_SWITCH.value,
            "wanted_status": status.value,
        }

        if brightness is not None and isinstance(brightness, int):
            payload["perc"] = max(0, min(brightness, 100))

        if rgb is not None and isinstance(rgb, list) and len(rgb) == 3:
            payload["rgb"] = [max(0, min(v, 255)) for v in rgb]

        return payload
