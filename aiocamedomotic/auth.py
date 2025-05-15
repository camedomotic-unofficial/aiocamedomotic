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
This module manages the HTTP interaction with the CAME Domotic API.

Note:
   As a consumer of the CAME Domotic Unofficial library, **it's quite unlikely that you
   will need to use this class directly**: you should use the ``CameDomoticAPI`` and the
   CameEntity classes instead.

   In case of special needs, consider requesting the implementation of the desired
   feature in the CAME Domotic Unofficial library, or forking the library and implement
   the feature yourself.
"""

import functools
import json
import time
from typing import Optional
from asyncio import Lock
import aiohttp

from cryptography.fernet import Fernet

from .utils import LOGGER
from .errors import (
    CameDomoticAuthError,
    CameDomoticServerError,
    CameDomoticServerNotFoundError,
)


def handle_came_domotic_errors(func):
    """Decorator to handle CAME Domotic API errors.

    The decorator catches the following exceptions:
    - aiohttp.ClientResponseError: for HTTP errors (4xx, 5xx)
    - aiohttp.ServerTimeoutError: for timeouts
    - aiohttp.ClientError: for other network-related errors
    - any other exception: for unforeseen errors

    Raises:
        CameDomoticServerError: in case of any of the above errors.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """Wrapper function for the decorator."""
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientResponseError as e:
            # Specific HTTP errors
            raise CameDomoticServerError(
                f"HTTP POST resulted in an HTTP {e.status} error ({e.message})"
            ) from e
        except aiohttp.ServerTimeoutError as e:
            # Handle timeouts specifically
            raise CameDomoticServerError(
                f"HTTP POST resulted in a timeout error ({e})"
            ) from e
        except aiohttp.ClientError as e:
            # General network-related errors
            raise CameDomoticServerError(
                f"HTTP POST resulted in an unexpected network error ({e})'"
            ) from e
        except Exception as e:
            # Catch-all for any other unforeseen errors
            raise CameDomoticServerError(
                "Generic error in communication with CAME Domotic API."
            ) from e

    return wrapper


