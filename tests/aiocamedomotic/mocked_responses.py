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

# pylint: disable=import-error
# pylint: disable=no-name-in-module

SL_REGISTRATION_ACK = {
    "sl_cmd": "sl_registration_ack",
    "sl_client_id": "my_session_id",
    "sl_keep_alive_timeout_sec": 900,
    "sl_data_ack_reason": 0,
}

SL_USERS_LIST_RESP = {
    "sl_cmd": "sl_users_list_resp",
    "sl_data_ack_reason": 0,
    "sl_client_id": "75c6c33a",
    "sl_users_list": [{"name": "admin"}],
}

SL_KEEP_ALIVE_ACK = {
    "sl_cmd": "sl_keep_alive_ack",
    "sl_data_ack_reason": 0,
    "sl_client_id": "my_session_id",
}

SL_LOGOUT_ACK = {
    "sl_cmd": "sl_logout_ack",
    "sl_ack_reason": 0,
    "sl_data_ack_reason": 0,
}

FEATURE_LIST_RESP = {
    "cmd_name": "feature_list_resp",
    "cseq": 1,
    "keycode": "0000FFFF9999AAAA",
    "swver": "1.2.3",
    "type": "0",
    "board": "3",
    "serial": "0011ffee",
    "list": [
        "lights",
        "openings",
        "thermoregulation",
        "scenarios",
        "digitalin",
        "energy",
        "loadsctrl",
    ],
    "recovery_status": 0,
    "sl_data_ack_reason": 0,
}

STATUS_UPDATE_RESP = {
    "cmd_name": "status_update_resp",
    "cseq": 2,
    "sl_data_ack_reason": 0,
    "result": [
        {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 7,
            "name": "Room 1",
            "floor_ind": 37,
            "room_ind": 45,
            "temp_dec": 202,
            "status": 0,
            "mode": 2,
            "set_point": 349,
            "season": "winter",
            "antifreeze": 30,
            "t1": 190,
            "t2": 200,
            "t3": 210,
            "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
            "reason": 1,
        },
        {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 5,
            "name": "Room 2",
            "floor_ind": 17,
            "room_ind": 31,
            "temp_dec": 206,
            "status": 0,
            "mode": 2,
            "set_point": 338,
            "season": "winter",
            "antifreeze": 30,
            "t1": 185,
            "t2": 195,
            "t3": 205,
            "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
            "reason": 1,
        },
        {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 11,
            "name": "Room 3",
            "floor_ind": 37,
            "room_ind": 54,
            "temp_dec": 200,
            "status": 0,
            "mode": 2,
            "set_point": 348,
            "season": "winter",
            "antifreeze": 30,
            "t1": 185,
            "t2": 200,
            "t3": 210,
            "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
            "reason": 1,
        },
    ],
}

LIGHT_LIST_RESP = {
    "array": [
        {
            "act_id": 1,
            "floor_ind": 19,
            "name": "light_ChQQs",
            "room_ind": 23,
            "status": 1,
            "type": "STEP_STEP",
        },
        {
            "act_id": 2,
            "floor_ind": 19,
            "name": "light_vdAEA",
            "room_ind": 23,
            "status": 1,
            "type": "STEP_STEP",
        },
        {
            "act_id": 3,
            "floor_ind": 19,
            "name": "light_onbFB",
            "room_ind": 23,
            "status": 0,
            "type": "STEP_STEP",
        },
        {
            "act_id": 4,
            "floor_ind": 19,
            "name": "light_xoOyy",
            "perc": 52,
            "room_ind": 23,
            "status": 0,
            "type": "DIMMER",
        },
        {
            "act_id": 5,
            "floor_ind": 19,
            "name": "light_epChT",
            "room_ind": 23,
            "status": 0,
            "type": "STEP_STEP",
        },
        {
            "act_id": 6,
            "floor_ind": 19,
            "name": "light_DVyyO",
            "room_ind": 23,
            "status": 0,
            "type": "STEP_STEP",
        },
        {
            "act_id": 7,
            "floor_ind": 19,
            "name": "light_XeXgB",
            "perc": 14,
            "room_ind": 29,
            "status": 0,
            "type": "DIMMER",
        },
    ],
    "cmd_name": "light_list_resp",
    "cseq": 1,
    "sl_data_ack_reason": 0,
}

