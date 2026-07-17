# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
Base classes for the CAME Domotic API entity model system.

This module defines the foundational base classes used across the CAME Domotic
API implementation, including the core CameEntity class and derived entity types
such as User and ServerInfo that are common across the API functionality.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..auth import Auth
from ..const import _CommandType
from ..errors import CameDomoticAuthError, CameDomoticServerError
from ..utils import (
    LOGGER,
    EntityValidator,
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

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
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
            If login with the new credentials fails, a
            ``CameDomoticAuthError`` is raised and the previous credentials
            are restored so the API client remains connected as the
            original user.
        """

        LOGGER.debug("Attempting to switch to user '%s'", self.name)

        # Backup current user details
        backup_user = self.auth.backup_auth_credentials()

        try:
            await self._attempt_login_as_current_user(password)
        except CameDomoticAuthError as e:
            LOGGER.error("Unable to set user '%s' as current user (%s)", self.name, e)
            LOGGER.warning("Restoring previous credentials after failed user switch")
            self.auth.restore_auth_credentials(backup_user)
            raise

        LOGGER.info("Successfully switched to user '%s'", self.name)

    async def async_delete(self) -> None:
        """Delete this user from the CAME Domotic server.

        Sends a delete-user request to the server for the user identified by
        this object's ``name`` property.

        Raises:
            ValueError: If this user is the currently authenticated user.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if self.name == self.auth.current_username:
            raise ValueError(
                f"Cannot delete the currently authenticated user ('{self.name}')."
            )
        LOGGER.debug("Deleting user '%s'", self.name)
        await self.auth.async_send_command(
            {},
            command_type=_CommandType.DELETE_USER_REQUEST.value,
            additional_payload={"sl_login": self.name},
        )
        LOGGER.info("User '%s' deleted", self.name)

    async def async_change_password(
        self, current_password: str, new_password: str
    ) -> None:
        """Change the password of this user on the CAME Domotic server.

        Args:
            current_password (str): The user's current password.
            new_password (str): The desired new password.

        Note:
            Changing the password does not invalidate existing active sessions
            for that user — they remain valid until they expire. The new
            password will be required at the next login.

            If the changed user is the currently authenticated user, the stored
            credentials are updated automatically in the active session — no
            additional action is required.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error or the
                password change is rejected (``sl_user_pwd_change_ack_reason``
                is non-zero).
        """
        LOGGER.debug("Changing password for user '%s'", self.name)
        json_response = await self.auth.async_send_command(
            {},
            command_type=_CommandType.CHANGE_USER_PASSWORD_REQUEST.value,
            additional_payload={
                "sl_login": self.name,
                "sl_pwd": current_password,
                "sl_new_pwd": new_password,
            },
        )
        ack_reason = json_response.get("sl_user_pwd_change_ack_reason", 0)
        if ack_reason != 0:
            raise CameDomoticServerError(
                f"Password change rejected by server "
                f"(sl_user_pwd_change_ack_reason={ack_reason})"
            )
        if self.name == self.auth.current_username:
            # pylint: disable-next=protected-access
            self.auth._update_stored_password(new_password)
            LOGGER.debug(
                "Stored password updated in active session for user '%s'", self.name
            )
        LOGGER.info("Password changed for user '%s'", self.name)

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
    """Keycode of the server (CAME proprietary unique identifier)."""

    serial: str
    """Serial number of the server."""

    features: list[str]
    """List of feature strings reported by the server.

    Each feature corresponds to a functional block (e.g. lights, openings).
    Values are plain strings whose known values are defined in
    :class:`~aiocamedomotic.const.ServerFeature`. Because ``ServerFeature``
    is a :class:`~enum.StrEnum`, you can compare entries against enum
    members directly (e.g.
    ``ServerFeature.LIGHTS in server_info.features``).

    The return type is kept as ``list[str]`` so that features introduced by
    newer firmware versions are preserved even if the library does not yet
    define them in :class:`~aiocamedomotic.const.ServerFeature`.
    """

    swver: str | None = None
    """Software version of the server."""

    type: str | None = None
    """Type of the server."""

    board: str | None = None
    """Board type of the server."""

    def __post_init__(self) -> None:
        """Validate that required properties are present and not None."""
        missing: list[str] = []

        if self.keycode is None:
            missing.append("keycode")
        if self.serial is None:
            missing.append("serial")
        if self.features is None:
            missing.append("features")

        if missing:
            raise ValueError(
                f"Missing required ServerInfo properties: {', '.join(missing)}"
            )


@dataclass
class ServerDateTime(CameEntity):
    """Date and time reported by a CAME Domotic server.

    Returned by :meth:`CameDomoticAPI.async_get_server_datetime`. Wraps the
    ``datetime_req`` response, which carries the server clock both as a Unix
    epoch (UTC) and as a local wall-clock string, plus the server timezone and
    the current daylight-saving-time flag.

    Useful for diagnosing the timestamps carried by push updates.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(self.raw_data, required_keys=["epoch"])

    @property
    def epoch(self) -> int:
        """Server clock as a Unix epoch, in seconds (UTC)."""
        return self.raw_data["epoch"]

    @property
    def timezone_name(self) -> str | None:
        """IANA timezone name of the server (e.g. ``"Europe/Rome"``).

        ``None`` if the server response does not include it.
        """
        return self.raw_data.get("server_timezone")

    @property
    def datetime_string(self) -> str | None:
        """Local wall-clock time as a ``"YYYY-MM-DD HH:MM:SS"`` string.

        Already offset for the server timezone and DST. ``None`` if the server
        response does not include it.
        """
        return self.raw_data.get("datetime")

    @property
    def daylight_saving_time(self) -> bool:
        """Whether daylight saving time is currently in effect on the server."""
        return bool(self.raw_data.get("daylight_saving_time", 0))

    @property
    def utc_datetime(self) -> datetime:
        """Server clock as a timezone-aware :class:`~datetime.datetime` (UTC).

        Derived from :attr:`epoch`.
        """
        return datetime.fromtimestamp(self.epoch, tz=timezone.utc)


@dataclass
class Floor(CameEntity):
    """
    Floor entity in the CAME Domotic API.

    Represents a floor in the building structure with its identifier and name.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data, required_keys=["floor_ind", "name"]
        )

    @property
    def id(self) -> int:
        """ID of the floor."""
        return self.raw_data["floor_ind"]

    @property
    def name(self) -> str:
        """Name of the floor."""
        return self.raw_data["name"]


