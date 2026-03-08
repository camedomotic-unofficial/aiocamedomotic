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

from types import TracebackType

import aiohttp

from .auth import Auth
from .const import (
    _DEFAULT_COMMAND_TIMEOUT,
    _CommandName,
    _CommandNameResponse,
    _CommandType,
    _TopologicScope,
)
from .models import (
    AnalogSensor,
    Floor,
    Light,
    Opening,
    Room,
    Scenario,
    ServerInfo,
    ThermoZone,
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
        lights_list = json_response.get("array", [])
        LOGGER.info("Retrieved %d light(s)", len(lights_list))
        return [Light(light, self.auth) for light in lights_list]

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
        zones_list = json_response.get("array", [])
        LOGGER.info("Retrieved %d thermo zone(s)", len(zones_list))
        return [ThermoZone(zone, self.auth) for zone in zones_list]

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
                sensors.append(AnalogSensor(sensor_data))
        LOGGER.info("Retrieved %d analog sensor(s)", len(sensors))
        return sensors

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

        openings_data = json_response.get("array", [])
        LOGGER.info("Retrieved %d opening(s)", len(openings_data))
        return [Opening(opening_data, self.auth) for opening_data in openings_data]

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
        scenarios_list = json_response.get("array", [])
        LOGGER.info("Retrieved %d scenario(s)", len(scenarios_list))
        return [Scenario(data, self.auth) for data in scenarios_list]

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
            close_websession_on_disposal (bool, default False): If True, the aiohttp
                session will be closed when the CameDomoticAPI object is disposed. If
                the websession is not provided, this argument is ignored and the session
                will always be closed.
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
