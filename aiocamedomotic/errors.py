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
"""

from .const import get_ack_error_message, is_auth_error


class CameDomoticError(Exception):
    """Base exception class for the CAME Domotic package."""


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
        message = get_ack_error_message(ack_code)
        return f"ACK error {ack_code}: {message}"

    @staticmethod
    def create_ack_error(ack_code: int):
        """Create appropriate exception based on ACK error code.

        Args:
            ack_code (int): The ACK error code from the server.

        Returns:
            CameDomoticError: Appropriate exception instance based on error code.
        """
        message = CameDomoticServerError.format_ack_error(ack_code)

        if is_auth_error(ack_code):
            return CameDomoticAuthError(message)
        else:
            return CameDomoticServerError(message)
