# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic sound zone entity models and control functionality.

This module implements the classes for working with audio (sound) zones in a
CAME Domotic system. A sound zone is an audio output room that can be powered
on/off (standby), muted, adjusted in volume within a server-provided range,
and switched between the available input sources.

.. note::
    Sound zone support is **not verified against a live plant**. The data model and
    commands are implemented from the behaviour of an existing, field-tested
    third-party integration. Depending on the firmware, the available sources
    are reported either as a ``sources`` array or as flat ``source_N`` /
    ``id_source_N`` fields; both formats are normalized by :attr:`SoundZone.sources`.
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

# Values of the "standby" and "mute" flags in the sound zone data.
_SOUND_STANDBY_ON = 1
_SOUND_MUTE_ON = 1

# Highest index scanned for the flat "source_N" fields format.
_MAX_FLAT_SOURCES = 31

# Keys of the server envelope that must not leak into the zone raw_data
# when refreshing from a sound_room_src_resp payload.
_PROTOCOL_KEYS = ("cmd_name", "cseq", "sl_data_ack_reason")


class SoundZoneAction(Enum):
    """Actions accepted by the ``sound_switch_req`` command.

    Values:
        - STANDBY ("standby"): power the zone on/off
        - MUTE ("mute"): mute/unmute the zone
        - VOLUME ("volume"): set the raw volume value
        - SOURCE ("source"): select an input source by ID
    """

    STANDBY = "standby"
    MUTE = "mute"
    VOLUME = "volume"
    SOURCE = "source"


