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

from enum import Enum

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


# region Enums for building the JSON commands to be sent to the Came Domotic server


class _CommandType(Enum):
    'Values for the "sl_cmd" attribute'

    DATA_REQUEST = "sl_data_req"
    REGISTRATION_REQUEST = "sl_registration_req"
    KEEP_ALIVE_REQUEST = "sl_keep_alive_req"
    LOGOUT_REQUEST = "sl_logout_req"
    USERS_LIST_REQUEST = "sl_users_list_req"


class _CommandName(Enum):
    'Values for the "cmd_name" attribute in the "sl_appl_msg" payload key'

    # Lists
    FEATURE_LIST = "feature_list_req"
    FLOOR_LIST = "floor_list_req"
    ROOM_LIST = "room_list_req"
    LIGHT_LIST = "light_list_req"
    OPENINGS_LIST = "openings_list_req"
    RELAYS_LIST = "relays_list_req"
    THERMO_LIST = "thermo_list_req"
    METERS_LIST = "meters_list_req"
    DIGITALIN_LIST = "digitalin_list_req"
    # Status
    STATUS_UPDATE = "status_update_req"
    # Actions
    LIGHT_SWITCH = "light_switch_req"
    OPENING_MOVE = "opening_move_req"


class _CommandNameResponse(Enum):
    "Values for validating the response type to a CAME Domotic request"

    # Lists
    FEATURE_LIST = "feature_list_resp"
    FLOOR_LIST = "floor_list_resp"
    ROOM_LIST = "room_list_resp"
    LIGHT_LIST = "light_list_resp"
    OPENINGS_LIST = "openings_list_resp"
    RELAYS_LIST = "relays_list_resp"
    THERMO_LIST = "thermo_list_resp"
    METERS_LIST = "meters_list_resp"
    DIGITALIN_LIST = "digitalin_list_resp"
    # Status
    STATUS_UPDATE = "status_update_resp"
    # Actions


class _TopologicScope(Enum):
    "Topologic scopes used in the CAME Domotic requests"

    PLANT = "plant"


class _ServerFeature(Enum):
    LIGHTS = "lights"
    OPENINGS = "openings"
    THERMOREGULATION = "thermoregulation"
    SCENARIOS = "scenarios"
    DIGITALIN = "digitalin"
    ENERGY = "energy"
    LOADSCTRL = "loadsctrl"


# endregion