OPENINGS_LIST_RESP = {
    "array": [
        {
            "close_act_id": 0,
            "floor_ind": 41,
            "name": "opening_GxwWQ",
            "open_act_id": 0,
            "partial": [],
            "room_ind": 41,
            "status": 0,
            "type": 0,
        },
        {
            "close_act_id": 1,
            "floor_ind": 41,
            "name": "opening_UFjCM",
            "open_act_id": 1,
            "partial": [],
            "room_ind": 47,
            "status": 0,
            "type": 0,
        },
        {
            "close_act_id": 2,
            "floor_ind": 41,
            "name": "opening_TwwAv",
            "open_act_id": 2,
            "partial": [],
            "room_ind": 53,
            "status": 0,
            "type": 0,
        },
    ],
    "cmd_name": "openings_list_resp",
    "cseq": 1,
    "sl_data_ack_reason": 0,
}

SCENARIOS_LIST_RESP = {
    "array": [
        {
            "icon_id": 14,
            "id": 0,
            "name": "scenario_SGgbR",
            "scenario_status": 0,
            "status": 0,
            "user-defined": 0,
        },
        {
            "icon_id": 14,
            "id": 1,
            "name": "scenario_OjEUl",
            "scenario_status": 0,
            "status": 0,
            "user-defined": 0,
        },
        {
            "icon_id": 14,
            "id": 2,
            "name": "scenario_dhbOA",
            "scenario_status": 0,
            "status": 0,
            "user-defined": 0,
        },
    ],
    "cmd_name": "scenarios_list_resp",
    "cseq": 2,
    "sl_data_ack_reason": 0,
}

DIGITALIN_LIST_RESP = {
    "array": [
        {
            "ack": 1,
            "act_id": 0,
            "addr": 200,
            "name": "digitalin_PvGCT",
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "type": 1,
            "utc_time": 0,
        },
        {
            "ack": 0,
            "act_id": 1,
            "addr": 201,
            "name": "digitalin_BuTbB",
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "status": 1,
            "type": 1,
            "utc_time": 1708366780,
        },
        {
            "ack": 0,
            "act_id": 2,
            "addr": 202,
            "name": "digitalin_meatO",
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "status": 1,
            "type": 1,
            "utc_time": 1708319672,
        },
        {
            "ack": 1,
            "act_id": 3,
            "addr": 203,
            "name": "digitalin_SAgye",
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "type": 1,
            "utc_time": 0,
        },
        {
            "ack": 0,
            "act_id": 4,
            "addr": 204,
            "name": "digitalin_kzvCi",
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "status": 1,
            "type": 1,
            "utc_time": 1708370274,
        },
    ],
    "cmd_name": "digitalin_list_resp",
    "cseq": 3,
    "sl_data_ack_reason": 0,
}

THERMO_LIST_RESP = {
    "cseq": 13,
    "cmd_name": "thermo_list_resp",
    "array": [
        {
            "act_id": 1,
            "name": "Room 1",
            "floor_ind": 37,
            "room_ind": 57,
            "status": 0,
            "temp": 200,
            "mode": 2,
            "set_point": 348,
            "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
            "season": "winter",
            "leaf": True,
        },
        {
            "act_id": 52,
            "name": "Room 2",
            "floor_ind": 37,
            "room_ind": 59,
            "status": 0,
            "temp": 201,
            "mode": 2,
            "set_point": 343,
            "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
            "season": "winter",
            "leaf": True,
        },
    ],
    "sl_data_ack_reason": 0,
}