@dataclass
class SoundZone(CameEntity):
    """Sound zone entity in the CameDomotic API.

    Represents a single audio zone. Zones are keyed on their ``id`` (not
    ``act_id``). They can be powered on/off, muted, adjusted in volume, and
    switched between the available input sources.

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
        """Unique sound zone identifier."""
        return self.raw_data["id"]

    @property
    def name(self) -> str | None:
        """Display name of the zone, or ``None`` if the server omits it."""
        return self.raw_data.get("name")

    @property
    def is_on(self) -> bool:
        """Whether the zone is powered on (i.e. not in standby)."""
        return self.raw_data.get("standby") != _SOUND_STANDBY_ON

    @property
    def is_muted(self) -> bool:
        """Whether the zone is muted."""
        return self.raw_data.get("mute") == _SOUND_MUTE_ON

    @property
    def volume(self) -> int | None:
        """Raw volume value reported by the server, or ``None`` if absent."""
        return self.raw_data.get("volume")

    @property
    def min_volume(self) -> int | None:
        """Lower bound of the raw volume range, or ``None`` if absent."""
        return self.raw_data.get("min_volume")

    @property
    def max_volume(self) -> int | None:
        """Upper bound of the raw volume range, or ``None`` if absent."""
        return self.raw_data.get("max_volume")

    @property
    def volume_level(self) -> float | None:
        """Volume normalized to the 0.0–1.0 range.

        Returns ``None`` when the raw volume or its range is unknown, and
        ``0.0`` when the server reports an empty range
        (``max_volume == min_volume``). Values are clamped to 0.0–1.0.
        """
        volume = self.volume
        min_volume = self.min_volume
        max_volume = self.max_volume
        if volume is None or min_volume is None or max_volume is None:
            return None
        if max_volume == min_volume:
            return 0.0
        return max(0.0, min(1.0, (volume - min_volume) / (max_volume - min_volume)))

    @property
    def source(self) -> str | None:
        """Name of the currently selected source, or ``None`` if unknown."""
        return self.raw_data.get("source_name") or self.raw_data.get("source")

    @property
    def sources(self) -> list[dict[str, Any]]:
        """Available input sources, normalized to ``{"name", "id"}`` dicts.

        Depending on the firmware, the server reports sources either as a
        ``sources`` array (items carrying ``source`` or ``source_name`` plus
        ``id``) or as flat ``source_N`` fields with an optional
        ``id_source_N`` companion (defaulting to ``N - 1``). Both formats are
        merged and deduplicated by ``(name, id)``.
        """
        sources: list[dict[str, Any]] = []
        for src in self.raw_data.get("sources") or []:
            name = src.get("source") or src.get("source_name")
            sources.append({"name": name, "id": src.get("id")})

        for index in range(1, _MAX_FLAT_SOURCES + 1):
            name = self.raw_data.get(f"source_{index}")
            if name is None:
                continue
            sources.append(
                {
                    "name": name,
                    "id": self.raw_data.get(f"id_source_{index}", index - 1),
                }
            )

        deduped: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any]] = set()
        for src in sources:
            key = (src["name"], src["id"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(src)
        return deduped

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    async def _async_switch(self, action: SoundZoneAction, value: int) -> None:
        """Send a ``sound_switch_req`` command for this zone.

        The server replies with a generic acknowledgement (no dedicated
        response command), so only the standard ack is validated.
        """
        LOGGER.debug(
            "Sending cmd 'sound_switch_req' for zone '%s' (ID: %s), "
            "action=%s, value=%s.",
            self.name,
            self.id,
            action.value,
            value,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.SOUND_SWITCH.value,
                "id": self.id,
                "action": action.value,
                "value": value,
            }
        )

    async def async_turn_on(self) -> None:
        """Power on the zone (leave standby).

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self._async_switch(SoundZoneAction.STANDBY, 0)
        self.raw_data["standby"] = 0
        LOGGER.info("Sound zone '%s' (ID: %s) turned on.", self.name, self.id)

    async def async_turn_off(self) -> None:
        """Put the zone in standby.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        await self._async_switch(SoundZoneAction.STANDBY, _SOUND_STANDBY_ON)
        self.raw_data["standby"] = _SOUND_STANDBY_ON
        LOGGER.info("Sound zone '%s' (ID: %s) turned off.", self.name, self.id)

    async def async_set_mute(self, muted: bool) -> None:
        """Mute or unmute the zone.

        Args:
            muted: ``True`` to mute the zone, ``False`` to unmute it.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        value = _SOUND_MUTE_ON if muted else 0
        await self._async_switch(SoundZoneAction.MUTE, value)
        self.raw_data["mute"] = value
        LOGGER.info(
            "Sound zone '%s' (ID: %s) %s.",
            self.name,
            self.id,
            "muted" if muted else "unmuted",
        )

    async def async_set_volume_level(self, volume_level: float) -> None:
        """Set the zone volume from a normalized 0.0–1.0 level.

        The level is denormalized onto the server-provided
        ``min_volume``/``max_volume`` range and rounded to the nearest raw
        value.

        Args:
            volume_level: Desired volume in the 0.0–1.0 range.

        Raises:
            ValueError: If ``volume_level`` is outside the 0.0–1.0 range, or
                the zone does not report its volume range.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not 0.0 <= volume_level <= 1.0:
            raise ValueError(
                f"volume_level must be between 0.0 and 1.0, got {volume_level}"
            )
        min_volume = self.min_volume
        max_volume = self.max_volume
        if min_volume is None or max_volume is None:
            raise ValueError(
                "Cannot set the volume: the zone does not report its "
                "min_volume/max_volume range"
            )
        value = round(min_volume + (max_volume - min_volume) * volume_level)
        await self._async_switch(SoundZoneAction.VOLUME, value)
        self.raw_data["volume"] = value
        LOGGER.info(
            "Sound zone '%s' (ID: %s) volume set to %s.", self.name, self.id, value
        )

    async def async_select_source(self, source_name: str) -> None:
        """Select an input source by name.

        The name is matched against the normalized :attr:`sources` list and
        the corresponding source ID is sent to the server.

        Args:
            source_name: Name of the source to select, as reported in
                :attr:`sources`.

        Raises:
            ValueError: If no source with the given name (and a valid ID) is
                available on this zone.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        for src in self.sources:
            source_id = src["id"]
            if src["name"] == source_name and source_id is not None:
                await self._async_switch(SoundZoneAction.SOURCE, source_id)
                self.raw_data["source_name"] = source_name
                self.raw_data["source_id"] = source_id
                LOGGER.info(
                    "Sound zone '%s' (ID: %s) switched to source '%s'.",
                    self.name,
                    self.id,
                    source_name,
                )
                return
        raise ValueError(
            f"Source '{source_name}' is not available on sound zone "
            f"'{self.name}' (ID: {self.id})"
        )

    async def async_send_source_command(self, source_id: int, action: str) -> None:
        """Send an advanced command to an audio source (``suftif_cmd_req``).

        This is a low-level primitive: the set of supported actions depends on
        the source device (e.g. tuner or media player transport commands) and
        is passed through to the server unchanged.

        Args:
            source_id: ID of the target source, as reported in :attr:`sources`.
            action: Action string understood by the source device.

        The server replies with a generic acknowledgement (no dedicated
        response command), so only the standard ack is validated.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending cmd 'suftif_cmd_req' for source ID %s, action=%s.",
            source_id,
            action,
        )
        await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.SUFTIF_CMD.value,
                "id": source_id,
                "action": action,
            }
        )
        LOGGER.info("Source ID %s sent action '%s'.", source_id, action)

    async def async_refresh(self) -> None:
        """Refresh this zone's state from the server (``sound_room_src_req``).

        Fetches the current state of this single zone and merges it into
        :attr:`raw_data`. The update is applied only if the response refers to
        this zone's ID.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Refreshing sound zone '%s' (ID: %s) state.", self.name, self.id)
        response = await self.auth.async_send_command(
            {
                "cmd_name": _CommandName.SOUND_ROOM_SRC.value,
                "value": self.id,
            },
            response_command=_CommandNameResponse.SOUND_ROOM_SRC.value,
        )
        if response.get("id") != self.id:
            LOGGER.warning(
                "Ignoring sound zone refresh for ID %s: response refers to ID %s.",
                self.id,
                response.get("id"),
            )
            return
        self.raw_data.update(
            {k: v for k, v in response.items() if k not in _PROTOCOL_KEYS}
        )
        LOGGER.info("Sound zone '%s' (ID: %s) state refreshed.", self.name, self.id)