class Auth:
    """Class to make authenticated requests to the CAME Domotic API server.

    Note:
        This class is not meant to be used directly, but through the ``CameDomoticAPI``
        class. To create an instance of this class, use the factory method
        ``async_create``.
    """

    # Default timeout "safe zone" for session expiration
    _DEFAULT_SAFE_ZONE_SEC = 30
    _DEFAULT_HTTP_HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
    }

    # Factory method to create an Auth instance
    @classmethod
    async def async_create(
        cls,
        websession: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        close_websession_on_disposal: bool = True,
    ):
        """Create an Auth instance.

        Args:
            websession (ClientSession): the aiohttp client session.
            host (str): the host of the CAME Domotic server.
            username (str): the username to use for the authentication.
            password (str): the password to use for the authentication.
            close_websession_on_disposal (bool, optional): whether to close the
                websession when disposing the Auth instance (default: True).

        Raises:
            CameDomoticServerNotFoundError: if the host doesn't respond to an HTTP
                request or doesn't expose the CAME Domotic API endopoint.

        Returns:
            Auth: the Auth instance.

        Note:
            The session is not logged in until the first request is made.
        """

        auth = cls(
            websession,
            host,
            username,
            password,
            close_websession_on_disposal=close_websession_on_disposal,
        )
        await auth.async_validate_host()

        return auth

    @staticmethod
    def create_cypher_suite() -> Fernet:
        """Create a cypher suite."""
        key = Fernet.generate_key()
        return Fernet(key)

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        close_websession_on_disposal: bool = True,
    ):
        """Initialize the Auth instance.

        Args:
            websession (ClientSession): the aiohttp client session.
            host (str): the host of the CAME Domotic server.
            username (str): the username to use for the authentication.
            password (str): the password to use for the authentication.
            close_websession_on_disposal (bool, optional, default True): whether to
                close the websession when disposing the Auth instance (default: True).

        Note:
            This method doesn't check the validity of the host URL.
            The session is not logged in until the first request is made.
        """

        # Encrypt the username and password for security reasons:
        # the encryption key is generated at runtime and not stored anywhere.
        # This is not much secure, but it's better than storing the credentials
        # in clear text in the memory of the running process; also, this at least ensure
        # that the credentials cannot be written in the logs even by mistake.
        self.cipher_suite = Auth.create_cypher_suite()
        self.username = self.cipher_suite.encrypt(username.encode())
        self.password = self.cipher_suite.encrypt(password.encode())

        self.host = host
        self.websession = websession
        self.close_websession_on_disposal = close_websession_on_disposal

        self.session_expiration_timestamp = (
            time.monotonic() - 3600
        )  # Set to an old timestamp to force login

        self.client_id = ""
        self.keep_alive_timeout_sec = 0
        self.cseq = 0

        self._lock = Lock()

    # region Context manager

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.async_dispose()

    # endregion

    def get_endpoint_url(self) -> str:
        """Get the CAME Domotic endpoint URL.

        Returns:
            str: the endpoint URL.
        """

        return f"http://{self.host}/domo/"

    async def async_get_valid_client_id(self) -> str:
        """Get a valid client ID, eventually logging in if needed.

        Returns:
            str: the client ID.

        Raises:
            CameDomoticAuthError: if an error occurs during the login.
        """
        async with self._lock:
            if not self.is_session_valid():
                await self._async_perform_login()
            return self.client_id

    @handle_came_domotic_errors
    async def async_send_command(
        self,
        payload: dict,
        *,
        timeout: Optional[int] = 10,
        skip_ack_check: bool = False,
    ) -> aiohttp.ClientResponse:
        """Send a command to the CAME Domotic server.

        Args:
            payload (dict): the payload to send.
            timeout (int, optional): the timeout in seconds (default: 10s).
            skip_ack_check (bool, optional): whether to skip the ACK check (default:
                False).

        Returns:
            ClientResponse: the response.

        Raises:
            CameDomoticServerError: if an error occurs during the command.
        """

        try:
            response = await self.websession.post(
                self.get_endpoint_url(),
                data={"command": json.dumps(payload)},
                headers=Auth._DEFAULT_HTTP_HEADERS,
                timeout=aiohttp.ClientTimeout(total=timeout),
            )

            # Check if the response HTTP status is 2xx
            if 200 <= response.status < 300:
                # Increment the command sequence number
                self.cseq += 1
                # Refresh the session expiration timestamp, keeping a "safe zone"
                self.session_expiration_timestamp = time.monotonic() + max(
                    0, self.keep_alive_timeout_sec - Auth._DEFAULT_SAFE_ZONE_SEC
                )

            if not skip_ack_check:
                await self.async_raise_for_status_and_ack(response)

            return response

        except CameDomoticServerError as e:
            cmd_name = (payload.get("sl_appl_msg") or {}).get("cmd_name")
            LOGGER.error("Error sending command '%s': %s", cmd_name, e)
            raise e
        except Exception as e:
            cmd_name = (payload.get("sl_appl_msg") or {}).get("cmd_name")
            LOGGER.exception("Error sending command '%s': %s", cmd_name, e)
            raise CameDomoticServerError("Error sending command") from e

    # The following method is not async because it is used in the __init__ method
    async def async_validate_host(self, timeout: Optional[int] = 10) -> None:
        """Validate the host asynchronously using aiohttp.

        Args:
            timeout (int, optional): the timeout in seconds (default: 10s).

        Raises:
            CameDomoticServerNotFoundError: if the host doesn't respond to an HTTP
                request or doesn't expose the CAME Domotic API endopoint.
        """
        endpoint_url = self.get_endpoint_url()
        client_timeout = aiohttp.ClientTimeout(total=timeout)

        try:
            async with self.websession.get(
                endpoint_url, timeout=client_timeout
            ) as resp:
                # Ensure that the server URL is available
                resp.raise_for_status()
                if resp.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=resp.reason or "Unknown error",
                        headers=resp.headers,
                    )
        except aiohttp.ClientResponseError as e:
            # Specific HTTP errors
            raise CameDomoticServerNotFoundError(
                f"HTTP GET of '{endpoint_url}' resulted in an HTTP {e.status} error "
                f"({e.message})"
            ) from e
        except aiohttp.ServerTimeoutError as e:
            # Handle timeouts specifically
            raise CameDomoticServerNotFoundError(
                f"HTTP GET of '{endpoint_url}' resulted in a timeout error)"
            ) from e
        except aiohttp.ClientError as e:
            # Broader category for client-side issues
            raise CameDomoticServerNotFoundError(
                f"HTTP GET of '{endpoint_url}' resulted in an unexpected error ({e})'"
            ) from e

    async def async_login(self) -> None:
        """Login to the CAME Domotic server.

        Raises:
            CameDomoticAuthError: if an error occurs during the login.
        """
        async with self._lock:
            if self.is_session_valid():
                await self._async_perform_keep_alive()
            else:
                await self._async_perform_login()

    async def _async_perform_login(self) -> None:
        """Login to the CAME Domotic server (no lock).

        Raises:
            CameDomoticAuthError: if an error occurs during the login.
        """
        try:
            payload = {
                "sl_cmd": "sl_registration_req",
                "sl_login": self.cipher_suite.decrypt(self.username).decode(),
                "sl_pwd": self.cipher_suite.decrypt(self.password).decode(),
            }

            # skip_ack_check = True so that a bad ACK code is tracked as an
            # authentication error and not as a generic server error
            response = await self.async_send_command(payload, skip_ack_check=True)
            data = await response.json(content_type=None)

            # Validate the response ACK code
            ack_reason = data.get("sl_data_ack_reason")
            if ack_reason and ack_reason == 1:
                raise CameDomoticAuthError("Bad credentials.")
            if ack_reason and ack_reason != 0:
                raise CameDomoticAuthError(
                    f"Authentication failed (ACK error: {ack_reason})"
                )

            # ACK is ok, store the login data
            self.client_id = data.get("sl_client_id")
            self.keep_alive_timeout_sec = data.get("sl_keep_alive_timeout_sec")
            self.session_expiration_timestamp = time.monotonic() + max(
                0, self.keep_alive_timeout_sec - Auth._DEFAULT_SAFE_ZONE_SEC
            )
        except CameDomoticAuthError as e:
            raise e
        except json.JSONDecodeError as e:
            raise CameDomoticAuthError(
                "Bad login response (JSON decoding failed)"
            ) from e
        except aiohttp.ClientResponseError as e:
            raise CameDomoticAuthError(
                f"Login failed due to HTTP {e.status} error ({e.message})"
            ) from e
        except Exception as e:
            raise CameDomoticAuthError("Unexpected error logging in") from e

    async def async_keep_alive(self) -> None:
        """Keep the session alive, eventually logging in again if needed.

        Raises:
            CameDomoticServerError: if an error occurs during the keep-alive request.
            CameDomoticAuthError: if an error occurs during the login.
        """
        async with self._lock:
            if not self.is_session_valid():
                await self._async_perform_login()
            else:
                await self._async_perform_keep_alive()

    async def _async_perform_keep_alive(self) -> None:
        """Keep the session alive, eventually logging in again if needed (no lock).

        Raises:
            CameDomoticServerError: if an error occurs during the keep-alive request.
            CameDomoticAuthError: if an error occurs during the login.
        """
        payload = {
            "sl_client_id": self.client_id,
            "sl_cmd": "sl_keep_alive_req",
        }
        await self.async_send_command(payload)

    @handle_came_domotic_errors
    async def async_logout(self) -> None:
        """Logout from the CAME Domotic server.

        Raises:
            CameDomoticServerError: if an error occurs during the logout.
        """

        # Logout only if the session is still valid
        if self.is_session_valid():
            payload = {
                "sl_client_id": self.client_id,
                "sl_cmd": "sl_logout_req",
            }

            await self.async_send_command(payload)

            self.client_id = ""
            self.session_expiration_timestamp = time.monotonic()

    async def async_dispose(self):
        """Dispose the Auth instance, eventually logging out if needed.

        This method also explicitly clears sensitive attributes (username, password,
        and cipher_suite) to enhance security when the Auth instance is disposed.
        """
        if self.is_session_valid():
            try:
                await self.async_logout()
            except CameDomoticServerError:
                pass
        if self.close_websession_on_disposal:
            await self.websession.close()

        # Explicitly clear sensitive attributes
        self.username = None
        self.password = None
        self.cipher_suite = None

    # region Utilities

    def is_session_valid(self) -> bool:
        """Check whether the session is still valid or not."""
        # Notice that self.session_expiration_timestamp already include the safe zone
        # set with the private constant _DEFAULT_SAFE_ZONE_SEC
        return (
            self.session_expiration_timestamp > time.monotonic()
            and self.client_id != ""
        )

    @staticmethod
    async def async_raise_for_status_and_ack(response: aiohttp.ClientResponse):
        """Check the response status and raise an error if necessary.

        Args:
            response (ClientResponse): the response.

        Raises:
            CameDomoticServerError: if there is an error interacting with
                the remote CAME Domotic server.
        """
        try:
            response.raise_for_status()
        except Exception as e:
            raise CameDomoticServerError(
                f"Exception raised for HTTP status: {response.status}"
            ) from e

        try:
            resp_json = await response.json(content_type=None)
        except json.JSONDecodeError as e:
            raise CameDomoticServerError("Error decoding the response to JSON") from e

        ack_reason = resp_json.get("sl_data_ack_reason")

        if ack_reason and ack_reason != 0:
            raise CameDomoticServerError(f"Bad ack code ({ack_reason})")

    def backup_auth_credentials(self):
        """Backup the current authentication credentials."""
        return (
            self.username,
            self.password,
            self.client_id,
            self.session_expiration_timestamp,
            self.keep_alive_timeout_sec,
            self.cseq,
        )

    def restore_auth_credentials(self, backup_state):
        """Restore authentication credentials from a backup.

        Args:
            backup_state (tuple): Username and password.
        """
        (
            self.username,
            self.password,
            self.client_id,
            self.session_expiration_timestamp,
            self.keep_alive_timeout_sec,
            self.cseq,
        ) = backup_state

    def update_auth_credentials(self, username, password):
        """Update the authentication credentials.

        Args:
            username (str): New username.
            password (str): New password.
        """
        self.username = self.cipher_suite.encrypt(username.encode())
        self.password = self.cipher_suite.encrypt(password.encode())

        # Invalidate the (previous) session, since the credentials have changed
        self.session_expiration_timestamp = time.monotonic() - 3600
        self.client_id = ""

    # endregion
