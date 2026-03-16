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
This module exposes the CAME Domotic API to the end-users.
"""

from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any

import aiohttp

from .auth import Auth
from .const import (
    _DEFAULT_COMMAND_TIMEOUT,
    _FEATURE_TO_NESTED_CMD,
    _NESTED_3LEVEL_FEATURES,
    _CommandName,
    _CommandNameResponse,
    _CommandType,
    _ServerFeature,
    _TopologicScope,
)
from .errors import CameDomoticAuthError
from .models import (
    AnalogSensor,
    AnalogSensorType,
    Camera,
    DigitalInput,
    Floor,
    Light,
    Opening,
    PlantTopology,
    Relay,
    Room,
    Scenario,
    ServerInfo,
    TerminalGroup,
    ThermoZone,
    ThermoZoneSeason,
    TopologyFloor,
    TopologyRoom,
    UpdateList,
    User,
)
from .utils import LOGGER


class CameDomoticAPI:
    """Main class, exposes all the public methods of the CAME Domotic API."""

    def __init__(self, auth: Auth, *, command_timeout: int = _DEFAULT_COMMAND_TIMEOUT):
        """Initialize the CAME Domotic API object.

        Args:
            auth (Auth): the authentication object used to interact with
                the CAME Domotic API.
            command_timeout (int, optional): the default timeout in seconds
                for all commands sent to the server (default: 30s). This
                applies to all methods unless overridden per-call (e.g. via
                the ``timeout`` parameter in ``async_get_updates``).
        """
        self.auth = auth
        self.auth.command_timeout = command_timeout
        LOGGER.debug(
            "CameDomoticAPI initialized (command_timeout=%ds)", command_timeout
        )

    async def __aenter__(self) -> CameDomoticAPI:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.async_dispose()

    async def async_dispose(self) -> None:
        """Dispose the CameDomoticAPI object."""
        LOGGER.debug("Disposing CameDomoticAPI")
        try:
            await self.auth.async_dispose()
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Error while disposing the CameDomoticAPI object")

    async def async_get_users(self) -> list[User]:
        """Get the list of users defined on the server.

        Returns:
            list[User]: List of users. Returns an empty list if no users are defined
            or if the server response doesn't contain the users list.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching users list")
        json_response = await self.auth.async_send_command(
            {}, command_type=_CommandType.USERS_LIST_REQUEST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        users_list = json_response.get("sl_users_list", [])
        LOGGER.info("Retrieved %d user(s)", len(users_list))
        return [User(user, self.auth) for user in users_list]

    async def async_get_terminal_groups(self) -> list[TerminalGroup]:
        """Get the list of terminal groups defined on the server.

        Terminal groups define the permission scope assigned to users at
        creation time. Call this method before :meth:`async_add_user` to
        discover the available group names on the server.

        The ``group`` parameter of :meth:`async_add_user` accepts a group
        **name** (e.g. ``"ETI/Domo"``), not its numeric ID. The special value
        ``"*"`` (the default) may be used when fine-grained group assignment is
        not required.

        Returns:
            list[TerminalGroup]: Available groups. Returns an empty list if
            none are defined or the server response lacks the ``array`` key.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching terminal groups list")
        json_response = await self.auth.async_send_command(
            {"cmd_name": _CommandName.TERMINALS_GROUPS_LIST.value},
            response_command=_CommandNameResponse.TERMINALS_GROUPS_LIST.value,
        )
        groups = json_response.get("array", [])
        LOGGER.info("Retrieved %d terminal group(s)", len(groups))
        return [TerminalGroup(g) for g in groups]

    async def async_add_user(
        self, username: str, password: str, group: str = "*"
    ) -> User:
        """Add a new user to the CAME Domotic server.

        Args:
            username (str): The login name for the new user.
            password (str): The initial password for the new user.
            group (str, optional): The **name** of the permission group to
                assign to the new user (e.g. ``"ETI/Domo"``). Defaults to
                ``"*"``. Use :meth:`async_get_terminal_groups` to retrieve
                the available group names from the server.

        Returns:
            User: A ``User`` object representing the newly created user.

        .. warning::
            This operation is based on reverse-engineered API documentation and
            has not been verified against a real CAME Domotic server. Behaviour
            may differ across firmware versions.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Adding user '%s'", username)
        await self.auth.async_send_command(
            {},
            command_type=_CommandType.ADD_USER_REQUEST.value,
            additional_payload={
                "sl_login": username,
                "sl_pwd": password,
                "sl_group": group,
            },
        )
        LOGGER.info("User '%s' added", username)
        return User({"name": username}, self.auth)

    async def async_get_server_info(self) -> ServerInfo:
        """Get the server information.

        Provides info about the server (keycode, software version, etc.) and the list of
        features supported by the CAME Domotic server.

        Returns:
            ServerInfo: Server information.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching server info")
        payload = {
            "cmd_name": _CommandName.FEATURE_LIST.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.FEATURE_LIST.value
        )

        LOGGER.info(
            "Server info: keycode=%s, swver=%s, features=%s",
            json_response.get("keycode"),
            json_response.get("swver"),
            json_response.get("list"),
        )
        return ServerInfo(
            keycode=json_response.get("keycode"),  # type: ignore[arg-type]
            swver=json_response.get("swver"),
            type=json_response.get("type"),
            board=json_response.get("board"),
            serial=json_response.get("serial"),  # type: ignore[arg-type]
            features=json_response.get("list"),  # type: ignore[arg-type]
        )

    async def async_ping(self) -> float:
        """Ping the CAME Domotic server and measure round-trip latency.

        Sends a keep-alive request to verify connectivity. If the session has
        expired, it transparently re-authenticates first.

        Returns:
            float: Round-trip latency in milliseconds.

        Raises:
            CameDomoticServerNotFoundError: If the server is unreachable.
            CameDomoticAuthError: If authentication fails.
            CameDomoticServerTimeoutError: If the request times out.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Pinging server")
        start = time.monotonic()
        await self.auth.async_keep_alive()
        latency_ms = (time.monotonic() - start) * 1000
        LOGGER.info("Ping latency: %.1f ms", latency_ms)
        return latency_ms

    async def async_get_floors(self) -> list[Floor]:
        """Get the list of all the floors defined on the server.

        Returns:
            list[Floor]: List of floors.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching floors list")
        payload = {
            "cmd_name": _CommandName.FLOOR_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.FLOOR_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        floor_list = json_response.get("floor_list", [])
        LOGGER.info("Retrieved %d floor(s)", len(floor_list))
        return [Floor(floor) for floor in floor_list]

    async def async_get_rooms(self) -> list[Room]:
        """Get the list of all the rooms defined on the server.

        Returns:
            list[Room]: List of rooms.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching rooms list")
        payload = {
            "cmd_name": _CommandName.ROOM_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.ROOM_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        room_list = json_response.get("room_list", [])
        LOGGER.info("Retrieved %d room(s)", len(room_list))
        return [Room(room) for room in room_list]

    async def async_get_lights(self) -> list[Light]:
        """Get the list of all the light devices defined on the server.

        Returns:
            list[Light]: List of lights.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching lights list")
        payload = {
            "cmd_name": _CommandName.LIGHT_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.LIGHT_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        lights_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d light(s)", len(lights_list))
        return [Light(light_data, self.auth) for light_data in lights_list]

    async def async_get_thermo_zones(self) -> list[ThermoZone]:
        """Get the list of all thermoregulation zones defined on the server.

        Returns:
            list[ThermoZone]: List of thermoregulation zones.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching thermoregulation zones")
        payload = {
            "cmd_name": _CommandName.THERMO_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.THERMO_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        zones_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d thermo zone(s)", len(zones_list))
        return [ThermoZone(zone_data, self.auth) for zone_data in zones_list]

    async def async_get_analog_sensors(self) -> list[AnalogSensor]:
        """Get analog sensor readings from the thermoregulation system.

        Retrieves top-level temperature, humidity, and pressure sensor
        readings from the thermoregulation list response.

        Returns:
            list[AnalogSensor]: List of analog sensors found in the response.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching analog sensors")
        payload = {
            "cmd_name": _CommandName.THERMO_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.THERMO_LIST.value
        )

        sensors = []
        for key in ("temperature", "humidity", "pressure"):
            sensor_data = json_response.get(key)
            if sensor_data and isinstance(sensor_data, dict):
                try:
                    sensor_type = AnalogSensorType(key)
                except ValueError:
                    LOGGER.warning(
                        "Unknown analog sensor type '%s'. "
                        "Returning AnalogSensorType.UNKNOWN. "
                        "Please report this to the library developers.",
                        key,
                    )
                    sensor_type = AnalogSensorType.UNKNOWN
                sensors.append(AnalogSensor(sensor_data, sensor_type))
        LOGGER.info("Retrieved %d analog sensor(s)", len(sensors))
        return sensors

    async def async_set_thermo_season(self, season: ThermoZoneSeason) -> None:
        """Set the global thermoregulation season for all zones.

        This is a plant-level command that changes the season for the
        entire thermoregulation system.

        .. warning::
            Setting ``season`` to ``PLANT_OFF`` causes the CAME server to
            automatically switch **all** thermoregulation zones to
            ``ThermoZoneMode.OFF``. Reverting the season back to ``WINTER``
            or ``SUMMER`` does **not** restore the previous zone modes —
            each zone stays ``OFF`` until its mode is changed explicitly via
            :meth:`~aiocamedomotic.models.ThermoZone.async_set_mode` or
            :meth:`~aiocamedomotic.models.ThermoZone.async_set_config`.

        Args:
            season: The season to set. Valid values are ``WINTER``,
                ``SUMMER``, and ``PLANT_OFF``.

        Raises:
            ValueError: If ``season`` is ``ThermoZoneSeason.UNKNOWN``.
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        if season == ThermoZoneSeason.UNKNOWN:
            raise ValueError("Cannot set season to UNKNOWN")

        LOGGER.debug("Setting global thermo season to '%s'", season.value)
        payload = {
            "cmd_name": _CommandName.THERMO_SEASON.value,
            "season": season.value,
        }
        await self.auth.async_send_command(payload)
        LOGGER.info("Global thermo season set to '%s'", season.value)

    async def async_get_updates(self, timeout: int | None = None) -> UpdateList:
        """Get status updates from the server using long polling.

        This method performs a long-polling request: it blocks until the server
        sends one or more real-time status updates (e.g., a light turned on, a
        scenario activated), then returns them all at once.

        Args:
            timeout (int | None, optional): the timeout in seconds for the
                long-polling request. If None, uses the instance-level
                ``command_timeout`` (default: 30s). Since this method uses
                long polling, a longer timeout (e.g. 120s) is recommended
                to avoid premature disconnections.

        Returns:
            UpdateList: List of status updates received from the server.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        LOGGER.debug("Fetching status updates (timeout=%s)", timeout)
        payload = {
            "cmd_name": _CommandName.STATUS_UPDATE.value,
        }
        json_response = await self.auth.async_send_command(
            payload,
            response_command=_CommandNameResponse.STATUS_UPDATE.value,
            timeout=timeout,
        )
        updates = UpdateList((json_response or {}).get("result", []))
        LOGGER.info(
            "Received %d status update(s)%s",
            len(updates),
            " (includes plant update)" if updates.has_plant_update else "",
        )
        return updates

    async def async_get_digital_inputs(self) -> list[DigitalInput]:
        """Get the list of all digital input devices defined on the server.

        Digital inputs are read-only binary sensors (e.g. physical buttons,
        contact sensors). They report their state but cannot be controlled.

        Returns:
            list[DigitalInput]: List of digital inputs.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching digital inputs list")
        payload = {
            "cmd_name": _CommandName.DIGITALIN_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.DIGITALIN_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        digitalin_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d digital input(s)", len(digitalin_list))
        return [
            DigitalInput(digitalin_data, self.auth) for digitalin_data in digitalin_list
        ]

    async def async_get_cameras(self) -> list[Camera]:
        """Get the list of all TVCC cameras defined on the server.

        Cameras are read-only entities providing access to IP camera
        stream URIs. They do not support control commands.

        .. note::
            This method uses API commands documented in the CAME JS client
            but not yet verified against a real server. Behaviour may differ
            across firmware versions.

        Returns:
            list[Camera]: List of cameras.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching cameras list")
        payload = {
            "cmd_name": _CommandName.TVCC_CAMERAS_LIST.value,
            "username": self.auth.current_username,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.TVCC_CAMERAS_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        cameras_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d camera(s)", len(cameras_list))
        return [Camera(camera_data, self.auth) for camera_data in cameras_list]

    async def async_get_openings(self) -> list[Opening]:
        """Get the list of all opening devices defined on the server.

        Returns:
            list[Opening]: List of openings.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching openings list")
        payload = {
            "cmd_name": _CommandName.OPENINGS_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.OPENINGS_LIST.value
        )

        openings_data = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d opening(s)", len(openings_data))
        return [Opening(opening_data, self.auth) for opening_data in openings_data]

    async def async_get_relays(self) -> list[Relay]:
        """Get the list of all relay devices defined on the server.

        Relays are simple on/off switches that can be controlled remotely.

        .. note::
            This method uses API commands documented in the CAME API
            specification but not yet verified against a real server.
            Behaviour may differ across firmware versions.

        Returns:
            list[Relay]: List of relays.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching relays list")
        payload = {
            "cmd_name": _CommandName.RELAYS_LIST.value,
            "topologic_scope": _TopologicScope.PLANT.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.RELAYS_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        relays_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d relay(s)", len(relays_list))
        return [Relay(relay_data, self.auth) for relay_data in relays_list]

    async def async_get_scenarios(self) -> list[Scenario]:
        """Get the list of all scenarios defined on the server.

        Returns:
            list[Scenario]: List of scenarios.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching scenarios list")
        payload = {
            "cmd_name": _CommandName.SCENARIOS_LIST.value,
        }

        json_response = await self.auth.async_send_command(
            payload, response_command=_CommandNameResponse.SCENARIOS_LIST.value
        )

        # Defaults to an empty list if the key is missing from the response JSON
        scenarios_list = json_response.get("array", []) or []
        LOGGER.info("Retrieved %d scenario(s)", len(scenarios_list))
        return [Scenario(scenario_data, self.auth) for scenario_data in scenarios_list]

    async def async_get_topology(self) -> PlantTopology:
        """Get the complete plant topology (floors and rooms).

        Merges data from the standard ``floor_list_req`` / ``room_list_req``
        endpoints with the nested device list commands
        (``nested_light_list_req``, ``nested_openings_list_req``,
        ``nested_thermo_list_req``) to build a comprehensive topology even on
        servers where the flat floor/room endpoints return empty.

        Only nested commands for features supported by the server are sent.

        Returns:
            PlantTopology: The merged plant topology.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        LOGGER.debug("Fetching plant topology")

        nested_tasks = await self._build_nested_tasks()

        # Run flat endpoints and nested commands concurrently
        flat_coros: list[Any] = [self.async_get_floors(), self.async_get_rooms()]
        nested_coros = [coro for _, coro in nested_tasks]
        all_results = await asyncio.gather(
            *flat_coros, *nested_coros, return_exceptions=True
        )

        flat_floors_result = all_results[0]
        flat_rooms_result = all_results[1]
        nested_results = list(
            zip(
                [feat for feat, _ in nested_tasks],
                all_results[2:],
                strict=False,
            )
        )

        floors, rooms = self._parse_flat_results(flat_floors_result, flat_rooms_result)
        self._merge_nested_results(nested_results, floors, rooms)
        return self._build_plant_topology(floors, rooms)

    async def _build_nested_tasks(self) -> list[tuple[_ServerFeature, Any]]:
        """Fetch server info and return (feature, coro) pairs for nested cmds."""
        nested_tasks: list[tuple[_ServerFeature, Any]] = []
        try:
            server_info = await self.async_get_server_info()
        except CameDomoticAuthError:
            raise
        except Exception:  # noqa: BLE001
            LOGGER.warning(
                "Failed to fetch server info; skipping nested topology commands",
                exc_info=True,
            )
            return nested_tasks

        for feature_str in server_info.features:
            try:
                feature = _ServerFeature(feature_str)
            except ValueError:
                continue
            if feature in _FEATURE_TO_NESTED_CMD:
                cmd_name, resp_cmd = _FEATURE_TO_NESTED_CMD[feature]
                coro = self.auth.async_send_command(
                    {"cmd_name": cmd_name},
                    response_command=resp_cmd,
                )
                nested_tasks.append((feature, coro))

        return nested_tasks

    @staticmethod
    def _parse_flat_results(
        flat_floors_result: Any,
        flat_rooms_result: Any,
    ) -> tuple[dict[int, str], dict[tuple[int, int], str]]:
        """Extract floor/room dicts from flat endpoint results, logging failures."""
        floors: dict[int, str] = {}
        rooms: dict[tuple[int, int], str] = {}

        if not isinstance(flat_floors_result, BaseException):
            for floor in flat_floors_result:
                floors.setdefault(floor.id, floor.name)
        else:
            LOGGER.warning("Failed to fetch flat floors: %s", flat_floors_result)

        if not isinstance(flat_rooms_result, BaseException):
            for room in flat_rooms_result:
                rooms.setdefault((room.floor_id, room.id), room.name)
        else:
            LOGGER.warning("Failed to fetch flat rooms: %s", flat_rooms_result)

        return floors, rooms

    @staticmethod
    def _merge_nested_results(
        nested_results: list[tuple[_ServerFeature, Any]],
        floors: dict[int, str],
        rooms: dict[tuple[int, int], str],
    ) -> None:
        """Merge nested command results into floors/rooms dicts in-place.

        Also applies fallback room names for rooms that still have no name.
        """
        for feature, result in nested_results:
            if isinstance(result, BaseException):
                LOGGER.warning("Failed to fetch nested %s: %s", feature.value, result)
                continue
            if feature in _NESTED_3LEVEL_FEATURES:
                n_floors, n_rooms = CameDomoticAPI._parse_nested_3level(result)
            else:
                n_floors, n_rooms = CameDomoticAPI._parse_nested_2level(result)
            for fid, fname in n_floors.items():
                if fid not in floors or not floors[fid]:
                    floors[fid] = fname
            for key, rname in n_rooms.items():
                if key not in rooms or (not rooms[key] and rname):
                    rooms[key] = rname

        for key in rooms:
            if not rooms[key]:
                rooms[key] = f"Room {key[1]}"

    @staticmethod
    def _build_plant_topology(
        floors: dict[int, str],
        rooms: dict[tuple[int, int], str],
    ) -> PlantTopology:
        """Assemble a PlantTopology from merged floor/room dictionaries."""
        floor_rooms: dict[int, list[TopologyRoom]] = {}
        for (fid, rid), rname in sorted(rooms.items()):
            floor_rooms.setdefault(fid, []).append(TopologyRoom(id=rid, name=rname))

        union_keys = set(floors.keys()) | set(floor_rooms.keys())
        topology_floors = [
            TopologyFloor(
                id=fid,
                name=floors.get(fid, ""),
                rooms=floor_rooms.get(fid, []),
            )
            for fid in sorted(union_keys)
        ]

        LOGGER.info(
            "Plant topology: %d floor(s), %d room(s)",
            len(topology_floors),
            sum(len(f.rooms) for f in topology_floors),
        )
        return PlantTopology(floors=topology_floors)

    @staticmethod
    def _parse_nested_3level(
        response: dict[str, Any],
    ) -> tuple[dict[int, str], dict[tuple[int, int], str]]:
        """Extract floors and rooms from a 3-level nested response.

        Structure: array -> Floor(name, floor_ind)
        -> Room(name, room_ind) -> Device(leaf)
        """
        floors: dict[int, str] = {}
        rooms: dict[tuple[int, int], str] = {}
        for floor_node in response.get("array", []) or []:
            if floor_node.get("leaf"):
                continue
            floor_ind = floor_node.get("floor_ind")
            if floor_ind is None:
                continue
            floors[floor_ind] = floor_node.get("name", "")
            for room_node in floor_node.get("array", []) or []:
                if room_node.get("leaf"):
                    continue
                room_ind = room_node.get("room_ind")
                if room_ind is not None:
                    rooms[(floor_ind, room_ind)] = room_node.get("name", "")
        return floors, rooms

    @staticmethod
    def _parse_nested_2level(
        response: dict[str, Any],
    ) -> tuple[dict[int, str], dict[tuple[int, int], str]]:
        """Extract floors and room IDs from a 2-level nested response.

        Structure: array -> Floor(name, floor_ind) -> Device(leaf, with room_ind)
        Room names are not available at this level.
        """
        floors: dict[int, str] = {}
        rooms: dict[tuple[int, int], str] = {}
        for floor_node in response.get("array", []) or []:
            if floor_node.get("leaf"):
                continue
            floor_ind = floor_node.get("floor_ind")
            if floor_ind is None:
                continue
            floors[floor_ind] = floor_node.get("name", "")
            for device_node in floor_node.get("array", []) or []:
                room_ind = device_node.get("room_ind")
                device_floor = device_node.get("floor_ind", floor_ind)
                if room_ind is not None and device_floor is not None:
                    rooms.setdefault((device_floor, room_ind), "")
        return floors, rooms

    @classmethod
    async def async_create(
        cls,
        host: str,
        username: str,
        password: str,
        *,
        websession: aiohttp.ClientSession | None = None,
        close_websession_on_disposal: bool = False,
        command_timeout: int = _DEFAULT_COMMAND_TIMEOUT,
    ) -> CameDomoticAPI:
        """Create a CameDomoticAPI object.

        Args:
            host (str): The host of the CAME Domotic server.
            username (str): The username to use for the API.
            password (str): The password to use for the API.
            websession (aiohttp.ClientSession, optional): The aiohttp session to use for
                the API. If not provided, a new aiohttp.ClientSession will be created.
            close_websession_on_disposal (bool, default False): Controls whether the
                aiohttp session is closed when this object is disposed.

                - ``False`` (default): the session is **preserved** on disposal. Use
                  this when the caller owns the session and reuses it elsewhere — which
                  is the typical case in Home Assistant and other frameworks that
                  maintain a single long-lived ``aiohttp.ClientSession`` shared across
                  multiple integrations. Closing it here would break every other
                  component that relies on it.
                - ``True``: the session is closed on disposal. Use this only when you
                  explicitly want this object to take ownership of the provided session
                  and close it when done.

                .. note::
                    When no ``websession`` is provided, this argument is ignored: the
                    internally created session is always closed on disposal.
            command_timeout (int, optional): the default timeout in seconds
                for all commands sent to the server (default: 30s).

        Returns:
            CameDomoticAPI: The CameDomoticAPI object.

        Raises:
            CameDomoticServerNotFoundError: if the host doesn't respond to an HTTP
                request or doesn't expose the CAME Domotic API endpoint.

        Note:
            The session is not logged in until the first request is made.
        """
        LOGGER.debug("Creating CameDomoticAPI for host '%s'", host)
        session = websession or aiohttp.ClientSession()
        try:
            auth = await Auth.async_create(
                session,
                host,
                username,
                password,
                close_websession_on_disposal=(
                    close_websession_on_disposal if websession else True
                ),
                command_timeout=command_timeout,
            )
        except Exception:
            LOGGER.warning(
                "Failed to create API for host '%s', cleaning up session", host
            )
            if not websession:
                await session.close()
            raise
        LOGGER.info("CameDomoticAPI created for host '%s'", host)
        return cls(auth, command_timeout=command_timeout)