ENERGY_STAT_RESP = {
    "cseq": 14,
    "meter_id": 3,
    "request_id": 2,
    "cmd_name": "energy_stat_resp",
    "unit": "W",
    "maxvalue": 5000,
    "array": [
        {
            "time": 1708372200,
            "delta_secs": -3600,
            "power": 678,
            "energy": 10218498,
        },
        {
            "time": 1708372800,
            "delta_secs": -3000,
            "power": 246,
            "energy": 10218539,
        },
        {
            "time": 1708373400,
            "delta_secs": -2400,
            "power": 264,
            "energy": 10218583,
        },
        {
            "time": 1708374000,
            "delta_secs": -1800,
            "power": 246,
            "energy": 10218624,
        },
        {
            "time": 1708374600,
            "delta_secs": -1200,
            "power": 198,
            "energy": 10218657,
        },
    ],
    "sl_data_ack_reason": 0,
}

METERS_LIST_RESP = {
    "cseq": 15,
    "cmd_name": "meters_list_resp",
    "array": [
        {
            "name": "Meter 1",
            "id": 1,
            "meter_type": 1,
            "produced": 0,
            "instant_power": 144,
            "unit": "W",
            "energy_unit": "Wh",
            "last_24h_avg": 10218678,
            "last_month_avg": 10218678,
        },
        {
            "name": "Meter 2",
            "id": 2,
            "meter_type": 1,
            "produced": 0,
            "instant_power": 144,
            "unit": "W",
            "energy_unit": "Wh",
            "last_24h_avg": 10218678,
            "last_month_avg": 10218678,
        },
    ],
    "sl_data_ack_reason": 0,
}

LOADSCTRL_METER_LIST_RESP = {
    "cseq": 16,
    "cmd_name": "loadsctrl_meter_list_resp",
    "array": [
        {
            "name": "Meter 1",
            "id": 123456,
            "hysteresis": 400,
            "max_power": 5000,
            "profile_data": [
                "444444444444444444444444",
                "444444444444444444444444",
                "444444444444444444444444",
                "444444444444444444444444",
                "444444444444444444444444",
                "444444444444444444444444",
                "444444444444444444444444",
            ],
            "meter_id": 1,
            "power": 144,
        }
    ],
    "sl_data_ack_reason": 0,
}

TERMINALS_GROUPS_LIST_RESP = {
    "cseq": 20,
    "cmd_name": "terminals_groups_list_resp",
    "array": [{"group_name": "ETI/Domo", "group_id": 5}],
    "sl_data_ack_reason": 0,
}

SL_ADD_USER_RESP = {
    "sl_cmd": "sl_add_user_ack",
    "sl_data_ack_reason": 0,
}

SL_DELETE_USER_RESP = {
    "sl_cmd": "sl_del_user_ack",
    "sl_data_ack_reason": 0,
}

SL_CHANGE_USER_PASSWORD_RESP = {
    "sl_cmd": "sl_user_pwd_change_ack",
    "sl_user_pwd_change_ack_reason": 0,
    "sl_ack_reason": 0,
    "sl_data_ack_reason": 0,
}

TIMERS_LIST_RESP = {
    "cseq": 3,
    "cmd_name": "timers_list_resp",
    "array": [
        {
            "name": "Temporizzatore",
            "id": 117,
            "enabled": 0,
            "days": 1,
            "bars": 2,
            "timetable": [
                {
                    "start": {"hour": 2, "min": 0, "sec": 0},
                    "stop": {"hour": 8, "min": 0, "sec": 0},
                    "active": 0,
                    "index": 0,
                },
                {
                    "start": {"hour": 18, "min": 30, "sec": 0},
                    "stop": {"hour": 22, "min": 0, "sec": 0},
                    "active": 1,
                    "index": 1,
                },
            ],
        },
        {
            "name": "Irrigazione giardino",
            "id": 118,
            "enabled": 1,
            "days": 85,
            "bars": 1,
            "timetable": [
                {
                    "start": {"hour": 6, "min": 0, "sec": 0},
                    "stop": {"hour": 7, "min": 30, "sec": 0},
                    "active": 1,
                    "index": 0,
                },
            ],
        },
        {
            "name": "Luci esterne",
            "id": 119,
            "enabled": 1,
            "days": 127,
            "bars": 1,
            "timetable": [
                {
                    "start": {"hour": 19, "min": 0, "sec": 0},
                    "stop": {"hour": 23, "min": 59, "sec": 59},
                    "active": 1,
                    "index": 0,
                },
            ],
        },
    ],
    "sl_data_ack_reason": 0,
}

