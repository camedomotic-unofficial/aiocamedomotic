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
CAME Domotic status update handling.

This module provides classes for processing and representing status updates
from the CAME Domotic system. It implements typed dataclass wrappers for each
update indication type, a factory function to parse raw update dicts, and a
specialized list-based data structure to track chronological updates received
from the CAME Domotic API.
"""

from __future__ import annotations

from collections import UserList
from dataclasses import dataclass
from typing import Any

from ..const import _UPDATE_CMD_TO_DEVICE_TYPE, DeviceType, UpdateIndicator
from ..utils import LOGGER
from .base import CameEntity
from .light import LightStatus, LightType
from .opening import OpeningStatus
from .relay import RelayStatus
from .scenario import ScenarioStatus
from .thermo_zone import (
    ThermoZoneFanSpeed,
    ThermoZoneMode,
    ThermoZoneSeason,
    ThermoZoneStatus,
)


def get_update_device_type(update: dict[str, Any]) -> DeviceType | None:
    """Return the device type for a status update dict, or None if unknown.

    Args:
        update: A single update dict from the ``status_update_resp`` result
            array. Must contain a ``cmd_name`` key.

    Returns:
        The corresponding :class:`~aiocamedomotic.const.DeviceType`, or
        ``None`` if the ``cmd_name`` is not recognized.
    """
    cmd_name: str | None = update.get("cmd_name")
    if cmd_name is None:
        return None
    return _UPDATE_CMD_TO_DEVICE_TYPE.get(cmd_name)


# ---------------------------------------------------------------------------
# Typed update classes
# ---------------------------------------------------------------------------


@dataclass
class DeviceUpdate(CameEntity):
    """Base class for a typed status update from the CAME API.

    Wraps the raw update dict and exposes common properties. Subclasses add
    device-specific accessors.

    Args:
        raw_data: The original dict from the ``status_update_resp`` result
            array.
    """

    raw_data: dict[str, Any]

    @property
    def cmd_name(self) -> str:
        """The indication ``cmd_name`` string from the raw update."""
        return self.raw_data.get("cmd_name", "")

    @property
    def update_indicator(self) -> UpdateIndicator | None:
        """The :class:`~aiocamedomotic.const.UpdateIndicator` for this update,
        or ``None`` if the ``cmd_name`` is not recognized."""
        try:
            return UpdateIndicator(self.cmd_name)
        except ValueError:
            return None

    @property
    def device_type(self) -> DeviceType | None:
        """The :class:`~aiocamedomotic.const.DeviceType` for this update,
        or ``None`` if the ``cmd_name`` is not recognized."""
        return _UPDATE_CMD_TO_DEVICE_TYPE.get(self.cmd_name)

    @property
    def device_id(self) -> int | None:
        """Primary device identifier (``act_id``, ``open_act_id``, or ``id``).

        Returns the first available identifier, or ``None`` if none is present.
        """
        return (
            self.raw_data.get("act_id")
            or self.raw_data.get("open_act_id")
            or self.raw_data.get("id")
        )

    @property
    def name(self) -> str:
        """Device name from the update."""
        return self.raw_data.get("name", "")


@dataclass
class LightUpdate(DeviceUpdate):
    """Typed update for a light device (``light_switch_ind`` /
    ``light_update_ind``).
    """

    @property
    def act_id(self) -> int:
        """Light actuator ID."""
        return self.raw_data["act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index."""
        return self.raw_data.get("floor_ind", 0)

    @property
    def room_ind(self) -> int:
        """Room index."""
        return self.raw_data.get("room_ind", 0)

    @property
    def status(self) -> LightStatus:
        """Light status (OFF, ON, AUTO)."""
        return LightStatus(self.raw_data["status"])

    @property
    def light_type(self) -> LightType:
        """Light type (STEP_STEP, DIMMER, RGB)."""
        try:
            return LightType(self.raw_data.get("type", "UNKNOWN_LIGHT_TYPE"))
        except ValueError:
            return LightType.UNKNOWN

    @property
    def perc(self) -> int:
        """Brightness percentage (0-100). Defaults to 100 for non-dimmable."""
        return self.raw_data.get("perc", 100)

    @property
    def rgb(self) -> list[int] | None:
        """RGB color values ``[R, G, B]`` (0-255 each), or ``None``."""
        return self.raw_data.get("rgb")


