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
CAME Domotic thermoregulation entity models.

This module implements the classes for working with thermoregulation zones
and analog sensors in a CAME Domotic system. It provides read-only access
to zone state (temperature, setpoint, mode, season) and analog sensor
readings (temperature, humidity, pressure).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..auth import Auth
from ..utils import (
    LOGGER,
    EntityValidator,
)
from .base import CameEntity, ServerInfo


class ThermoZoneStatus(Enum):
    """Status of a thermoregulation zone.

    Allowed values are:
        - OFF (0)
        - ON (1)
    """

    OFF = 0
    ON = 1


class ThermoZoneMode(Enum):
    """Operating mode of a thermoregulation zone.

    Allowed values are:
        - OFF (0)
        - MANUAL (1)
        - AUTO (2)
        - JOLLY (3)
    """

    OFF = 0
    MANUAL = 1
    AUTO = 2
    JOLLY = 3
    UNKNOWN = -1


class ThermoZoneSeason(Enum):
    """Season setting for a thermoregulation zone.

    Allowed values are:
        - PLANT_OFF ("plant_off")
        - WINTER ("winter")
        - SUMMER ("summer")
    """

    PLANT_OFF = "plant_off"
    WINTER = "winter"
    SUMMER = "summer"
    UNKNOWN = "unknown"


@dataclass
class ThermoZone(CameEntity):
    """
    Thermoregulation zone entity in the CameDomotic API.

    Represents a single thermoregulation zone with its current state,
    including temperature readings, setpoint, operating mode, and season.

    Temperature values from the API are integers multiplied by 10
    (e.g., 215 = 21.5 degrees C). Properties in this class return
    converted float values in degrees.

    Raises:
        ValueError: If ``name`` or ``act_id`` keys are missing from the
            input data, or the auth argument is not an instance of the
            expected ``Auth`` class.
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
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def unique_id(self) -> str | None:
        """Stable unique identifier for this thermoregulation zone entity."""
        if self.server_info is None:
            return None
        return f"{self.server_info.keycode}_thermo_zone_{self.act_id}"

    @property
    def act_id(self) -> int:
        """ID of the thermoregulation zone."""
        return self.raw_data["act_id"]

    @property
    def name(self) -> str:
        """Name of the thermoregulation zone."""
        return self.raw_data["name"]

    @property
    def floor_ind(self) -> int:
        """Floor index of the thermoregulation zone."""
        return self.raw_data["floor_ind"]

    @property
    def room_ind(self) -> int:
        """Room index of the thermoregulation zone."""
        return self.raw_data["room_ind"]

    @property
    def status(self) -> ThermoZoneStatus:
        """Status of the thermoregulation zone (OFF or ON)."""
        try:
            return ThermoZoneStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown thermo zone status '%s' for zone '%s' (ID: %s). "
                "Please report this to the library developers.",
                self.raw_data.get("status"),
                self.name,
                self.act_id,
            )
            return ThermoZoneStatus.OFF

    @property
    def temperature(self) -> float:
        """Current temperature in degrees Celsius.

        Handles both ``temp`` (from list responses) and ``temp_dec``
        (from status indications) field names.
        """
        raw = self.raw_data.get("temp", self.raw_data.get("temp_dec", 0))
        return raw / 10.0

    @property
    def mode(self) -> ThermoZoneMode:
        """Operating mode of the thermoregulation zone.

        Returns ``ThermoZoneMode.UNKNOWN`` for unrecognized mode values.
        """
        try:
            return ThermoZoneMode(self.raw_data.get("mode", -1))
        except ValueError:
            LOGGER.warning(
                "Unknown thermo zone mode '%s' for zone '%s' (ID: %s). "
                "Returning ThermoZoneMode.UNKNOWN. "
                "Please report this to the library developers.",
                self.raw_data.get("mode"),
                self.name,
                self.act_id,
            )
            return ThermoZoneMode.UNKNOWN

    @property
    def set_point(self) -> float:
        """Target temperature in degrees Celsius."""
        return self.raw_data.get("set_point", 0) / 10.0

    @property
    def season(self) -> ThermoZoneSeason:
        """Season setting for the thermoregulation zone.

        Returns ``ThermoZoneSeason.UNKNOWN`` for unrecognized season values.
        """
        try:
            return ThermoZoneSeason(self.raw_data.get("season", "unknown"))
        except ValueError:
            LOGGER.warning(
                "Unknown thermo zone season '%s' for zone '%s' (ID: %s). "
                "Returning ThermoZoneSeason.UNKNOWN. "
                "Please report this to the library developers.",
                self.raw_data.get("season"),
                self.name,
                self.act_id,
            )
            return ThermoZoneSeason.UNKNOWN

    @property
    def antifreeze(self) -> float | None:
        """Antifreeze temperature in degrees Celsius, or None if not set."""
        raw = self.raw_data.get("antifreeze")
        if raw is None:
            return None
        return raw / 10.0

    @property
    def leaf(self) -> bool:
        """Whether this is an actual zone (leaf node) in the hierarchy."""
        return self.raw_data.get("leaf", True)


@dataclass
class AnalogSensor(CameEntity):
    """
    Analog sensor from the CAME Domotic thermoregulation system.

    Represents a top-level temperature, humidity, or pressure sensor
    reading from the thermoregulation list response. These sensors are
    separate from the thermoregulation zones.

    Note:
        The ``value`` property returns the real sensor reading in the
        unit reported by ``unit`` (e.g., degrees C, %, hPa).

    Raises:
        ValueError: If ``name`` or ``act_id`` keys are missing from
            the input data.
    """

    raw_data: dict[str, Any]
    server_info: ServerInfo | None = None

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "act_id"],
            typed_keys={"act_id": int},
        )

    @property
    def unique_id(self) -> str | None:
        """Stable unique identifier for this analog sensor entity."""
        if self.server_info is None:
            return None
        return f"{self.server_info.keycode}_analog_sensor_{self.act_id}"

    @property
    def act_id(self) -> int:
        """ID of the analog sensor."""
        return self.raw_data["act_id"]

    @property
    def name(self) -> str:
        """Name of the analog sensor."""
        return self.raw_data["name"]

    @property
    def value(self) -> float:
        """Sensor reading in the unit reported by ``unit``."""
        raw = self.raw_data.get("value", 0)
        if self.unit == "°C":
            return raw / 10.0
        return float(raw)

    @property
    def unit(self) -> str:
        """Unit of measurement (e.g., '°C', '%', 'hPa')."""
        return self.raw_data.get("unit", "")
