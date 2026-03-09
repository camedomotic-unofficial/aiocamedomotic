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

"""Utilities for the CAME Domotic API."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import aiohttp

LOGGER = logging.getLogger(__package__)


async def async_is_came_endpoint(
    host: str,
    websession: aiohttp.ClientSession | None = None,
    timeout: int = 10,
) -> bool:
    """Check whether a host exposes the CAME Domotic API endpoint.

    Performs a credential-free HTTP GET on the CAME API URL to determine
    if the host is a CAME ETI/Domo server. Suitable for network
    autodiscovery alongside :data:`~aiocamedomotic.const.CAME_MAC_PREFIXES`.

    Args:
        host: IP address or hostname of the device to check
            (e.g., ``"192.168.1.100"``, ``"came-server.local"``).
        websession: Optional :class:`aiohttp.ClientSession` to reuse. When
            provided, the caller retains ownership and the session will **not**
            be closed by this function. When omitted, a temporary session is
            created and closed automatically.
        timeout: HTTP request timeout in seconds (default: 10).

    Returns:
        ``True`` if the host responds with HTTP 200 on the CAME API endpoint,
        ``False`` otherwise (network error, timeout, wrong status, etc.).
    """
    endpoint_url = f"http://{host}/domo/"
    LOGGER.debug("Checking CAME endpoint at '%s'", endpoint_url)

    own_session = websession is None
    session = websession or aiohttp.ClientSession()

    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with session.get(endpoint_url, timeout=client_timeout) as resp:
            if resp.status == 200:
                LOGGER.debug("CAME endpoint confirmed at '%s'", endpoint_url)
                return True
            LOGGER.debug(
                "Host at '%s' responded with HTTP %s", endpoint_url, resp.status
            )
            return False
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.debug("CAME endpoint check failed for '%s': %s", endpoint_url, exc)
        return False
    finally:
        if own_session:
            await session.close()


class EntityValidator:
    """Mixin class to validate the CAME entities."""

    @staticmethod
    def validate_data(
        data: Any,
        required_keys: Sequence[str],
        typed_keys: dict[str, type] | None = None,
    ) -> None:
        """
        Validates the necessary data fields in the provided dictionary.

        Args:
            data (dict): The data dictionary to validate.
            required_keys (list): A list of keys that must be present in the data.
            typed_keys (dict, optional): Mapping of key to expected type. For each
                entry, the value at that key must be an instance of the expected type.
                Keys in ``typed_keys`` should also appear in ``required_keys`` to
                ensure they are present before type-checking.

        Raises:
            ValueError: If the data is not a dict, any required key is missing,
                or any typed key has a value of the wrong type.
        """
        if not isinstance(data, dict):
            LOGGER.debug(
                "Validation failed: expected dict, got %s", type(data).__name__
            )
            raise ValueError("Provided data must be a dictionary.")

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            LOGGER.debug("Validation failed: missing keys %s", missing_keys)
            raise ValueError(
                f"Data is missing required keys: {', '.join(missing_keys)}"
            )

        if typed_keys:
            for key, expected_type in typed_keys.items():
                if key in data and not isinstance(data[key], expected_type):
                    LOGGER.debug(
                        "Validation failed: key '%s' expected %s, got %s",
                        key,
                        expected_type.__name__,
                        type(data[key]).__name__,
                    )
                    raise ValueError(
                        f"Key '{key}' expected {expected_type.__name__}, "
                        f"got {type(data[key]).__name__}"
                    )