@dataclass
class OpeningUpdate(DeviceUpdate):
    """Typed update for an opening device (``opening_move_ind`` /
    ``opening_update_ind``).
    """

    @property
    def open_act_id(self) -> int:
        """Actuator ID for the opening action."""
        return self.raw_data["open_act_id"]

    @property
    def close_act_id(self) -> int:
        """Actuator ID for the closing action."""
        return self.raw_data["close_act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index."""
        return self.raw_data.get("floor_ind", 0)

    @property
    def room_ind(self) -> int:
        """Room index."""
        return self.raw_data.get("room_ind", 0)

    @property
    def status(self) -> OpeningStatus:
        """Opening status (STOPPED, OPENING, CLOSING, etc.)."""
        try:
            return OpeningStatus(self.raw_data["status"])
        except ValueError:
            return OpeningStatus.UNKNOWN

    @property
    def device_id(self) -> int | None:
        """For openings the primary ID is ``open_act_id``."""
        return self.raw_data.get("open_act_id")


@dataclass
class RelayUpdate(DeviceUpdate):
    """Typed update for a relay device (``relay_status_ind`` /
    ``relay_update_ind``).
    """

    @property
    def act_id(self) -> int:
        """Relay actuator ID."""
        return self.raw_data["act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index."""
        return self.raw_data.get("floor_ind", 0)

    @property
    def room_ind(self) -> int:
        """Room index."""
        return self.raw_data.get("room_ind", 0)

    @property
    def status(self) -> RelayStatus:
        """Relay status (OFF, ON)."""
        try:
            return RelayStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            return RelayStatus.UNKNOWN


@dataclass
class ThermoZoneUpdate(DeviceUpdate):
    """Typed update for a thermostat zone (``thermo_zone_info_ind`` /
    ``thermo_update_ind``).
    """

    @property
    def act_id(self) -> int:
        """Zone actuator ID."""
        return self.raw_data["act_id"]

    @property
    def floor_ind(self) -> int:
        """Floor index."""
        return self.raw_data.get("floor_ind", 0)

    @property
    def room_ind(self) -> int:
        """Room index."""
        return self.raw_data.get("room_ind", 0)

    @property
    def status(self) -> ThermoZoneStatus:
        """Zone status (OFF, ON)."""
        try:
            return ThermoZoneStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            return ThermoZoneStatus.OFF

    @property
    def temperature(self) -> float:
        """Current temperature in degrees Celsius (converted from
        ``temp_dec``).
        """
        return self.raw_data.get("temp_dec", 0) / 10.0

    @property
    def mode(self) -> ThermoZoneMode:
        """Operating mode (OFF, MANUAL, AUTO, JOLLY)."""
        try:
            return ThermoZoneMode(self.raw_data.get("mode", -1))
        except ValueError:
            return ThermoZoneMode.UNKNOWN

    @property
    def set_point(self) -> float:
        """Target temperature in degrees Celsius (converted from
        ``set_point``).
        """
        return self.raw_data.get("set_point", 0) / 10.0

    @property
    def season(self) -> ThermoZoneSeason:
        """Season setting (PLANT_OFF, WINTER, SUMMER)."""
        try:
            return ThermoZoneSeason(self.raw_data.get("season", "unknown"))
        except ValueError:
            return ThermoZoneSeason.UNKNOWN

    @property
    def fan_speed(self) -> ThermoZoneFanSpeed:
        """Fan speed setting (OFF, SLOW, MEDIUM, FAST, AUTO)."""
        try:
            return ThermoZoneFanSpeed(self.raw_data.get("fan_speed", -1))
        except ValueError:
            return ThermoZoneFanSpeed.UNKNOWN

    @property
    def dehumidifier_enabled(self) -> bool:
        """Whether the dehumidifier is enabled."""
        return bool(self.raw_data.get("dehumidifier", {}).get("enabled", 0))

    @property
    def dehumidifier_setpoint(self) -> float | None:
        """Dehumidifier humidity setpoint in percent, or None if not present."""
        val = self.raw_data.get("dehumidifier", {}).get("setpoint")
        if val is None:
            return None
        return float(val)

    @property
    def t1(self) -> float | None:
        """Temperature sensor 1 reading in degrees Celsius."""
        raw = self.raw_data.get("t1")
        return raw / 10.0 if raw is not None else None

    @property
    def t2(self) -> float | None:
        """Temperature sensor 2 reading in degrees Celsius."""
        raw = self.raw_data.get("t2")
        return raw / 10.0 if raw is not None else None

    @property
    def t3(self) -> float | None:
        """Temperature sensor 3 reading in degrees Celsius."""
        raw = self.raw_data.get("t3")
        return raw / 10.0 if raw is not None else None


@dataclass
class ScenarioUpdate(DeviceUpdate):
    """Typed update for a scenario (``scenario_status_ind`` /
    ``scenario_activation_ind`` / ``scenario_user_ind``).
    """

    @property
    def id(self) -> int:
        """Scenario ID."""
        return self.raw_data["id"]

    @property
    def scenario_status(self) -> ScenarioStatus:
        """Scenario status (OFF, TRIGGERED, ACTIVE)."""
        try:
            return ScenarioStatus(self.raw_data["scenario_status"])
        except (ValueError, KeyError):
            return ScenarioStatus.UNKNOWN

    @property
    def device_id(self) -> int | None:
        """For scenarios the primary ID is ``id``."""
        return self.raw_data.get("id")


@dataclass
class DigitalInputUpdate(DeviceUpdate):
    """Typed update for a digital input (``digitalin_status_ind`` /
    ``digitalin_update_ind``).
    """

    @property
    def act_id(self) -> int:
        """Digital input actuator ID."""
        return self.raw_data["act_id"]

    @property
    def status(self) -> int:
        """Digital input status value."""
        return self.raw_data.get("status", 0)

    @property
    def addr(self) -> int:
        """Digital input address."""
        return self.raw_data.get("addr", 0)

    @property
    def utc_time(self) -> int:
        """UTC timestamp of the digital input event."""
        return self.raw_data.get("utc_time", 0)


@dataclass
class PlantUpdate(DeviceUpdate):
    """Marker update for ``plant_update_ind``.

    When this indication is received, all cached devices must be discarded and
    re-fetched from the server.
    """

    @property
    def is_plant_update(self) -> bool:
        """Always returns ``True``."""
        return True


# ---------------------------------------------------------------------------
# Factory and mapping
# ---------------------------------------------------------------------------

_INDICATOR_TO_UPDATE_CLASS: dict[str, type[DeviceUpdate]] = {
    "light_switch_ind": LightUpdate,
    "light_update_ind": LightUpdate,
    "opening_move_ind": OpeningUpdate,
    "opening_update_ind": OpeningUpdate,
    "thermo_zone_info_ind": ThermoZoneUpdate,
    "thermo_update_ind": ThermoZoneUpdate,
    "scenario_status_ind": ScenarioUpdate,
    "scenario_activation_ind": ScenarioUpdate,
    "scenario_user_ind": ScenarioUpdate,
    "relay_status_ind": RelayUpdate,
    "relay_update_ind": RelayUpdate,
    "digitalin_status_ind": DigitalInputUpdate,
    "digitalin_update_ind": DigitalInputUpdate,
    "plant_update_ind": PlantUpdate,
}


def parse_update(raw: dict[str, Any]) -> DeviceUpdate:
    """Parse a raw update dict into the appropriate typed
    :class:`DeviceUpdate` subclass.

    Args:
        raw: A single update dict from the ``status_update_resp`` result
            array.

    Returns:
        A typed :class:`DeviceUpdate` subclass instance. If the ``cmd_name``
        is not recognized, a generic :class:`DeviceUpdate` is returned so
        that the consumer can still access :attr:`~DeviceUpdate.raw_data`.
    """
    cmd_name = raw.get("cmd_name", "")
    cls = _INDICATOR_TO_UPDATE_CLASS.get(cmd_name, DeviceUpdate)
    if cls is DeviceUpdate and cmd_name:
        LOGGER.debug(
            "Unknown update cmd_name '%s', using generic DeviceUpdate", cmd_name
        )
    return cls(raw_data=raw)


# ---------------------------------------------------------------------------
# UpdateList
# ---------------------------------------------------------------------------


@dataclass
class UpdateList(UserList[dict[str, Any]], CameEntity):
    """Chronological list of status updates from the CameDomotic API.

    Extends :class:`~collections.UserList` to maintain backward compatibility:
    iterating yields raw ``dict`` objects. Additional methods provide typed
    access and filtering.
    """

    def __init__(self, updates: UserList[dict[str, Any]] | None = None):
        try:
            super().__init__(updates)
        except TypeError as exc:
            LOGGER.warning("Caught exception in the UpdateList method", exc_info=exc)
            super().__init__()
        LOGGER.debug("UpdateList created with %d update(s)", len(self.data))

    def get_by_device_type(self, device_type: DeviceType) -> list[dict[str, Any]]:
        """Return raw update dicts filtered to the given device type.

        Args:
            device_type: The :class:`~aiocamedomotic.const.DeviceType` to
                filter by.

        Returns:
            A list of raw update dicts whose ``cmd_name`` maps to
            *device_type*.
        """
        return [u for u in self.data if get_update_device_type(u) == device_type]

    def get_typed_updates(self) -> list[DeviceUpdate]:
        """Parse all updates into typed :class:`DeviceUpdate` objects.

        Returns:
            A list of :class:`DeviceUpdate` subclass instances, one per raw
            update dict.
        """
        return [parse_update(u) for u in self.data]

    def get_typed_by_device_type(self, device_type: DeviceType) -> list[DeviceUpdate]:
        """Parse and filter updates by device type.

        Args:
            device_type: The :class:`~aiocamedomotic.const.DeviceType` to
                filter by.

        Returns:
            Typed :class:`DeviceUpdate` instances whose
            :attr:`~DeviceUpdate.device_type` matches *device_type*.
        """
        return [
            parse_update(u)
            for u in self.data
            if get_update_device_type(u) == device_type
        ]

    @property
    def has_plant_update(self) -> bool:
        """Whether any update in this list is a ``plant_update_ind``.

        When ``True``, the consumer should discard all cached devices and
        re-fetch them from the server.
        """
        return any(u.get("cmd_name") == UpdateIndicator.PLANT.value for u in self.data)