@dataclass
class Room(CameEntity):
    """
    Room entity in the CAME Domotic API.

    Represents a room in the building structure with its identifier, name,
    and the floor it belongs to.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data, required_keys=["room_ind", "name", "floor_ind"]
        )

    @property
    def id(self) -> int:
        """ID of the room."""
        return self.raw_data["room_ind"]

    @property
    def name(self) -> str:
        """Name of the room."""
        return self.raw_data["name"]

    @property
    def floor_id(self) -> int:
        """ID of the floor this room belongs to."""
        return self.raw_data["floor_ind"]


@dataclass
class TopologyRoom(CameEntity):
    """A room in the plant topology.

    Lightweight representation used by :class:`PlantTopology` to describe the
    building structure independently of any specific device type.
    """

    id: int
    """Numeric identifier of the room (``room_ind``)."""

    name: str
    """Human-readable name of the room."""


@dataclass
class TopologyFloor(CameEntity):
    """A floor in the plant topology.

    Contains the list of rooms discovered on this floor.
    """

    id: int
    """Numeric identifier of the floor (``floor_ind``)."""

    name: str
    """Human-readable name of the floor."""

    rooms: list[TopologyRoom]
    """Rooms belonging to this floor."""


@dataclass
class PlantTopology(CameEntity):
    """Complete plant topology (floors and rooms).

    Built by merging data from the standard ``floor_list_req`` /
    ``room_list_req`` endpoints and the nested device list commands
    (``nested_light_list_req``, ``nested_openings_list_req``,
    ``nested_thermo_list_req``).
    """

    floors: list[TopologyFloor]
    """All floors in the plant, each containing its rooms."""


@dataclass
class TerminalGroup(CameEntity):
    """Terminal group in the CAME Domotic API.

    Represents a user permission group (e.g. ``"ETI/Domo"``). Groups are
    assigned to users at creation time via
    :meth:`CameDomoticAPI.async_add_user`. Use
    :meth:`CameDomoticAPI.async_get_terminal_groups` to retrieve the
    available group names before creating a user.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data, required_keys=["group_name", "group_id"]
        )

    @property
    def name(self) -> str:
        """Name of the group (e.g. ``"ETI/Domo"``)."""
        return self.raw_data["group_name"]

    @property
    def id(self) -> int:
        """Numeric ID of the group."""
        return self.raw_data["group_id"]
