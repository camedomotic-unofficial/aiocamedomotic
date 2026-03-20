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
This module contains the exceptions that can be raised by the CAME Domotic API.

Exception hierarchy and suggested Home Assistant mapping:

- :exc:`CameDomoticServerNotFoundError` → ``ConfigEntryNotReady``
  (host unreachable, transient)
- :exc:`CameDomoticAuthError` → ``ConfigEntryAuthFailed``
  (bad credentials, permanent — triggers reauth flow)
- :exc:`CameDomoticServerTimeoutError` → ``ConfigEntryNotReady``
  (request timeout, transient)
- :exc:`CameDomoticServerError` (other ACK codes) → log and re-raise
"""

from __future__ import annotations

from .const import AckErrorCode


class CameDomoticError(Exception):
    """Base exception class for the CAME Domotic package."""

    ack_code: AckErrorCode | int | None = None


class CameDomoticServerNotFoundError(CameDomoticError):
    """Raised when the specified host is not available."""


# Authentication exception class
class CameDomoticAuthError(CameDomoticError):
    """Raised when there is an authentication error with the remote server."""


# Server exception class
class CameDomoticServerError(CameDomoticError):
    """
    Raised if an error occurs while interacting with the remote CAME Domotic server.
    """

    @staticmethod
    def format_ack_error(ack_code: int) -> str:
        """Formats the ack code in a human-readable format.

        Args:
            ack_code (int): The ACK error code from the server.

        Returns:
            str: The formatted error message.
        """
        try:
            message = AckErrorCode(ack_code).message
        except ValueError:
            message = f"Unknown error code: {ack_code}"
        return f"ACK error {ack_code}: {message}"

    @staticmethod
    def create_ack_error(ack_code: int) -> CameDomoticError:
        """Create appropriate exception based on ACK error code.

        Args:
            ack_code (int): The ACK error code from the server.

        Returns:
            CameDomoticError: Appropriate exception instance based on error code.
        """
        message = CameDomoticServerError.format_ack_error(ack_code)

        try:
            is_auth = AckErrorCode(ack_code).is_auth
        except ValueError:
            is_auth = False

        exc: CameDomoticError
        if is_auth:
            exc = CameDomoticAuthError(message)
        else:
            exc = CameDomoticServerError(message)
        exc.ack_code = ack_code
        return exc


class CameDomoticServerTimeoutError(CameDomoticServerError):
    """Raised when a request to the CAME Domotic server times out.

    This exception indicates a transient failure. When using this library with
    Home Assistant, it should be mapped to ``ConfigEntryNotReady`` to allow the
    integration to retry with exponential backoff.

    See also the exception hierarchy mapping for Home Assistant integrations:

    - :exc:`CameDomoticServerNotFoundError` → ``ConfigEntryNotReady``
      (host unreachable, transient)
    - :exc:`CameDomoticAuthError` → ``ConfigEntryAuthFailed``
      (bad credentials, permanent — triggers reauth flow)
    - :exc:`CameDomoticServerTimeoutError` → ``ConfigEntryNotReady``
      (request timeout, transient)
    - :exc:`CameDomoticServerError` (other ACK codes) → log and re-raise
    """
