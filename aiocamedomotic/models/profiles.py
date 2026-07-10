# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic weekly schedule profiles ("profile_data").

CAME transmits weekly schedules as arrays of digit strings — one string per
day, one character per time slot, each character a digit ``1``-``5``
selecting one of the five levels shown in the official app. Two features use
this pattern (both confirmed by captured traffic, ETI/Domo swver 3.0.1):

- **loadsctrl** (:class:`LoadsCtrlProfile`): 7 strings of 24 characters
  (Monday..Sunday, one slot per hour).
- **thermo** (:class:`ThermoProfile`): 8 strings of 96 characters
  (Monday..Sunday plus the **JOLLY** profile as the 8th row, one slot per
  quarter hour).

Although the thermo wire format has 15-minute slots, the official app edits
profiles **per hour** for both features, always writing four identical
quarters per hour. This library follows the same contract: the public API
speaks in hours only (edit spans are whole hours), while the wire resolution
is preserved internally so that ``from_wire(x).to_wire() == x`` holds
byte-for-byte for any server-provided value.

Profiles are immutable value objects: editing methods return a new instance
and never modify the original, so the only way changes reach the server is
an explicit set command carrying ``to_wire()``. Captured traffic shows that
profile reads and writes always carry the **full week**; a profile object
cannot represent less than the full grid, so partial sends are impossible
by construction.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, time
from enum import IntEnum
from typing import Any, ClassVar, Self

from ..utils import LOGGER


class ProfileDay(IntEnum):
    """A row of a weekly profile grid.

    ``MONDAY``..``SUNDAY`` are ``0``..``6``, matching both the wire row
    order (Monday first) and :meth:`datetime.date.weekday`, so
    ``ProfileDay(some_date.weekday())`` is always correct.

    ``JOLLY`` (``7``) is the special thermo profile used while a thermo zone
    is in JOLLY mode; it is the 8th wire row of thermo profiles and is not a
    valid day for loadsctrl profiles.
    """

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    JOLLY = 7


WEEKDAYS: tuple[ProfileDay, ...] = (
    ProfileDay.MONDAY,
    ProfileDay.TUESDAY,
    ProfileDay.WEDNESDAY,
    ProfileDay.THURSDAY,
    ProfileDay.FRIDAY,
    ProfileDay.SATURDAY,
    ProfileDay.SUNDAY,
)
"""The seven real weekdays (Monday..Sunday), excluding :attr:`ProfileDay.JOLLY`.

Convenience for editing methods on thermo profiles, where an omitted
``days`` argument targets every row including JOLLY.
"""


@dataclass(frozen=True)
class ProfileSpan:
    """A run of consecutive slots sharing the same level (read-only view).

    Produced by :meth:`WeeklyProfile.spans`. The range is half-open:
    ``start`` is inclusive, ``end`` is exclusive; an ``end`` of ``time(0)``
    means "through midnight" (end of day).
    """

    start: time
    end: time
    level: int


