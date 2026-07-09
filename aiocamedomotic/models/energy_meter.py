# SPDX-FileCopyrightText: 2024 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic energy meter entity models.

This module implements the class for working with energy meters in a CAME
Domotic system. Energy meters are read-only, plant-level entities exposed via
the ``energy`` feature: they report the instantaneous power measured on a
line together with energy values. They have no ``act_id`` and
no floor/room placement — the ``id`` field is their identifier, and it is
also the matching key for ``meter_instant_power_ind`` push updates.

Energy meters provide readings but do not support control commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..utils import (
    LOGGER,
    EntityValidator,
)
from .base import CameEntity


class EnergyMeterType(Enum):
    """Type of an energy meter, as reported in the ``meter_type`` field.

    Allowed values are:
        - POWER (1): Power meter (the only value observed on real servers).
        - UNKNOWN (-1): Returned when the server reports an unrecognised
          ``meter_type`` value.
    """

    POWER = 1
    UNKNOWN = -1


@dataclass
class EnergyMeter(CameEntity):
    """Read-only energy meter from the ``meters_list_resp`` endpoint.

    Represents an energy meter exposed via the ``energy`` feature. Energy
    meters are plant-level entities keyed by :attr:`id` (they have no
    ``act_id``, floor, or room). They report the current power reading and
    energy values, and cannot be controlled.

    Args:
        raw_data: Dictionary containing the meter data from the API.

    Raises:
        ValueError: If ``name`` or ``id`` keys are missing from the input
            data, or if ``id`` is not an integer.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "id"],
            typed_keys={"id": int},
        )

    @property
    def id(self) -> int:
        """Unique meter identifier.

        This is also the matching key for ``meter_instant_power_ind``
        push updates (energy meters have no ``act_id``).
        """
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Display name of the meter."""
        return self.raw_data["name"]

    @property
    def meter_type(self) -> EnergyMeterType:
        """Type of the meter (POWER is the only value observed so far)."""
        try:
            return EnergyMeterType(self.raw_data["meter_type"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown energy meter type '%s' encountered for meter '%s' "
                "(ID: %s). Returning EnergyMeterType.UNKNOWN. Please report "
                "this to the library developers.",
                self.raw_data.get("meter_type"),
                self.name,
                self.id,
            )
            return EnergyMeterType.UNKNOWN

    @property
    def instant_power(self) -> int:
        """Current power reading, in the unit reported by :attr:`unit`.

        The value is passed through exactly as reported by the server
        (no unit conversion is applied).
        """
        return self.raw_data.get("instant_power", 0)

    @property
    def unit(self) -> str:
        """Unit of measurement for :attr:`instant_power` (``'W'`` observed)."""
        return self.raw_data.get("unit", "W")

    @property
    def energy_unit(self) -> str:
        """Unit of measurement (``'Wh'`` observed) for the
        :attr:`last_24h_avg` and :attr:`last_month_avg` values."""
        return self.raw_data.get("energy_unit", "Wh")

    @property
    def produced(self) -> int:
        """Raw ``produced`` field from the server.

        ``0`` observed on consumption meters; semantics for production
        meters are unverified.
        """
        return self.raw_data.get("produced", 0)

    @property
    def last_24h_avg(self) -> int:
        """Raw ``last_24h_avg`` field from the server, in :attr:`energy_unit`.

        The value is passed through exactly as reported by the server.
        """
        return self.raw_data.get("last_24h_avg", 0)

    @property
    def last_month_avg(self) -> int:
        """Raw ``last_month_avg`` field from the server, in :attr:`energy_unit`.

        The value is passed through exactly as reported by the server.
        """
        return self.raw_data.get("last_month_avg", 0)
