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
CAME Domotic timer entity models and control functionality.

This module implements the classes for working with timers in a CAME Domotic
system. Timers are scheduling entities that define time-based activation
windows for associated devices. They support enabling/disabling, day-of-week
toggling, and timetable configuration.

The ``days`` field is a 7-bit bitmask encoding active days of the week
(bit 0 = Monday, bit 6 = Sunday).
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

_DAY_NAMES: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


@dataclass(frozen=True)
class TimerTimeSlot:
    """A single time window within a timer's timetable.

    On some firmware versions, the ``stop`` and ``active`` fields may be
    absent. Properties return ``None`` for missing optional fields.

    Args:
        raw_data: Dictionary from a single timetable array entry.

    Raises:
        ValueError: If ``index`` or ``start`` keys are missing.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        if "index" not in self.raw_data or "start" not in self.raw_data:
            raise ValueError(
                "TimerTimeSlot requires 'index' and 'start' keys, "
                f"got: {list(self.raw_data.keys())}"
            )

    @property
    def index(self) -> int:
        """Zero-based slot position in the timetable (0-3)."""
        return self.raw_data["index"]

    @property
    def start_hour(self) -> int:
        """Start time hour (0-23). Defaults to 0 if missing."""
        return self.raw_data["start"].get("hour", 0)

    @property
    def start_min(self) -> int:
        """Start time minute (0-59). Defaults to 0 if missing."""
        return self.raw_data["start"].get("min", 0)

    @property
    def start_sec(self) -> int:
        """Start time second (0-59). Defaults to 0 if missing."""
        return self.raw_data["start"].get("sec", 0)

    @property
    def stop_hour(self) -> int | None:
        """Stop time hour, or ``None`` if the ``stop`` field is absent."""
        stop = self.raw_data.get("stop")
        return stop.get("hour", 0) if stop else None

    @property
    def stop_min(self) -> int | None:
        """Stop time minute, or ``None`` if the ``stop`` field is absent."""
        stop = self.raw_data.get("stop")
        return stop.get("min", 0) if stop else None

    @property
    def stop_sec(self) -> int | None:
        """Stop time second, or ``None`` if the ``stop`` field is absent."""
        stop = self.raw_data.get("stop")
        return stop.get("sec", 0) if stop else None

    @property
    def active(self) -> bool | None:
        """Whether this time window is active, or ``None`` if absent."""
        val = self.raw_data.get("active")
        return bool(val) if val is not None else None


@dataclass
class Timer(CameEntity):
    """Timer entity in the CameDomotic API.

    Represents a scheduling timer with time-based activation windows.
    Supports enabling/disabling, day-of-week toggling, and timetable
    configuration via the CAME API.

    The ``days`` field is a 7-bit bitmask (bit 0 = Monday, ...,
    bit 6 = Sunday). For example, ``days=85`` (binary ``1010101``)
    means Monday, Wednesday, Friday, and Sunday.

    Raises:
        ValueError: If ``name`` or ``id`` keys are missing from the input
            data or the auth argument is not an instance of ``Auth``.
    """

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "id"],
            typed_keys={"id": int},
        )
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )
        bars = self.raw_data.get("bars")
        timetable = self.raw_data.get("timetable", [])
        if bars is not None and isinstance(timetable, list) and bars != len(timetable):
            LOGGER.debug(
                "Timer '%s' (ID: %s): bars=%d but timetable has %d entries",
                self.raw_data.get("name"),
                self.raw_data.get("id"),
                bars,
                len(timetable),
            )

    @property
    def id(self) -> int:
        """Unique timer identifier."""
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Display name of the timer."""
        return self.raw_data["name"]

    @property
    def enabled(self) -> bool:
        """Whether the timer is globally enabled."""
        return bool(self.raw_data.get("enabled", 0))

    @property
    def days(self) -> int:
        """Bitmask of active days (bit 0 = Monday, ..., bit 6 = Sunday)."""
        return self.raw_data.get("days", 0)

    @property
    def bars(self) -> int:
        """Number of timetable bars reported by the server."""
        return self.raw_data.get("bars", 0)

    @property
    def timetable(self) -> list[TimerTimeSlot]:
        """Scheduled time slots.

        Malformed entries are skipped with a warning.
        """
        raw_timetable = self.raw_data.get("timetable", [])
        if not isinstance(raw_timetable, list):
            LOGGER.warning(
                "Timer '%s' (ID: %s): timetable is not a list, returning empty",
                self.name,
                self.id,
            )
            return []
        slots: list[TimerTimeSlot] = []
        for entry in raw_timetable:
            if not isinstance(entry, dict):
                LOGGER.warning(
                    "Timer '%s' (ID: %s): skipping non-dict timetable entry: %s",
                    self.name,
                    self.id,
                    entry,
                )
                continue
            try:
                slots.append(TimerTimeSlot(entry))
            except ValueError as exc:
                LOGGER.warning(
                    "Timer '%s' (ID: %s): skipping malformed timetable entry: %s",
                    self.name,
                    self.id,
                    exc,
                )
        return slots

    @property
    def active_days(self) -> list[str]:
        """Human-readable names of the days the timer is active on."""
        return [_DAY_NAMES[i] for i in range(7) if self.days & (1 << i)]

    def is_active_on_day(self, day_index: int) -> bool:
        """Check whether the timer is active on a specific day.

        Args:
            day_index: Day index (0=Monday, 1=Tuesday, ..., 6=Sunday).

        Returns:
            ``True`` if the timer is scheduled for this day, ``False``
            otherwise (including when *day_index* is out of range).
        """
        if not 0 <= day_index <= 6:
            return False
        return bool(self.days & (1 << day_index))

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    async def async_enable(self) -> None:
        """Enable the timer.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending cmd 'timers_enable_req' for timer '%s' (ID: %s), value=1.",
            self.name,
            self.id,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.TIMERS_ENABLE.value,
                "id": self.id,
                "value": 1,
            }
        )
        self.raw_data["enabled"] = 1
        LOGGER.info("Timer '%s' (ID: %s) enabled.", self.name, self.id)

    async def async_disable(self) -> None:
        """Disable the timer.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending cmd 'timers_enable_req' for timer '%s' (ID: %s), value=0.",
            self.name,
            self.id,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.TIMERS_ENABLE.value,
                "id": self.id,
                "value": 0,
            }
        )
        self.raw_data["enabled"] = 0
        LOGGER.info("Timer '%s' (ID: %s) disabled.", self.name, self.id)

    async def async_enable_day(self, day: int) -> None:
        """Enable the timer for a specific day of the week.

        Args:
            day: Day index (0=Monday, 1=Tuesday, ..., 6=Sunday).

        Raises:
            ValueError: If *day* is not in range 0-6.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not 0 <= day <= 6:
            raise ValueError(f"day must be 0-6, got {day}")
        LOGGER.debug(
            "Sending cmd 'timers_enable_day_req' for timer '%s' (ID: %s), "
            "day=%d, value=1.",
            self.name,
            self.id,
            day,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.TIMERS_ENABLE_DAY.value,
                "id": self.id,
                "day": day,
                "value": 1,
            }
        )
        self.raw_data["days"] = self.raw_data.get("days", 0) | (1 << day)
        LOGGER.info("Timer '%s' (ID: %s) day %d enabled.", self.name, self.id, day)

    async def async_disable_day(self, day: int) -> None:
        """Disable the timer for a specific day of the week.

        Args:
            day: Day index (0=Monday, 1=Tuesday, ..., 6=Sunday).

        Raises:
            ValueError: If *day* is not in range 0-6.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not 0 <= day <= 6:
            raise ValueError(f"day must be 0-6, got {day}")
        LOGGER.debug(
            "Sending cmd 'timers_enable_day_req' for timer '%s' (ID: %s), "
            "day=%d, value=0.",
            self.name,
            self.id,
            day,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.TIMERS_ENABLE_DAY.value,
                "id": self.id,
                "day": day,
                "value": 0,
            }
        )
        self.raw_data["days"] = self.raw_data.get("days", 0) & ~(1 << day)
        LOGGER.info("Timer '%s' (ID: %s) day %d disabled.", self.name, self.id, day)

    async def async_set_timetable(
        self,
        slots: list[tuple[int, int, int] | None],
    ) -> None:
        """Set the timer's timetable.

        Sends the complete timetable to the server. The list must contain
        exactly 4 entries — one per available slot. Use ``None`` for empty
        slots.

        Args:
            slots: List of 4 entries. Each entry is either a
                ``(hour, min, sec)`` tuple for an active slot, or ``None``
                for an empty slot.

        Raises:
            ValueError: If *slots* does not contain exactly 4 entries.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if len(slots) != 4:
            raise ValueError(f"timetable must have exactly 4 slots, got {len(slots)}")

        timetable: list[dict[str, Any]] = []
        for slot in slots:
            if slot is None:
                timetable.append({"start": {"hour": -1, "min": -1, "sec": -1}})
            else:
                hour, minute, sec = slot
                timetable.append({"start": {"hour": hour, "min": minute, "sec": sec}})

        LOGGER.debug(
            "Sending cmd 'timers_set_req' for timer '%s' (ID: %s).",
            self.name,
            self.id,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.TIMERS_SET.value,
                "id": self.id,
                "timetable": timetable,
            }
        )

        new_timetable: list[dict[str, Any]] = []
        for i, slot in enumerate(slots):
            if slot is not None:
                hour, minute, sec = slot
                new_timetable.append(
                    {
                        "start": {"hour": hour, "min": minute, "sec": sec},
                        "index": i,
                    }
                )
        self.raw_data["timetable"] = new_timetable
        LOGGER.info("Timer '%s' (ID: %s) timetable updated.", self.name, self.id)