class WeeklyProfile:
    """Immutable weekly schedule grid (abstract base).

    Concrete subclasses (:class:`LoadsCtrlProfile`, :class:`ThermoProfile`)
    define the grid shape via :attr:`DAYS` and :attr:`WIRE_SLOTS_PER_DAY`;
    all parsing, reading, and editing logic lives here.

    Instances are immutable value objects: editing methods
    (:meth:`with_level`, :meth:`with_day_copied`) return a **new** instance,
    and equality/hashing are by value (two profiles of the same class with
    the same grid are equal). Construct instances via :meth:`from_wire` or
    :meth:`constant`.

    The public API speaks in **hours** (the official app edits per hour);
    the internal grid keeps the wire resolution, so serializing an unedited
    profile reproduces the server bytes exactly.
    """

    # ClassVar annotations are class attributes, not instance slots, but
    # pylint's declare-non-slot check flags them in slotted classes.
    DAYS: ClassVar[tuple[ProfileDay, ...]]  # pylint: disable=declare-non-slot
    """The rows of the grid, in wire order."""

    WIRE_SLOTS_PER_DAY: ClassVar[int]  # pylint: disable=declare-non-slot
    """Number of wire slots per day row (a multiple of 24)."""

    LEVELS: ClassVar[frozenset[int]] = frozenset({1, 2, 3, 4, 5})
    """Allowed level values (the five levels shown in the official app)."""

    __slots__ = ("_rows",)

    _rows: tuple[tuple[int, ...], ...]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        days = getattr(cls, "DAYS", None)
        slots = getattr(cls, "WIRE_SLOTS_PER_DAY", None)
        if not days:
            raise TypeError(f"{cls.__name__} must define a non-empty DAYS tuple")
        if not isinstance(slots, int) or slots <= 0 or slots % 24 != 0:
            raise TypeError(
                f"{cls.__name__}.WIRE_SLOTS_PER_DAY must be a positive multiple "
                f"of 24, got {slots!r}"
            )

    def __init__(self, rows: Sequence[Sequence[int]]) -> None:
        """Create a profile from a grid of levels (one row per day).

        Args:
            rows: Exactly ``len(DAYS)`` rows of exactly
                ``WIRE_SLOTS_PER_DAY`` integers, each in :attr:`LEVELS`.

        Raises:
            TypeError: If called on the abstract ``WeeklyProfile`` class.
            ValueError: If the grid shape or any level value is invalid.
        """
        cls = type(self)
        if cls is WeeklyProfile:
            raise TypeError(
                "WeeklyProfile is an abstract base: instantiate "
                "LoadsCtrlProfile or ThermoProfile instead"
            )
        if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
            raise ValueError(
                f"rows must be a sequence of exactly {len(cls.DAYS)} day rows"
            )
        if len(rows) != len(cls.DAYS):
            raise ValueError(
                f"rows must contain exactly {len(cls.DAYS)} day rows, got {len(rows)}"
            )
        frozen_rows: list[tuple[int, ...]] = []
        for index, row in enumerate(rows):
            if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
                raise ValueError(
                    f"rows[{index}] must be a sequence of exactly "
                    f"{cls.WIRE_SLOTS_PER_DAY} integer levels"
                )
            frozen_row = tuple(row)
            if len(frozen_row) != cls.WIRE_SLOTS_PER_DAY:
                raise ValueError(
                    f"rows[{index}] must contain exactly "
                    f"{cls.WIRE_SLOTS_PER_DAY} levels, got {len(frozen_row)}"
                )
            for value in frozen_row:
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value not in cls.LEVELS
                ):
                    raise ValueError(
                        f"rows[{index}] contains invalid level {value!r}: "
                        f"allowed levels are {sorted(cls.LEVELS)}"
                    )
            frozen_rows.append(frozen_row)
        self._rows = tuple(frozen_rows)

    # region Wire boundary

    @classmethod
    def from_wire(cls, data: Sequence[str]) -> Self:
        """Parse a profile from its raw wire format.

        The wire format is a list of digit strings, one per row of
        :attr:`DAYS` in order, each of exactly :attr:`WIRE_SLOTS_PER_DAY`
        characters, each character a digit in :attr:`LEVELS`.

        Guarantee: ``cls.from_wire(x).to_wire() == x`` byte-for-byte —
        nothing is normalized or reinterpreted.

        On profile types with sub-hour wire slots, a row whose hours are not
        uniform (different levels within the same hour) is unexpected — the
        official app edits per hour — so a warning is logged, but the data
        is accepted and preserved exactly.

        Args:
            data: The raw profile rows, e.g. from a server response.

        Raises:
            TypeError: If called on the abstract ``WeeklyProfile`` class.
            ValueError: If the shape or any character is invalid.
        """
        if cls is WeeklyProfile:
            raise TypeError(
                "WeeklyProfile is an abstract base: use "
                "LoadsCtrlProfile.from_wire() or ThermoProfile.from_wire()"
            )
        if isinstance(data, (str, bytes)) or not isinstance(data, Sequence):
            raise ValueError(
                f"profile data must be a list of exactly {len(cls.DAYS)} "
                "strings (one per day, Monday first)"
            )
        if len(data) != len(cls.DAYS):
            raise ValueError(
                f"profile data must contain exactly {len(cls.DAYS)} strings "
                f"(one per day, Monday first), got {len(data)}"
            )
        allowed_chars = {str(level) for level in cls.LEVELS}
        rows: list[tuple[int, ...]] = []
        for index, day_str in enumerate(data):
            if not isinstance(day_str, str) or len(day_str) != cls.WIRE_SLOTS_PER_DAY:
                raise ValueError(
                    f"profile data[{index}] must be a string of exactly "
                    f"{cls.WIRE_SLOTS_PER_DAY} characters"
                )
            if any(char not in allowed_chars for char in day_str):
                raise ValueError(
                    f"profile data[{index}] must contain only digits in "
                    f"{sorted(cls.LEVELS)}"
                )
            rows.append(tuple(int(char) for char in day_str))
        profile = cls(rows)
        slots_per_hour = cls._slots_per_hour()
        if slots_per_hour > 1 and any(
            len(set(row[hour * slots_per_hour : (hour + 1) * slots_per_hour])) > 1
            for row in rows
            for hour in range(24)
        ):
            LOGGER.warning(
                "%s data contains different levels within the same hour; "
                "this is unexpected (the official app edits profiles per "
                "hour). The data is preserved as-is, but hour-based edits "
                "overwrite whole hours. Please report this to the library "
                "developers.",
                cls.__name__,
            )
        return profile

    def to_wire(self) -> list[str]:
        """Serialize to the raw wire format (a fresh list of digit strings).

        For a profile obtained via :meth:`from_wire` and not edited since,
        this returns exactly the original input.
        """
        return ["".join(str(value) for value in row) for row in self._rows]

    # endregion

    # region Constructors

    @classmethod
    def constant(cls, level: int) -> Self:
        """Create a profile with every slot of every row set to ``level``.

        Raises:
            TypeError: If called on the abstract ``WeeklyProfile`` class.
            ValueError: If ``level`` is not in :attr:`LEVELS`.
        """
        if cls is WeeklyProfile:
            raise TypeError(
                "WeeklyProfile is an abstract base: use "
                "LoadsCtrlProfile.constant() or ThermoProfile.constant()"
            )
        cls._validate_level(level)
        return cls([[level] * cls.WIRE_SLOTS_PER_DAY for _ in cls.DAYS])

    # endregion

    # region Reading

    def level_at(self, day: ProfileDay | int, at: time | datetime | int) -> int:
        """Return the level active on ``day`` at the given moment.

        Args:
            day: The profile row to read (a :class:`ProfileDay` or its
                integer value).
            at: The moment of day: an ``int`` hour (0-23), a
                :class:`datetime.time`, or a :class:`datetime.datetime`
                (its time of day is used; the date is **not** used to pick
                ``day``). Any time is accepted — it resolves to the
                containing wire slot, so no hour alignment is required for
                reads.

        Raises:
            ValueError: If ``day`` is not a row of this profile type or
                ``at`` is not a valid moment of day.
        """
        row = self._rows[type(self).DAYS.index(self._validate_day(day))]
        if isinstance(at, datetime):
            at = at.time()
        slots_per_hour = self._slots_per_hour()
        if isinstance(at, int) and not isinstance(at, bool):
            if not 0 <= at <= 23:
                raise ValueError(f"at must be an hour in the range 0-23, got {at}")
            return row[at * slots_per_hour]
        if isinstance(at, time):
            return row[at.hour * slots_per_hour + at.minute * slots_per_hour // 60]
        raise ValueError(
            f"at must be an int hour, a time, or a datetime, got {type(at).__name__}"
        )

    def spans(self, day: ProfileDay | int) -> list[ProfileSpan]:
        """Return ``day``'s schedule as runs of consecutive equal levels.

        Each :class:`ProfileSpan` is a half-open ``[start, end)`` range; the
        last span's ``end`` is ``time(0)``, meaning "through midnight". For
        app-written data the boundaries fall on whole hours.

        Raises:
            ValueError: If ``day`` is not a row of this profile type.
        """
        row = self._rows[type(self).DAYS.index(self._validate_day(day))]
        result: list[ProfileSpan] = []
        run_start = 0
        for slot in range(1, len(row) + 1):
            if slot == len(row) or row[slot] != row[run_start]:
                result.append(
                    ProfileSpan(
                        start=self._slot_time(run_start),
                        end=self._slot_time(slot),
                        level=row[run_start],
                    )
                )
                run_start = slot
        return result

    # endregion

    # region Editing

    def with_level(
        self,
        level: int,
        *,
        days: ProfileDay | int | Iterable[ProfileDay | int] | None = None,
        start: time | int = 0,
        end: time | int | None = None,
    ) -> Self:
        """Return a copy with ``[start, end)`` on ``days`` set to ``level``.

        The original profile is not modified. The full week is always kept
        (and later sent to the server) — this method only chooses which
        cells of the copy get the new level.

        Args:
            level: The level to set (must be in :attr:`LEVELS`).
            days: The rows to change: a single :class:`ProfileDay` (or its
                integer value), an iterable of them, or ``None`` (the
                default) for **every** row of this profile type — on thermo
                profiles that includes :attr:`ProfileDay.JOLLY`; pass
                :data:`WEEKDAYS` to target Monday..Sunday only.
            start: Start hour, inclusive: an ``int`` (0-23) or a whole-hour
                :class:`datetime.time`. Defaults to ``0`` (midnight).
            end: End hour, exclusive: an ``int`` (1-24), a whole-hour
                :class:`datetime.time` (``time(0)`` means end of day), or
                ``None`` (the default) for end of day. Edits are hour-based,
                so ``start``/``end`` must be whole hours (no rounding is
                applied) and spans cannot cross midnight — split such an
                edit into two calls.

        Raises:
            ValueError: If ``level``, ``days``, ``start``, or ``end`` are
                invalid, or if ``start >= end``.
        """
        self._validate_level(level)
        day_list = self._normalize_days(days)
        start_hour = self._normalize_hour(start, name="start")
        if end is None or (isinstance(end, time) and end == time(0)):
            end_hour = 24
        else:
            end_hour = self._normalize_hour(end, name="end", maximum=24)
        if start_hour >= end_hour:
            raise ValueError(
                f"start must be before end, got start={start_hour} and end={end_hour}"
            )

        slots_per_hour = self._slots_per_hour()
        rows = [list(row) for row in self._rows]
        for day in day_list:
            row = rows[type(self).DAYS.index(day)]
            for slot in range(start_hour * slots_per_hour, end_hour * slots_per_hour):
                row[slot] = level
        return type(self)(rows)

    def with_day_copied(
        self,
        source: ProfileDay | int,
        to: ProfileDay | int | Iterable[ProfileDay | int],
    ) -> Self:
        """Return a copy with ``source``'s whole row copied over ``to``.

        The "copy this day to other days" operation. Rows are copied at wire
        resolution, so the copy is lossless. The original profile is not
        modified.

        Args:
            source: The row to copy from.
            to: The row(s) to copy onto: a single :class:`ProfileDay` (or
                its integer value) or an iterable of them.

        Raises:
            ValueError: If ``source`` or any target is not a row of this
                profile type.
        """
        cls = type(self)
        source_row = self._rows[cls.DAYS.index(self._validate_day(source))]
        rows = list(self._rows)
        for day in self._normalize_days(to):
            rows[cls.DAYS.index(day)] = source_row
        return cls(rows)

    # endregion

    # region Dunders

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self._rows == other._rows

    def __hash__(self) -> int:
        return hash((type(self), self._rows))

    def __repr__(self) -> str:
        return f"{type(self).__name__}.from_wire({self.to_wire()!r})"

    # endregion

    # region Internal helpers

    @classmethod
    def _slots_per_hour(cls) -> int:
        return cls.WIRE_SLOTS_PER_DAY // 24

    @classmethod
    def _validate_level(cls, level: int) -> None:
        if not isinstance(level, int) or isinstance(level, bool):
            raise ValueError(f"level must be an int, got {type(level).__name__}")
        if level not in cls.LEVELS:
            raise ValueError(f"level must be one of {sorted(cls.LEVELS)}, got {level}")

    @classmethod
    def _validate_day(cls, day: ProfileDay | int) -> ProfileDay:
        if isinstance(day, bool) or not isinstance(day, int):
            raise ValueError(
                f"day must be a ProfileDay or an int, got {type(day).__name__}"
            )
        try:
            profile_day = ProfileDay(day)
        except ValueError as err:
            raise ValueError(f"{day} is not a valid ProfileDay value") from err
        if profile_day not in cls.DAYS:
            raise ValueError(
                f"{profile_day.name} is not a valid day for {cls.__name__}"
            )
        return profile_day

    @classmethod
    def _normalize_days(
        cls, days: ProfileDay | int | Iterable[ProfileDay | int] | None
    ) -> list[ProfileDay]:
        if days is None:
            return list(cls.DAYS)
        if isinstance(days, int) and not isinstance(days, bool):
            return [cls._validate_day(days)]
        if isinstance(days, Iterable) and not isinstance(days, (str, bytes)):
            return [cls._validate_day(day) for day in days]
        raise ValueError(
            "days must be a ProfileDay, an int, an iterable of them, or "
            f"None, got {type(days).__name__}"
        )

    @classmethod
    def _normalize_hour(cls, value: time | int, *, name: str, maximum: int = 23) -> int:
        if isinstance(value, time):
            if value.minute or value.second or value.microsecond:
                raise ValueError(
                    f"{name} must be a whole hour (edits are hour-based), got {value!r}"
                )
            hour = value.hour
        elif isinstance(value, int) and not isinstance(value, bool):
            hour = value
        else:
            raise ValueError(
                f"{name} must be an int hour or a datetime.time, "
                f"got {type(value).__name__}"
            )
        if not 0 <= hour <= maximum:
            raise ValueError(f"{name} must be in the range 0-{maximum}, got {hour}")
        return hour

    def _slot_time(self, slot: int) -> time:
        """Convert a wire slot index to its start time (end-of-day → time(0))."""
        if slot == self.WIRE_SLOTS_PER_DAY:
            return time(0)
        minutes = slot * 24 * 60 // self.WIRE_SLOTS_PER_DAY
        return time(hour=minutes // 60, minute=minutes % 60)

    # endregion


class LoadsCtrlProfile(WeeklyProfile):
    """Weekly hourly threshold profile of a loads controller.

    7 rows (Monday..Sunday) of 24 hourly slots; each level ``1``-``5``
    selects the power threshold active in that hour as a fraction of the
    controller's ``max_power`` (the five levels shown in the official app).

    Used by :attr:`LoadsCtrlMeter.profile` and accepted by
    :meth:`LoadsCtrlMeter.async_set_config`.
    """

    DAYS = WEEKDAYS
    WIRE_SLOTS_PER_DAY = 24


class ThermoProfile(WeeklyProfile):
    """Weekly setpoint-level profile of a thermo zone.

    8 rows — Monday..Sunday plus :attr:`ProfileDay.JOLLY` as the 8th row —
    of 96 quarter-hour wire slots; each level ``1``-``5`` selects one of the
    five setpoint levels shown in the official app. The app edits thermo
    profiles per hour, so this class exposes hours only (see
    :class:`WeeklyProfile`).

    Currently a read/edit value type only: the thermo profile set command
    has never been observed in captured traffic, so writing a profile back
    to a zone is not yet supported by the library.
    """

    DAYS = WEEKDAYS + (ProfileDay.JOLLY,)
    WIRE_SLOTS_PER_DAY = 96
