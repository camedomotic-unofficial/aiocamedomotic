# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic irrigation entity models and control functionality.

This module implements the classes for working with irrigation sectors in a
CAME Domotic system. An irrigation sector is a schedulable watering zone with
its own weekly programme, water percentage, start/end windows, and sprinkler
configuration. It can be forced on/off and its schedule can be
enabled/disabled.

.. note::
    Irrigation support is **not verified against a live plant**: the feature is
    absent from the reference plant's ``feature_list_resp``. The data model and
    commands are implemented from the behaviour of an existing, field-tested
    third-party integration. The exact shape of the ``start``, ``end``, and
    ``sprinklers`` fields may vary between firmware versions; their raw values
    are exposed as-is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..auth import Auth
from ..const import _CommandName
from ..utils import (
    LOGGER,
    EntityValidator,
)
from .base import CameEntity


@dataclass
class Irrigation(CameEntity):
    """Irrigation sector entity in the CameDomotic API.

    Represents a single schedulable watering zone. Sectors are keyed on their
    ``id`` (not ``act_id``). They can be forced on/off via :meth:`async_force`
    and their weekly schedule enabled/disabled via :meth:`async_set_enabled`.

    .. note::
        Not verified against a live plant — see the module docstring.

    Raises:
        ValueError: If the ``id`` key is missing from the input data, or the
            auth argument is not an instance of the expected ``Auth`` class.
    """

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["id"],
            typed_keys={"id": int},
        )
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def id(self) -> int:
        """Unique irrigation sector identifier."""
        return self.raw_data["id"]

    @property
    def name(self) -> str | None:
        """Display name of the sector, or ``None`` if the server omits it."""
        return self.raw_data.get("name")

    @property
    def enabled(self) -> bool:
        """Whether the sector's weekly schedule is enabled."""
        return bool(self.raw_data.get("enabled", 0))

    @property
    def status(self) -> int:
        """Raw running status reported by the server (``0`` when absent)."""
        return self.raw_data.get("status", 0)

    @property
    def forced(self) -> bool:
        """Whether the sector is currently in a forced watering cycle."""
        return bool(self.raw_data.get("forced", 0))

    @property
    def days(self) -> int:
        """Bitmask of active days (bit 0 = Monday, ..., bit 6 = Sunday)."""
        return self.raw_data.get("days", 0)

    @property
    def perc(self) -> int:
        """Water percentage configured for the sector (``0`` when absent)."""
        return self.raw_data.get("perc", 0)

    @property
    def start(self) -> Any:
        """Raw start-window value, or ``None`` if absent.

        The exact shape is firmware-dependent and passed through unchanged.
        """
        return self.raw_data.get("start")

    @property
    def end(self) -> Any:
        """Raw end-window value, or ``None`` if absent.

        The exact shape is firmware-dependent and passed through unchanged.
        """
        return self.raw_data.get("end")

    @property
    def sprinklers(self) -> Any:
        """Raw sprinkler configuration, or ``None`` if absent.

        The exact shape is firmware-dependent and passed through unchanged.
        """
        return self.raw_data.get("sprinklers")

    @property
    def is_running(self) -> bool:
        """Whether the sector is currently watering.

        ``True`` when the sector reports a non-zero ``status`` or is in a
        forced cycle.
        """
        return bool(self.raw_data.get("status") or self.raw_data.get("forced"))

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    async def async_force(self) -> None:
        """Toggle a forced watering cycle for this sector.

        The command is a **toggle**: sending it starts a forced cycle if the
        sector is idle, and stops the running cycle otherwise. Callers that
        want explicit on/off semantics should check :attr:`is_running` before
        issuing the command.

        The server replies with a generic acknowledgement (no dedicated
        response command), so only the standard ack is validated.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending cmd 'irrigation_force_req' for sector '%s' (ID: %s).",
            self.name,
            self.id,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.IRRIGATION_FORCE.value,
                "id": self.id,
            }
        )
        LOGGER.info(
            "Irrigation sector '%s' (ID: %s) force toggled.", self.name, self.id
        )

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable the sector's weekly schedule.

        Args:
            enabled: ``True`` to enable the schedule, ``False`` to disable it.

        The server replies with a generic acknowledgement (no dedicated
        response command), so only the standard ack is validated.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        value = 1 if enabled else 0
        LOGGER.debug(
            "Sending cmd 'irrigation_set_req' for sector '%s' (ID: %s), enabled=%d.",
            self.name,
            self.id,
            value,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.IRRIGATION_SET.value,
                "id": self.id,
                "enabled": value,
            }
        )
        self.raw_data["enabled"] = value
        LOGGER.info(
            "Irrigation sector '%s' (ID: %s) schedule %s.",
            self.name,
            self.id,
            "enabled" if enabled else "disabled",
        )
