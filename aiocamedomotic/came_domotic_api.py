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

from typing import List, Optional

import aiohttp

from .utils import LOGGER

from .auth import Auth
from .models import ServerInfo, User, Light, UpdateList, Opening


class CameDomoticAPI:
    """Main class, exposes all the public methods of the CAME Domotic API."""

    def __init__(self, auth: Auth):
        """Initialize the CAME Domotic API object.

        Args:
            auth (Auth): the authentication object used to interact with
                the CAME Domotic API.
        """
        self.auth = auth

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.async_dispose()

    async def async_dispose(self):
        """Dispose the CameDomoticAPI object."""
        try:
            await self.auth.async_dispose()
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Error while disposing the CameDomoticAPI object")

    async def async_get_users(self) -> List[User]:
        """Get the list of users defined on the server.

        Returns:
            List[User]: List of users. Returns an empty list if no users are defined
            or if the server response doesn't contain the users list.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        client_id = await self.auth.async_get_valid_client_id()
        payload = {"sl_client_id": client_id, "sl_cmd": "sl_users_list_req"}

        response = await self.auth.async_send_command(payload)
        json_response = await response.json(content_type=None)

        # Defaults to an empty list if the key is missing from the response JSON
        users_list = json_response.get("sl_users_list", [])
        return [User(user, self.auth) for user in users_list]

    async def async_get_server_info(self) -> ServerInfo:
        """Get the server information

        Provides info about the server (keycode, software version, etc.) and the list of
        features supported by the CAME Domotic server.

        Returns:
            ServerInfo: Server information.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        client_id = await self.auth.async_get_valid_client_id()
        payload = {
            "sl_appl_msg": {
                "client": client_id,
                "cmd_name": "feature_list_req",
                "cseq": self.auth.cseq,
            },
            "sl_appl_msg_type": "domo",
            "sl_client_id": client_id,
            "sl_cmd": "sl_data_req",
        }
        response = await self.auth.async_send_command(payload)
        json_response = await response.json(content_type=None)

        return ServerInfo(
            keycode=json_response.get("keycode"),
            swver=json_response.get("swver"),
            type=json_response.get("type"),
            board=json_response.get("board"),
            serial=json_response.get("serial"),
            list=json_response.get("list"),
        )

    async def async_get_lights(self) -> List[Light]:
        """Get the list of all the light devices defined on the server.

        Returns:
            List[Light]: List of lights.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        client_id = await self.auth.async_get_valid_client_id()
        payload = {
            "sl_appl_msg": {
                "client": client_id,
                "cmd_name": "light_list_req",
                "cseq": self.auth.cseq,
                "topologic_scope": "plant",
                "value": 0,
            },
            "sl_appl_msg_type": "domo",
            "sl_client_id": client_id,
            "sl_cmd": "sl_data_req",
        }
        response = await self.auth.async_send_command(payload)
        json_response = await response.json(content_type=None)

        # Defaults to an empty list if the key is missing from the response JSON
        lights_list = json_response.get("array", [])
        return [Light(light, self.auth) for light in lights_list]

    async def async_get_updates(self) -> UpdateList:
        """Get the list of status updates from the server.

        Returns:
            CameUpdates: List of status updates.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """

        client_id = await self.auth.async_get_valid_client_id()
        payload = {
            "sl_appl_msg": {
                "client": client_id,
                "cmd_name": "status_update_req",
                "cseq": self.auth.cseq,
            },
            "sl_appl_msg_type": "domo",
            "sl_client_id": client_id,
            "sl_cmd": "sl_data_req",
        }
        response = await self.auth.async_send_command(payload)
        json_response = await response.json(content_type=None)
        return UpdateList(json_response)

    async def async_get_openings(self) -> List[Opening]:
        """Get the list of all opening devices defined on the server.

        Returns:
            List[Opening]: List of openings.

        Raises:
            CameDomoticAuthError: If the authentication fails.
            CameDomoticServerError: If the server returns an error.
        """
        client_id = await self.auth.async_get_valid_client_id()
        payload = {
            "sl_appl_msg": {
                "client": client_id,
                "cmd_name": "openings_list_req",
                "cseq": self.auth.cseq,
                "topologic_scope": "plant",
                "value": 0,
            },
            "sl_appl_msg_type": "domo",
            "sl_client_id": client_id,
            "sl_cmd": "sl_data_req",
        }
        response = await self.auth.async_send_command(payload)
        json_response = await response.json(content_type=None)

        openings_data = json_response.get("array", [])
        return [Opening(opening_data, self.auth) for opening_data in openings_data]

    @classmethod
    async def async_create(
        cls,
        host: str,
        username: str,
        password: str,
        *,
        websession: Optional[aiohttp.ClientSession] = None,
        close_websession_on_disposal: bool = False,
    ):
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

        Returns:
            CameDomoticAPI: The CameDomoticAPI object.

        Raises:
            CameDomoticServerNotFoundError: if the host doesn't respond to an HTTP
                request or doesn't expose the CAME Domotic API endopoint.

        Note:
            The session is not logged in until the first request is made.
        """
        auth = await Auth.async_create(
            websession or aiohttp.ClientSession(),
            host,
            username,
            password,
            close_websession_on_disposal=(
                close_websession_on_disposal if websession else True
            ),
        )
        return cls(auth)