TVCC_CAMERAS_LIST_RESP = {
    "cmd_name": "tvcc_cameras_list_resp",
    "cseq": 7,
    "sl_data_ack_reason": 0,
    "array": [
        {
            "id": 1,
            "name": "Front Door Camera",
            "uri": "http://192.168.1.100:8080/stream.swf",
            "uri_still": "http://192.168.1.100:8080/snapshot.jpg",
            "stream_type": "swf",
        },
        {
            "id": 2,
            "name": "Garden Camera",
            "uri": "http://192.168.1.101:8080/video",
            "uri_still": "http://192.168.1.101:8080/snapshot.jpg",
            "stream_type": "other_format",
        },
    ],
}

MAPS_LIST_RESP = {
    "cseq": 1,
    "cmd_name": "map_descr_resp",
    "map": [
        {
            "background": "maps/maps_living_room.jpg",
            "page_label": "Living Room",
            "page_scale": 1024,
            "page_id": 0,
            "array": [
                {
                    "x": 406,
                    "y": 289,
                    "width": 46,
                    "height": 69,
                    "label": "Ceiling Light",
                    "aspect": "maps_lights_Generic",
                    "icon_id": 0,
                    "permission": 1048575,
                    "read_only": 0,
                    "address": 84,
                    "type": 0,
                    "act_id": 13,
                    "status": 0,
                    "perc": 12,
                },
                {
                    "x": 574,
                    "y": 107,
                    "width": 46,
                    "height": 69,
                    "label": "Living Room Shutter",
                    "aspect": "maps_windows_Generic",
                    "icon_id": 0,
                    "permission": 1048575,
                    "read_only": 0,
                    "address": 25,
                    "type": 1,
                    "act_id": 68,
                },
            ],
        },
        {
            "background": "maps/maps_bedroom.jpg",
            "page_label": "Bedroom",
            "page_scale": 1024,
            "page_id": 1,
            "array": [
                {
                    "x": 504,
                    "y": 551,
                    "width": 46,
                    "height": 69,
                    "label": "Bedroom Light",
                    "aspect": "maps_lights_Generic",
                    "icon_id": 0,
                    "permission": 1048575,
                    "read_only": 0,
                    "address": 5,
                    "type": 0,
                    "act_id": 39,
                    "status": 0,
                },
                {
                    "x": 511,
                    "y": 128,
                    "width": 46,
                    "height": 69,
                    "label": "Bedroom Shutter",
                    "aspect": "maps_windows_Generic",
                    "icon_id": 0,
                    "permission": 1048575,
                    "read_only": 0,
                    "address": 20,
                    "type": 1,
                    "act_id": 60,
                },
                {
                    "x": 818,
                    "y": 165,
                    "width": 46,
                    "height": 69,
                    "label": "",
                    "aspect": "maps_thermo_Generic",
                    "icon_id": 0,
                    "permission": 1048575,
                    "read_only": 0,
                    "address": 3,
                    "type": 2,
                    "act_id": 52,
                    "temp": 214,
                    "thermo_status": 0,
                    "status": 0,
                    "mode": 2,
                },
            ],
        },
    ],
    "sl_data_ack_reason": 0,
}

ANALOGIN_LIST_RESP = {
    "cseq": 3,
    "cmd_name": "analogin_list_resp",
    "array": [
        {
            "name": "Igrometro",
            "act_id": 89,
            "value": 47,
            "unit": "%",
        },
        {
            "name": "Termometro esterno",
            "act_id": 90,
            "value": 215,
            "unit": "C",
        },
        {
            "name": "Barometro",
            "act_id": 91,
            "value": 1013,
            "unit": "hPa",
        },
    ],
    "sl_data_ack_reason": 0,
}

GENERIC_REPLY = {
    "cseq": 4,
    "cmd_name": "generic_reply",
    "sl_data_ack_reason": 0,
}
