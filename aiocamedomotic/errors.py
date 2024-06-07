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


class CameDomoticError(Exception):
    """Base exception class for the CAME Domotic package."""


class CameDomoticServerNotFoundError(CameDomoticError):
    """Raised when the specified host is not available"""


# Authentication exception class
class CameDomoticAuthError(CameDomoticError):
    """Raised when there is an authentication error with the remote server."""


# Server exception class
class CameDomoticServerError(CameDomoticError):
    """
    Raised if an error occurs while interacting with the remote CAME Domotic server
    """

    @staticmethod
    def format_ack_error(ack_code: str = "N/A", reason: str = "N/A") -> str:
        """Formats the ack code and reason in a human-readable format.

        Args:
            ack_code (str, optional): the ack code. Defaults to "N/A".
            reason (str, optional): the reason. Defaults to "N/A".

        Returns:
            str: the formatted error message.
        """

        # Convert with str() to ensure that will never raise an exception
        return f"Bad ack code: {str(ack_code)} - Reason: {str(reason)}"
