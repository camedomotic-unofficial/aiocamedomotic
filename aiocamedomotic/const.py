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
Constants for the CAME Domotic API.
"""

# ACK error codes and their meanings from the CAME Domotic server
ACK_ERROR_CODES = {
    1: "Invalid user.",
    3: "Too many sessions during login.",
    4: "Error occurred in JSON Syntax.",
    5: "No session layer command tag.",
    6: "Unrecognized session layer command.",
    7: "No client ID in request.",
    8: "Wrong client ID in request.",
    9: "Wrong application command.",
    10: "No reply to application command, maybe service down.",
    11: "Wrong application data.",
}

# Authentication-related error codes that should raise CameDomoticAuthError
AUTH_ERROR_CODES = {1, 3}


def get_ack_error_message(ack_code: int) -> str:
    """Get human-readable message for ACK error code.

    Args:
        ack_code (int): The ACK error code from the server.

    Returns:
        str: Human-readable error message.
    """
    return ACK_ERROR_CODES.get(ack_code, f"Unknown error code: {ack_code}")


def is_auth_error(ack_code: int) -> bool:
    """Check if ACK error code is authentication-related.

    Args:
        ack_code (int): The ACK error code from the server.

    Returns:
        bool: True if the error code is authentication-related.
    """
    return ack_code in AUTH_ERROR_CODES
