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
Base classes for the CAME Domotic API entity model system.

This module defines the foundational base classes used across the CAME Domotic
API implementation, including the core CameEntity class and derived entity types
such as User and ServerInfo that are common across the API functionality.
"""

from dataclasses import dataclass
from typing import Optional

from ..auth import Auth
from ..errors import CameDomoticAuthError
from ..utils import (
    EntityValidator,
    LOGGER,
)


class CameEntity:
    """Base class for all the CAME entities."""


@dataclass
class User(CameEntity):
    """
    User in the CAME Domotic API.

    Raises:
        ValueError: If `name` key is missing from the input data the auth argument is
            not an instance of the expected `Auth` class.
    """

    raw_data: dict
    auth: Auth

    def __post_init__(self):
        EntityValidator.validate_data(self.raw_data, required_keys=["name"])

    @property
    def name(self) -> str:
        """Name of the user."""
        return self.raw_data["name"]

    async def async_set_as_current_user(self, password: str) -> None:
        """Set the user as the current user in the CAME Domotic API session.

        Args:
            password (str): Password of the user.

        Raises:
            CameDomoticAuthError: If the authentication fails.

        Note:
            This method logs out the current user and logs in with the new user.
            In case of failure, the previous user is restored.
        """

        # Backup current user details
        backup_user = self.auth.backup_auth_credentials()

        try:
            await self._attempt_login_as_current_user(password)
        except CameDomoticAuthError as e:
            LOGGER.error("Unable to set user '%s' as current user (%s)", self.name, e)
            await self.auth.restore_auth_credentials(backup_user)
            raise

    async def _attempt_login_as_current_user(self, password: str) -> None:
        """Attempt to login with the user details.

        Args:
            password (str): New user's password.

        Raises:
            CameDomoticAuthError: If login fails.
        """
        await self.auth.async_logout()
        self.auth.update_auth_credentials(self.name, password)
        await self.auth.async_login()


@dataclass
class ServerInfo(CameEntity):
    """Server information of a CAME Domotic server."""

    keycode: str
    """Keycode of the server (i.e. MAC address in the form 001122AABBCC)."""

    serial: str
    """Serial number of the server."""

    list: list[str]
    """List of features supported by the server.

    Known values (as of now) are:
        - "lights"
        - "openings"
        - "thermoregulation"
        - "scenarios"
        - "digitalin"
        - "energy"
        - "loadsctrl"
    """

    swver: Optional[str] = None
    """Software version of the server."""

    type: Optional[str] = None
    """Type of the server."""

    board: Optional[str] = None
    """Board type of the server."""

    def __post_init__(self):
        """Validate that required properties are present and not None."""
        missing = []

        if self.keycode is None:
            missing.append("keycode")
        if self.serial is None:
            missing.append("serial")
        if self.list is None:
            missing.append("list")

        if missing:
            raise ValueError(
                f"Missing required ServerInfo properties: {', '.join(missing)}"
            )
