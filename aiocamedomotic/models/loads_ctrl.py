# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
CAME Domotic loads control entity models and control functionality.

This module implements the classes for working with the load-shedding system
exposed via the ``loadsctrl`` feature. The domain has two entity kinds:

- :class:`LoadsCtrlMeter` — the loads **controller**: binds an energy meter
  to an overload threshold (``max_power``), a hysteresis, and a weekly
  hourly threshold profile.
- :class:`LoadsCtrlRelay` — a **managed load**: an appliance the controller
  can *detach* (shed) when consumption exceeds the threshold, in priority
  order. **Lower priority value = detached first.**

The number of controllers and loads, and their names, are entirely
plant-specific configuration: every list may be empty, and nothing should be
assumed about specific appliances — always discover them from the server.

Protocol notes (from real captured traffic, ETI/Domo swver 3.0.1):

- The set commands (``loadsctrl_relay_set_req``, ``loadsctrl_meter_set_req``)
  are acknowledged with a bare ``{"cseq": ..., "sl_data_ack_reason": 0}``
  containing **no** ``cmd_name``, so no response-command matching is
  possible for them.
- Every accepted set is followed by a ``loadsctrl_relay_ind`` /
  ``loadsctrl_meter_ind`` push on the status-update channel, delivered to
  **all** clients including the one that issued the set.
- Set commands always carry the full field set (the official client echoes
  the untouched values): ``id`` + ``enabled`` + ``priority`` for relays,
  ``id`` + ``max_power`` + ``hysteresis`` + ``profile_data`` for meters.
"""

from __future__ import annotations

from collections.abc import Sequence
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
from .profiles import LoadsCtrlProfile


class LoadsCtrlRelayStatus(Enum):
    """Current output state of a load-control relay.

    Allowed values are:
        - OFF (0)
        - ON (1)
        - UNKNOWN (-1): Returned when the server reports an unrecognised
          status value.

    The relay output state is read-only: the loadsctrl commands cannot
    switch the relay on or off directly.
    """

    OFF = 0
    ON = 1
    UNKNOWN = -1


@dataclass
class LoadsCtrlRelay(CameEntity):
    """A load managed by a loads controller (``loadsctrl`` feature).

    Represents an appliance that the loads controller can *detach* (shed)
    when consumption exceeds the configured threshold. Loads are shed in
    priority order: **lower priority value = detached first**.

    Writable properties are changed via :meth:`async_set_enabled` and
    :meth:`async_set_priority`.

    Raises:
        ValueError: If ``name`` or ``id`` keys are missing from the input
            data, if ``id`` is not an integer, or if the auth argument is
            not an instance of the expected ``Auth`` class.
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
        """Load identifier.

        This is the key used by ``loadsctrl_relay_set_req`` and carried by
        ``loadsctrl_relay_ind`` push updates (not :attr:`act_id`).
        """
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Appliance name (user-defined, plant-specific)."""
        return self.raw_data["name"]

    @property
    def act_id(self) -> int:
        """Underlying actuator ID.

        Not used by any loadsctrl command: all loadsctrl operations are
        keyed by :attr:`id`.
        """
        return self.raw_data.get("act_id", 0)

    @property
    def priority(self) -> int:
        """Detach-order priority (raw server value).

        **Lower value = detached first.** The absolute numbering is a
        plant-specific convention.
        """
        return self.raw_data.get("priority", 0)

    @property
    def enabled(self) -> bool:
        """Whether the load participates in load shedding.

        This is the per-appliance on/off toggle shown in the official app.
        """
        return bool(self.raw_data.get("enabled", 0))

    @property
    def detached(self) -> bool:
        """Whether the controller has currently shed this load."""
        return bool(self.raw_data.get("detached", 0))

    @property
    def status(self) -> LoadsCtrlRelayStatus:
        """Current relay output state (read-only)."""
        try:
            return LoadsCtrlRelayStatus(self.raw_data["status"])
        except (ValueError, KeyError):
            LOGGER.warning(
                "Unknown loadsctrl relay status '%s' encountered for load '%s' "
                "(ID: %s). Returning LoadsCtrlRelayStatus.UNKNOWN. Please report "
                "this to the library developers.",
                self.raw_data.get("status"),
                self.name,
                self.id,
            )
            return LoadsCtrlRelayStatus.UNKNOWN

    @property
    def loadtype(self) -> int:
        """Raw ``loadtype`` field (opaque; ``1`` observed, semantics unknown)."""
        return self.raw_data.get("loadtype", 0)

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable this load's participation in load shedding.

        This is the equivalent of the per-appliance toggle in the official
        app. The wire command requires both fields, so the **current**
        :attr:`priority` is re-sent alongside the new ``enabled`` flag.

        Args:
            enabled: ``True`` to let the controller shed this load on
                overload, ``False`` to exclude it from load shedding.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug(
            "Sending 'loadsctrl_relay_set_req' command to the API (enabled=%s).",
            enabled,
        )

        # The ack carries no cmd_name, so no response_command is passed.
        payload = {
            "cmd_name": _CommandName.LOADSCTRL_RELAY_SET.value,
            "id": self.id,
            "enabled": 1 if enabled else 0,
            "priority": self.priority,
        }
        await self.auth.async_send_command(payload)

        # Update the status of the load if everything went as expected
        self.raw_data["enabled"] = 1 if enabled else 0

        LOGGER.info(
            "Load '%s' (ID: %s) %s",
            self.name,
            self.id,
            "enabled" if enabled else "disabled",
        )

    async def async_set_priority(self, priority: int) -> None:
        """Set the detach-order priority (raw server value).

        **Lower priority value = detached first.** The wire command requires
        both fields, so the **current** :attr:`enabled` flag is re-sent
        alongside the new priority.

        Args:
            priority: The new priority value (non-negative integer). The
                absolute numbering convention is plant-specific; the usual
                pattern is to swap/reuse the values already present on the
                plant (see
                :meth:`LoadsCtrlMeter.async_set_detach_order`).

        Raises:
            ValueError: If ``priority`` is not a non-negative integer.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError(f"priority must be an int, got {type(priority).__name__}")
        if priority < 0:
            raise ValueError(f"priority must be >= 0, got {priority}")

        LOGGER.debug(
            "Sending 'loadsctrl_relay_set_req' command to the API (priority=%d).",
            priority,
        )

        # The ack carries no cmd_name, so no response_command is passed.
        payload = {
            "cmd_name": _CommandName.LOADSCTRL_RELAY_SET.value,
            "id": self.id,
            "enabled": 1 if self.enabled else 0,
            "priority": priority,
        }
        await self.auth.async_send_command(payload)

        # Update the priority of the load if everything went as expected
        self.raw_data["priority"] = priority

        LOGGER.info(
            "Load '%s' (ID: %s) priority set to %d",
            self.name,
            self.id,
            priority,
        )


