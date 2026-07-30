# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic digital input (binary sensor) entity models.

This module implements the classes for working with digital inputs in a CAME
Domotic system. Digital inputs represent binary sensors such as physical
buttons, contact sensors, and similar devices. They are read-only for their
state, but inputs that raise a technical alarm or keep a signalling counter can
be acknowledged via :meth:`DigitalInput.async_ack`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..auth import Auth
from ..const import _CommandName, _CommandNameResponse
from ..utils import (
    LOGGER,
    EntityValidator,
)
from .base import CameEntity


class DigitalInputStatus(Enum):
    """Status of a digital input.

    Allowed values are:
        - ACTIVE (0): the input is active (e.g. a button is pressed)
        - IDLE (1): the input is idle (e.g. a button is not pressed)
    """

    ACTIVE = 0
    IDLE = 1
    UNKNOWN = -1


class DigitalInputType(Enum):
    """Type of a digital input.

    Allowed values are:
        - STATUS (1): standard status input
    """

    STATUS = 1
    UNKNOWN = -1


@dataclass
class DigitalInput(CameEntity):
    """
    Digital input (binary sensor) entity in the CameDomotic API.

    Digital inputs report their binary state (ACTIVE/IDLE) and cannot be
    switched remotely. Inputs that raise a technical alarm or keep a
    signalling counter can, however, be acknowledged via
    :meth:`async_ack`.

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
        """ID of the digital input."""
        return self.raw_data["act_id"]

    @property
    def name(self) -> str:
        """Name of the digital input."""
        return self.raw_data["name"]

    @property
    def status(self) -> DigitalInputStatus:
        """Status of the digital input: ACTIVE (0) or IDLE (1).

        ``ACTIVE`` means the input is triggered (e.g. a button is being
        pressed). ``IDLE`` means the input is in its normal resting state.

        Returns ``DigitalInputStatus.UNKNOWN`` when the status field is
        absent from the server response (some digital inputs do not
        report a status until their first state change).
        """
        raw_status = self.raw_data.get("status")
        if raw_status is None:
            return DigitalInputStatus.UNKNOWN
        try:
            return DigitalInputStatus(raw_status)
        except ValueError:
            LOGGER.warning(
                "Unknown digital input status '%s' encountered for "
                "digital input '%s' (ID: %s). "
                "Returning DigitalInputStatus.UNKNOWN. Please report this "
                "to the library developers.",
                raw_status,
                self.name,
                self.act_id,
            )
            return DigitalInputStatus.UNKNOWN

    @property
    def type(self) -> DigitalInputType:
        """Type of the digital input.

        Returns ``DigitalInputType.UNKNOWN`` when the type value is not
        recognized.
        """
        try:
            return DigitalInputType(self.raw_data["type"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown digital input type '%s' encountered for "
                "digital input '%s' (ID: %s). "
                "Returning DigitalInputType.UNKNOWN. Please report this "
                "to the library developers.",
                self.raw_data.get("type"),
                self.name,
                self.act_id,
            )
            return DigitalInputType.UNKNOWN

    @property
    def addr(self) -> int:
        """Address of the digital input."""
        return self.raw_data.get("addr", 0)

    @property
    def utc_time(self) -> int:
        """UTC timestamp of the last event (Unix epoch seconds).

        Returns ``0`` if the digital input has never been triggered.
        """
        return self.raw_data.get("utc_time", 0)

    async def async_ack(self) -> None:
        """Acknowledge the digital input.

        Some digital inputs raise a technical alarm or keep a signalling
        counter that stays latched until it is acknowledged. This command
        clears that pending signalling for the input; it has no effect on
        inputs that do not track one.

        The command is keyed on :attr:`addr` (not :attr:`act_id`). The
        server replies with ``digitalin_ack_resp`` echoing the input record,
        which is validated.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self.auth.async_get_valid_client_id()
        LOGGER.debug(
            "User authenticated, sending 'digitalin_ack_req' command to the API."
        )

        payload = {
            "cmd_name": _CommandName.DIGITALIN_ACK.value,
            "addr": self.addr,
        }
        await self.auth.async_send_command(
            payload,
            response_command=_CommandNameResponse.DIGITALIN_ACK.value,
        )

        LOGGER.info(
            "Digital input '%s' (ID: %s, addr: %s) acknowledged",
            self.name,
            self.act_id,
            self.addr,
        )
