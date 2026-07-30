# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic scenario entity models and control functionality.

This module implements the classes for working with scenarios in a CAME Domotic
system. Scenarios represent pre-configured automation sequences that can be
activated to control multiple devices at once. It provides properties to access
scenario attributes and a method to activate a scenario.
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


class ScenarioStatus(Enum):
    """Status of a scenario.

    Allowed values are:
        - OFF (0): scenario is not active
        - TRIGGERED (1): scenario has just been activated and is executing
        - ACTIVE (2): scenario is currently in effect
    """

    OFF = 0
    TRIGGERED = 1
    ACTIVE = 2
    UNKNOWN = -1


@dataclass
class Scenario(CameEntity):
    """
    Scenario entity in the CameDomotic API.

    Represents a pre-configured automation scenario that can be activated
    to control multiple devices at once.

    Raises:
        ValueError: If `name` or `id` keys are missing from the input data or the auth
            argument is not an instance of the expected `Auth` class.
    """

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "id"],
            typed_keys={"id": int},
        )
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def id(self) -> int:
        """ID of the scenario."""
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Name of the scenario."""
        return self.raw_data["name"]

    @property
    def icon_id(self) -> int:
        """Icon ID associated with the scenario."""
        return self.raw_data.get("icon_id", 0)

    @property
    def scenario_status(self) -> ScenarioStatus:
        """Scenario-specific status: OFF (0), TRIGGERED (1), or ACTIVE (2)."""
        try:
            return ScenarioStatus(self.raw_data["scenario_status"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown scenario_status '%s' encountered for scenario '%s' (ID: %s). "
                "Returning ScenarioStatus.UNKNOWN. "
                "Please report this to the library developers.",
                self.raw_data.get("scenario_status"),
                self.name,
                self.id,
            )
            return ScenarioStatus.UNKNOWN

    @property
    def status(self) -> int:
        """General status of the scenario."""
        return self.raw_data.get("status", 0)

    @property
    def user_defined(self) -> int:
        """Whether the scenario is user-defined (1) or system-defined (0)."""
        return self.raw_data.get("user-defined", 0)

    async def async_activate(self) -> None:
        """Activate the scenario.

        Sends the scenario activation command to the CAME Domotic server.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending cmd 'scenario_activation_req' for scenario '%s' (ID: %s).",
            self.name,
            self.id,
        )

        payload = {
            "cmd_name": _CommandName.SCENARIO_ACTIVATION.value,
            "id": self.id,
        }

        await self.auth.async_send_command(payload)

        LOGGER.info(
            "Successfully activated scenario '%s' (ID: %s).",
            self.name,
            self.id,
        )

    async def async_rename(self, name: str) -> None:
        """Rename the scenario.

        Sends the scenario rename command to the CAME Domotic server and
        updates the local ``name`` accordingly.

        .. note::
            Renaming is meant for **user-defined** scenarios (see
            :attr:`user_defined`): the official CAME app does not allow
            renaming system-defined ones. The command is sent anyway, but the
            server behaviour on system-defined scenarios is unverified.

        Args:
            name (str): The new name of the scenario.

        Raises:
            ValueError: If ``name`` is not a non-empty string.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not self.user_defined:
            LOGGER.warning(
                "Renaming scenario '%s' (ID: %s), which is not user-defined: "
                "the server may ignore or reject the request.",
                self.name,
                self.id,
            )

        LOGGER.debug(
            "Sending cmd 'scenario_rename_req' for scenario '%s' (ID: %s).",
            self.name,
            self.id,
        )

        payload = {
            "cmd_name": _CommandName.SCENARIO_RENAME.value,
            "id": self.id,
            "name": name,
        }

        await self.auth.async_send_command(payload)
        self.raw_data["name"] = name

        LOGGER.info(
            "Successfully renamed scenario (ID: %s) to '%s'.",
            self.id,
            name,
        )

    async def async_delete(self) -> None:
        """Delete the scenario from the CAME Domotic server.

        .. warning::
            The deletion is irreversible: the server discards the scenario
            and there is no way to restore it.

        .. note::
            Deletion is meant for **user-defined** scenarios (see
            :attr:`user_defined`): the official CAME app does not allow
            deleting system-defined ones. The command is sent anyway, but the
            server behaviour on system-defined scenarios is unverified.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not self.user_defined:
            LOGGER.warning(
                "Deleting scenario '%s' (ID: %s), which is not user-defined: "
                "the server may ignore or reject the request.",
                self.name,
                self.id,
            )

        LOGGER.debug(
            "Sending cmd 'scenario_delete_req' for scenario '%s' (ID: %s).",
            self.name,
            self.id,
        )

        payload = {
            "cmd_name": _CommandName.SCENARIO_DELETE.value,
            "id": self.id,
        }

        await self.auth.async_send_command(payload)

        LOGGER.info(
            "Successfully deleted scenario '%s' (ID: %s).",
            self.name,
            self.id,
        )