@dataclass
class LoadsCtrlMeter(CameEntity):
    """The loads controller bound to an energy meter (``loadsctrl`` feature).

    Binds an energy meter (:attr:`meter_id`) to an overload threshold
    (:attr:`max_power`), a hysteresis, and a weekly hourly threshold profile
    (:attr:`profile_data`). When consumption exceeds the threshold, the
    controller detaches its managed loads (fetched via
    :meth:`async_get_relays`) in priority order — lower priority value
    first.

    A plant may define any number of controllers (including zero); code
    should never assume a single controller.

    Raises:
        ValueError: If ``name`` or ``id`` keys are missing from the input
            data, if ``id`` is not an integer, or if the auth argument is
            not an instance of the expected ``Auth`` class.
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
        """Loads-controller identifier (opaque server value).

        Required by ``loadsctrl_relay_list_req``; do not confuse it with
        the bound energy meter's :attr:`meter_id`.
        """
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Controller name (mirrors the bound energy meter's name)."""
        return self.raw_data["name"]

    @property
    def meter_id(self) -> int:
        """The ``id`` of the associated energy meter (from the meters list)."""
        return self.raw_data.get("meter_id", 0)

    @property
    def power(self) -> float:
        """Current power reading in Watts (same as the meter's power).

        The value is passed through exactly as reported by the server
        (no unit conversion is applied).
        """
        return self.raw_data.get("power", 0)

    @property
    def max_power(self) -> int:
        """Overload threshold in Watts."""
        return self.raw_data.get("max_power", 0)

    @property
    def hysteresis(self) -> int:
        """Hysteresis around the overload threshold, in Watts."""
        return self.raw_data.get("hysteresis", 0)

    @property
    def profile_data(self) -> list[str]:
        """Weekly hourly threshold profile (raw wire format, copied).

        Seven strings — one per weekday, Monday first — of 24 characters
        each (one per hour of day). Each character is a digit ``1``-``5``
        selecting the power threshold active in that hour as a fraction of
        :attr:`max_power`. For a typed view use :attr:`profile`.

        Returns a copy: mutating the returned list does not affect
        ``raw_data``.
        """
        return list(self.raw_data.get("profile_data", []))

    @property
    def profile(self) -> LoadsCtrlProfile:
        """Weekly hourly threshold profile (typed view).

        Parsed fresh from ``raw_data`` on every access (never cached), so
        it always reflects the latest known server state. Edit it with the
        :class:`LoadsCtrlProfile` methods and write it back via
        :meth:`async_set_config`.

        Raises:
            ValueError: If ``raw_data`` lacks a well-formed
                ``profile_data`` value.
        """
        return LoadsCtrlProfile.from_wire(self.raw_data.get("profile_data", []))

    async def async_get_relays(self) -> list[LoadsCtrlRelay]:
        """Get the loads managed by this controller.

        Sends ``loadsctrl_relay_list_req`` with this controller's
        :attr:`id`. Relays are returned in server order; sort by
        :attr:`LoadsCtrlRelay.priority` (ascending) to get the detach-order
        view shown by the official app.

        Returns:
            list[LoadsCtrlRelay]: List of managed loads. Returns an empty
            list if none are defined or the server response lacks the
            ``array`` key.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching loadsctrl relays list for controller ID %s", self.id)
        payload = {
            "cmd_name": _CommandName.LOADSCTRL_RELAY_LIST.value,
            "id": self.id,
        }

        json_response = await self.auth.async_send_command(
            payload,
            response_command=_CommandNameResponse.LOADSCTRL_RELAY_LIST.value,
        )

        # Defaults to an empty list if the key is missing from the response JSON
        relays_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d loadsctrl relay(s)", len(relays_list))
        return [LoadsCtrlRelay(relay_data, self.auth) for relay_data in relays_list]

    async def async_set_config(
        self,
        *,
        max_power: int | None = None,
        hysteresis: int | None = None,
        profile_data: LoadsCtrlProfile | None = None,
    ) -> None:
        """Update the controller configuration.

        Sends ``loadsctrl_meter_set_req``. The wire command requires the
        full triple, so any unspecified argument is re-sent with its
        current value from ``raw_data``.

        Args:
            max_power: New overload threshold in Watts (positive integer),
                or ``None`` to keep the current value.
            hysteresis: New hysteresis in Watts (non-negative integer; ``0``
                disables the hysteresis band), or ``None`` to keep the
                current value.
            profile_data: New weekly hourly threshold profile as a
                :class:`LoadsCtrlProfile` (typically obtained from
                :attr:`profile` and edited), or ``None`` to keep the
                current value.

        Raises:
            ValueError: If ``max_power`` is not a positive integer, if
                ``hysteresis`` is not a non-negative integer, or if
                ``profile_data`` is not a ``LoadsCtrlProfile``.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if max_power is not None and (
            not isinstance(max_power, int)
            or isinstance(max_power, bool)
            or max_power <= 0
        ):
            raise ValueError(f"max_power must be a positive int, got {max_power!r}")
        if hysteresis is not None and (
            not isinstance(hysteresis, int)
            or isinstance(hysteresis, bool)
            or hysteresis < 0
        ):
            raise ValueError(
                f"hysteresis must be a non-negative int, got {hysteresis!r}"
            )
        if profile_data is not None and not isinstance(profile_data, LoadsCtrlProfile):
            raise ValueError(
                "profile_data must be a LoadsCtrlProfile, "
                f"got {type(profile_data).__name__}"
            )

        # The wire command requires the full triple: source untouched
        # values from raw_data.
        new_max_power = max_power if max_power is not None else self.max_power
        new_hysteresis = hysteresis if hysteresis is not None else self.hysteresis
        new_profile = (
            profile_data.to_wire() if profile_data is not None else self.profile_data
        )

        LOGGER.debug(
            "Sending 'loadsctrl_meter_set_req' command to the API "
            "(max_power=%d, hysteresis=%d).",
            new_max_power,
            new_hysteresis,
        )

        # The ack carries no cmd_name, so no response_command is passed.
        payload = {
            "cmd_name": _CommandName.LOADSCTRL_METER_SET.value,
            "id": self.id,
            "max_power": new_max_power,
            "hysteresis": new_hysteresis,
            "profile_data": new_profile,
        }
        await self.auth.async_send_command(payload)

        # Update the configuration if everything went as expected
        self.raw_data["max_power"] = new_max_power
        self.raw_data["hysteresis"] = new_hysteresis
        self.raw_data["profile_data"] = new_profile

        LOGGER.info(
            "Loads controller '%s' (ID: %s) configuration updated "
            "(max_power=%d, hysteresis=%d)",
            self.name,
            self.id,
            new_max_power,
            new_hysteresis,
        )

    async def async_set_detach_order(self, relays: Sequence[LoadsCtrlRelay]) -> None:
        """Rewrite priorities so loads are shed in the given order.

        The first element of ``relays`` is shed first (**lower priority
        value = shed first**). The method fetches the controller's current
        relay list, takes the existing priority values, sorts them
        ascending, and reassigns them to ``relays`` in sequence order —
        sending one ``loadsctrl_relay_set_req`` per relay whose priority
        actually changes (the official app also writes only changed
        relays). Reusing the existing value set keeps whatever absolute
        numbering convention the plant uses intact.

        Each write is issued through a freshly-fetched relay object (not
        the caller-supplied one), so it carries the ``enabled`` flag as of
        this call's own relay-list fetch rather than whatever value the
        caller's object happened to have cached — otherwise a stale
        caller-side ``enabled`` would be silently written back over a
        concurrent change made by another client. The caller-supplied
        objects are updated with the resulting state afterward, so they
        remain a valid source for further calls.

        This method is not atomic: it issues one set command per changed
        relay, sequentially. If a call fails partway through, the plant can
        be left with two relays sharing the same priority value (the new
        value is written to one relay before the old value is cleared from
        the other). This is safe to recover from by simply calling the
        method again: duplicate priority values found on the plant are
        repaired into a strictly increasing sequence (each duplicate is
        bumped just above the value before it) before being reassigned, so
        a replay of the same request converges to the requested order. The
        same repair also applies to plants whose priorities contain
        duplicates for any other reason, in which case some relays end up
        with priority values not previously used on the plant; a warning
        is logged when this happens.

        Args:
            relays: The desired detach order. Must be a permutation of this
                controller's relays (same IDs, no duplicates) — fetch them
                via :meth:`async_get_relays` first.

        Raises:
            ValueError: If ``relays`` is not a permutation of this
                controller's relays (same IDs, no duplicates).
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        current_relays = await self.async_get_relays()
        current_by_id = {relay.id: relay for relay in current_relays}

        requested_ids = [relay.id for relay in relays]
        if len(set(requested_ids)) != len(requested_ids) or set(requested_ids) != set(
            current_by_id
        ):
            raise ValueError(
                "relays must be a permutation of this controller's relays "
                "(same IDs, no duplicates); fetch them via async_get_relays() first"
            )

        # Duplicate priority values (e.g. left behind by a previous call
        # of this method that failed partway through) cannot express a
        # full detach order: repair them into a strictly increasing
        # sequence so the request is always applicable.
        current_priorities = sorted(relay.priority for relay in current_relays)
        priorities = list(current_priorities)
        for index in range(1, len(priorities)):
            if priorities[index] <= priorities[index - 1]:
                priorities[index] = priorities[index - 1] + 1
        if priorities != current_priorities:
            LOGGER.warning(
                "Loads controller '%s' (ID: %s) reports duplicate relay "
                "priority values; repairing them to %s to apply the "
                "requested detach order.",
                self.name,
                self.id,
                priorities,
            )

        changed = 0
        for relay, new_priority in zip(relays, priorities, strict=True):
            fresh_relay = current_by_id[relay.id]
            if fresh_relay.priority != new_priority:
                await fresh_relay.async_set_priority(new_priority)
                relay.raw_data.update(fresh_relay.raw_data)
                changed += 1

        LOGGER.info(
            "Loads controller '%s' (ID: %s) detach order updated (%d relay(s) written)",
            self.name,
            self.id,
            changed,
        )
