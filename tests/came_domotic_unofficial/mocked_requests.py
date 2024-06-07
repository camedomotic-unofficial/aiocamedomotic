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

"""This module contains examples of responses from the CAME Domotic server.

These responses are used to test the CAME Domotic server client.
"""

SL_REGISTRATION_REQ = {
    "sl_cmd": "sl_registration_req",
    "sl_login": "user",
    "sl_pwd": "password",
}

SL_USERS_LIST_REQ = {"sl_client_id": "my_session_id", "sl_cmd": "sl_users_list_req"}

SL_KEEP_ALIVE_REQ = {"sl_client_id": "my_session_id", "sl_cmd": "sl_keep_alive_req"}

SL_LOGOUT_REQ = {"sl_client_id": "my_session_id", "sl_cmd": "sl_logout_req"}

FEATURE_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "feature_list_req",
        "cseq": 1,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

STATUS_UPDATE_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "status_update_req",
        "cseq": 1,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

LIGHT_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "light_list_req",
        "cseq": 1,
        "topologic_scope": "plant",
        "value": 0,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

LIGHT_SWITCH_REQ = {
    "sl_appl_msg": {
        "act_id": 21,
        "client": "my_session_id",
        "cmd_name": "light_switch_req",
        "cseq": 1,
        "wanted_status": 1,
        "perc": 80,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

OPENINGS_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "openings_list_req",
        "cseq": 6,
        "topologic_scope": "plant",
        "value": 0,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

OPENING_MOVE_REQ = {
    "sl_appl_msg": {
        "act_id": 23,
        "client": "my_session_id",
        "cmd_name": "opening_move_req",
        "cseq": 1,
        "wanted_status": 1,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

SCENARIOS_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "scenarios_list_req",
        "cseq": 1,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

SCENARIO_ACTIVATION_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "scenario_activation_req",
        "cseq": 1,
        "id": 7,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

DIGITALIN_LIST_REQ = {
    "sl_appl_msg": {"cmd_name": "digitalin_list_req", "cseq": 1, "filter": 1012},
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

THERMO_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "thermo_list_req",
        "cseq": 1,
        "extended_infos": 2,
        "topologic_scope": "plant",
        "value": 0,
        "wanted_season": 2,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

THERMO_ZONE_CONFIG_REQ = {
    "sl_appl_msg": {
        "act_id": 22,
        "client": "my_session_id",
        "cmd_name": "thermo_zone_config_req",
        "cseq": 1,
        "extended_infos": 1,
        "mode": 2,
        "profile_data": "111111111111111111114444444411111111111111111111"
        "111111111111111111111111333344444444444444444444",
        "profile_id": 1,
        "set_point": 245,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

THERMO_SEASON_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "thermo_season_req",
        "cseq": 1,
        "season": "plant_off",
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

ENERGY_STAT_REQ = {
    "sl_appl_msg": {
        "UT_sec": 1893456000,
        "cmd_name": "energy_stat_req",
        "cseq": 1,
        "display_UT_sec": 1893456000,
        "meter_id": 4,
        "request_id": 1,
        "scope": "week",
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

METERS_LIST_REQ = {
    "sl_appl_msg": {"cmd_name": "meters_list_req", "cseq": 1},
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

LOADSCTRL_METER_LIST_REQ = {
    "sl_appl_msg": {"cmd_name": "loadsctrl_meter_list_req", "cseq": 1},
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

LOADSCTRL_METER_SET_REQ = {
    "sl_appl_msg": {
        "cmd_name": "loadsctrl_meter_set_req",
        "cseq": 137,
        "hysteresis": 1000,
        "id": 196632,
        "max_power": 4800,
        "profile_data": [
            "155555555555555555555555",
            "555555555555555555555555",
            "555555555555555555555555",
            "555555555555555555555555",
            "555555555555555555555555",
            "555555555555555555555555",
            "555555555555555555555555",
        ],
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

LOADSCTRL_RELAY_SET_REQ = {
    "sl_appl_msg": {
        "cmd_name": "loadsctrl_relay_set_req",
        "cseq": 1,
        "enabled": 1,
        "id": 65432,
        "priority": 78,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}

TERMINALS_GROUPS_LIST_REQ = {
    "sl_appl_msg": {
        "client": "my_session_id",
        "cmd_name": "terminals_groups_list_req",
        "cseq": 1,
    },
    "sl_appl_msg_type": "domo",
    "sl_client_id": "my_session_id",
    "sl_cmd": "sl_data_req",
}
