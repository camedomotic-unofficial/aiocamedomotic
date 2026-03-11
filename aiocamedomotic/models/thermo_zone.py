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
and analog sensors in a CAME Domotic system. It provides access to zone
state (temperature, setpoint, mode, season, fan speed, dehumidifier) and
analog sensor readings (temperature, humidity, pressure), as well as
control methods to configure zone settings such as target temperature,
operating mode, and fan speed.
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


class ThermoZoneFanSpeed(Enum):
    """Fan speed setting for a thermoregulation zone.

    Allowed values are:
        - OFF (0)
        - SLOW (1)
        - MEDIUM (2)
        - FAST (3)
        - AUTO (4)
    """

    OFF = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3
    AUTO = 4
    UNKNOWN = -1


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

    @property
    def fan_speed(self) -> ThermoZoneFanSpeed:
        """Fan speed setting for the thermoregulation zone.

        Returns ``ThermoZoneFanSpeed.UNKNOWN`` for unrecognized values.
        """
        try:
            return ThermoZoneFanSpeed(self.raw_data.get("fan_speed", -1))
        except ValueError:
            LOGGER.warning(
                "Unknown thermo zone fan speed '%s' for zone '%s' (ID: %s). "
                "Returning ThermoZoneFanSpeed.UNKNOWN. "
                "Please report this to the library developers.",
                self.raw_data.get("fan_speed"),
                self.name,
                self.act_id,
            )
            return ThermoZoneFanSpeed.UNKNOWN

    @property
    def dehumidifier_enabled(self) -> bool:
        """Whether the dehumidifier is enabled for this zone."""
        return bool(self.raw_data.get("dehumidifier", {}).get("enabled", 0))

    @property
    def dehumidifier_setpoint(self) -> float | None:
        """Dehumidifier humidity setpoint in percent, or None if not set."""
        val = self.raw_data.get("dehumidifier", {}).get("setpoint")
        if val is None:
            return None
        return float(val)

    @property
    def t1(self) -> float | None:
        """Temperature sensor 1 reading in degrees Celsius, or None."""
        raw = self.raw_data.get("t1")
        if raw is None:
            return None
        return raw / 10.0

    @property
    def t2(self) -> float | None:
        """Temperature sensor 2 reading in degrees Celsius, or None."""
        raw = self.raw_data.get("t2")
        if raw is None:
            return None
        return raw / 10.0

    @property
    def t3(self) -> float | None:
        """Temperature sensor 3 reading in degrees Celsius, or None."""
        raw = self.raw_data.get("t3")
        if raw is None:
            return None
        return raw / 10.0

    async def async_set_config(
        self,
        mode: ThermoZoneMode,
        set_point: float,
        *,
        fan_speed: ThermoZoneFanSpeed | None = None,
    ) -> None:
        """Configure the thermoregulation zone.

        .. note::
            The season cannot be changed via this method. The CAME server
            silently ignores any season value sent in a zone config request.
            Use :meth:`CameDomoticAPI.async_set_thermo_season` to change the
            season at the plant level.

        Args:
            mode: Operating mode to set.
            set_point: Target temperature in degrees Celsius.
            fan_speed: Fan speed setting (optional, requires extended info).

        Raises:
            ValueError: If ``mode`` or ``fan_speed`` is ``UNKNOWN``.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if mode == ThermoZoneMode.UNKNOWN:
            raise ValueError("Cannot set mode to UNKNOWN")

        if fan_speed is not None and fan_speed == ThermoZoneFanSpeed.UNKNOWN:
            raise ValueError("Cannot set fan_speed to UNKNOWN")

        LOGGER.debug(
            "Sending 'thermo_zone_config_req' command for zone '%s' (ID: %s)",
            self.name,
            self.act_id,
        )
        payload = self._prepare_thermo_config_payload(mode, set_point, fan_speed)
        await self.auth.async_send_command(payload)

        # Update the local state if the command succeeded
        self.raw_data["mode"] = mode.value
        self.raw_data["set_point"] = int(round(set_point * 10))
        if fan_speed is not None:
            self.raw_data["fan_speed"] = fan_speed.value

        LOGGER.info(
            "Zone '%s' (ID: %s) configured: mode=%s, set_point=%.1f°C%s",
            self.name,
            self.act_id,
            mode.name,
            set_point,
            f", fan_speed={fan_speed.name}" if fan_speed is not None else "",
        )

    def _prepare_thermo_config_payload(
        self,
        mode: ThermoZoneMode,
        set_point: float,
        fan_speed: ThermoZoneFanSpeed | None,
    ) -> dict[str, Any]:
        """Prepare the payload for the zone config API call."""
        payload: dict[str, Any] = {
            "act_id": self.act_id,
            "cmd_name": _CommandName.THERMO_ZONE_CONFIG.value,
            "mode": mode.value,
            "set_point": int(round(set_point * 10)),
            "extended_infos": 1 if fan_speed is not None else 0,
        }

        if fan_speed is not None:
            payload["fan_speed"] = fan_speed.value

        return payload

    async def async_set_temperature(self, temperature: float) -> None:
        """Set the target temperature, keeping the current operating mode.

        .. warning::
            This method only has an effect when the zone is in
            ``ThermoZoneMode.MANUAL`` mode. When the zone is in any other mode
            (e.g. ``AUTO``), the server accepts the request without error but
            silently discards the new setpoint. Use
            :meth:`async_set_config` with ``mode=ThermoZoneMode.MANUAL`` to
            guarantee that the setpoint is applied.

        Args:
            temperature: Target temperature in degrees Celsius.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self.async_set_config(mode=self.mode, set_point=temperature)

    async def async_set_mode(self, mode: ThermoZoneMode) -> None:
        """Set the operating mode, keeping the current target temperature.

        Args:
            mode: Operating mode to set.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self.async_set_config(mode=mode, set_point=self.set_point)

    async def async_set_fan_speed(self, fan_speed: ThermoZoneFanSpeed) -> None:
        """Set the fan speed, keeping the current mode and temperature.

        Args:
            fan_speed: Fan speed to set.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self.async_set_config(
            mode=self.mode, set_point=self.set_point, fan_speed=fan_speed
        )


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

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "act_id"],
            typed_keys={"act_id": int},
        )

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
