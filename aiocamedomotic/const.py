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

from __future__ import annotations

from enum import Enum, IntEnum

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


class DeviceType(IntEnum):
    """Device type IDs used by the CAME ETI/Domo system.

    Each device in the CAME Domotic system is associated with one of these type
    identifiers. Not all device types are currently supported by this library.

    Supported types:
        - ENERGY_SENSOR (-2)
        - ANALOG_SENSOR (-1)
        - LIGHT (0)
        - OPENING (1)
        - THERMOSTAT (2)
        - SCENARIO (4)
        - GENERIC_RELAY (11)
        - DIGITAL_INPUT (14)
    """

    ENERGY_SENSOR = -2
    ANALOG_SENSOR = -1
    LIGHT = 0
    OPENING = 1
    THERMOSTAT = 2
    PAGE = 3
    SCENARIO = 4
    CAMERA = 5
    SECURITY_PANEL = 6
    SECURITY_AREA = 7
    SECURITY_SCENARIO = 8
    SECURITY_INPUT = 9
    SECURITY_OUTPUT = 10
    GENERIC_RELAY = 11
    GENERIC_TEXT = 12
    SOUND_ZONE = 13
    DIGITAL_INPUT = 14


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
    SCENARIOS_LIST = "scenarios_list_req"
    RELAYS_LIST = "relays_list_req"
    THERMO_LIST = "thermo_list_req"
    METERS_LIST = "meters_list_req"
    DIGITALIN_LIST = "digitalin_list_req"
    # Status
    STATUS_UPDATE = "status_update_req"
    # Actions
    LIGHT_SWITCH = "light_switch_req"
    OPENING_MOVE = "opening_move_req"
    SCENARIO_ACTIVATION = "scenario_activation_req"


class _CommandNameResponse(Enum):
    "Values for validating the response type to a CAME Domotic request"

    # Lists
    FEATURE_LIST = "feature_list_resp"
    FLOOR_LIST = "floor_list_resp"
    ROOM_LIST = "room_list_resp"
    LIGHT_LIST = "light_list_resp"
    OPENINGS_LIST = "openings_list_resp"
    SCENARIOS_LIST = "scenarios_list_resp"
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
    RELAYS = "relays"
    THERMOREGULATION = "thermoregulation"
    SCENARIOS = "scenarios"
    DIGITALIN = "digitalin"
    ENERGY = "energy"
    LOADSCTRL = "loadsctrl"


# endregion


class UpdateIndicator(Enum):
    """Known status-update indication cmd_names from the CAME API.

    These identify the type of state change in a ``status_update_resp`` result
    item. Some indicators have two variants: one observed in real API traffic
    and one documented in API_reference.md. Both are mapped for firmware
    compatibility.
    """

    # Traffic-observed names
    LIGHT = "light_switch_ind"
    OPENING = "opening_move_ind"
    THERMOSTAT = "thermo_zone_info_ind"
    DIGITAL_INPUT = "digitalin_status_ind"
    SCENARIO_STATUS = "scenario_status_ind"
    SCENARIO_ACTIVATION = "scenario_activation_ind"
    ENERGY_METER = "meter_instant_power_ind"
    LOADSCTRL_METER = "loadsctrl_meter_ind"
    LOADSCTRL_RELAY = "loadsctrl_relay_ind"
    PLANT = "plant_update_ind"
    # API_reference.md variants (kept for firmware compatibility)
    LIGHT_LEGACY = "light_update_ind"
    OPENING_LEGACY = "opening_update_ind"
    THERMOSTAT_LEGACY = "thermo_update_ind"
    RELAY_LEGACY = "relay_update_ind"
    DIGITAL_INPUT_LEGACY = "digitalin_update_ind"
    SCENARIO_USER_LEGACY = "scenario_user_ind"


# Mapping from status update cmd_name to DeviceType
_UPDATE_CMD_TO_DEVICE_TYPE: dict[str, DeviceType] = {
    # Traffic-observed indicator names
    "light_switch_ind": DeviceType.LIGHT,
    "opening_move_ind": DeviceType.OPENING,
    "thermo_zone_info_ind": DeviceType.THERMOSTAT,
    "digitalin_status_ind": DeviceType.DIGITAL_INPUT,
    "scenario_status_ind": DeviceType.SCENARIO,
    "scenario_activation_ind": DeviceType.SCENARIO,
    "meter_instant_power_ind": DeviceType.ENERGY_SENSOR,
    # API_reference.md variant names (firmware compatibility)
    "light_update_ind": DeviceType.LIGHT,
    "opening_update_ind": DeviceType.OPENING,
    "thermo_update_ind": DeviceType.THERMOSTAT,
    "relay_update_ind": DeviceType.GENERIC_RELAY,
    "digitalin_update_ind": DeviceType.DIGITAL_INPUT,
    "scenario_user_ind": DeviceType.SCENARIO,
    # plant_update_ind intentionally omitted: it requires full cache
    # invalidation, not a per-device update
}

# Mapping from DeviceType to the corresponding server feature
_DEVICE_TYPE_TO_FEATURE: dict[DeviceType, _ServerFeature] = {
    DeviceType.LIGHT: _ServerFeature.LIGHTS,
    DeviceType.OPENING: _ServerFeature.OPENINGS,
    DeviceType.GENERIC_RELAY: _ServerFeature.RELAYS,
    DeviceType.THERMOSTAT: _ServerFeature.THERMOREGULATION,
    DeviceType.SCENARIO: _ServerFeature.SCENARIOS,
    DeviceType.DIGITAL_INPUT: _ServerFeature.DIGITALIN,
    DeviceType.ENERGY_SENSOR: _ServerFeature.ENERGY,
}
