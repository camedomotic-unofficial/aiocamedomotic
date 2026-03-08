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

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
from unittest.mock import AsyncMock, patch

import pytest

from aiocamedomotic import Auth, CameDomoticAPI
from aiocamedomotic.errors import (
    CameDomoticAuthError,
    CameDomoticError,
    CameDomoticServerError,
    CameDomoticServerNotFoundError,
)
from aiocamedomotic.models import (
    AnalogSensor,
    Floor,
    Light,
    Opening,
    Room,
    Scenario,
    ServerInfo,
    ThermoZone,
    UpdateList,
    User,
)
from tests.aiocamedomotic.mocked_responses import (
    FEATURE_LIST_RESP,
    LIGHT_LIST_RESP,
    SCENARIOS_LIST_RESP,
    THERMO_LIST_RESP,
)


class TestAPIInit:
    async def test_init(self, auth_instance):
        api = CameDomoticAPI(auth_instance)
        assert api.auth == auth_instance

    @patch.object(Auth, "async_dispose")
    async def test_aexit_calls_async_dispose(self, mock_async_dispose, auth_instance):
        api = CameDomoticAPI(auth_instance)
        await api.__aexit__(None, None, None)
        mock_async_dispose.assert_called_once()

    @patch.object(Auth, "async_dispose")
    async def test_aexit_no_exceptions(self, mock_async_dispose, auth_instance):
        mock_async_dispose.side_effect = CameDomoticError("error")
        api = CameDomoticAPI(auth_instance)
        try:
            await api.__aexit__(None, None, None)
        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"__aexit__ raised an exception: {e}")

    @patch.object(Auth, "async_dispose")
    async def test_async_dispose_disposes_auth(self, mock_async_dispose, auth_instance):
        api = CameDomoticAPI(auth_instance)
        await api.async_dispose()
        mock_async_dispose.assert_called_once()

    @patch.object(Auth, "async_dispose")
    async def test_async_dispose_no_exceptions(self, mock_async_dispose, auth_instance):
        mock_async_dispose.side_effect = CameDomoticError("error")
        api = CameDomoticAPI(auth_instance)
        try:
            await api.async_dispose()
        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"async_dispose raised an exception: {e}")

    @patch.object(Auth, "async_dispose")
    async def test_context_manager(self, mock_async_dispose, auth_instance):
        async with CameDomoticAPI(auth_instance):
            pass
        mock_async_dispose.assert_called_once()

    @patch.object(Auth, "async_dispose")
    async def test_context_manager_no_exceptions(
        self, mock_async_dispose, auth_instance
    ):
        mock_async_dispose.side_effect = CameDomoticError("error")
        try:
            async with CameDomoticAPI(auth_instance):
                pass
            mock_async_dispose.assert_called_once()
        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"__aexit__ raised an exception: {e}")

    @patch.object(Auth, "async_create")
    async def test_async_create_all_params(self, mock_async_create):
        mock_auth = AsyncMock()
        mock_session = AsyncMock()
        mock_async_create.return_value = mock_auth

        api = await CameDomoticAPI.async_create(
            "host",
            "username",
            "password",
            websession=mock_session,
            close_websession_on_disposal=True,
        )

        mock_async_create.assert_called_once_with(
            mock_session,
            "host",
            "username",
            "password",
            close_websession_on_disposal=True,
        )
        assert api.auth == mock_auth

    @patch("aiohttp.ClientSession")
    @patch.object(Auth, "async_create")
    async def test_async_create_default_params(
        self,
        mock_async_create,
        mock_session,  # pylint: disable=unused-argument
    ):
        mock_auth = AsyncMock()
        mock_async_create.return_value = mock_auth

        api = await CameDomoticAPI.async_create("host", "username", "password")

        mock_async_create.assert_called_once()
        assert api.auth == mock_auth

    @patch.object(Auth, "async_create")
    async def test_async_create_exception(self, mock_async_create):
        mock_async_create.side_effect = CameDomoticServerNotFoundError("error")

        with pytest.raises(CameDomoticServerNotFoundError, match="error"):
            await CameDomoticAPI.async_create("host", "username", "password")


class TestAPIUsers:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_users(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "sl_cmd": "sl_users_list_resp",
            "sl_data_ack_reason": 0,
            "sl_client_id": "75c6c33a",
            "sl_users_list": [{"name": "admin"}, {"name": "user"}],
        }

        users = await api.async_get_users()
        assert len(users) == 2
        assert isinstance(users[0], User)
        assert isinstance(users[1], User)
        assert users[0].name == "admin"
        assert users[1].name == "user"
        mock_send_command.assert_called_once_with({}, command_type="sl_users_list_req")

    @patch.object(Auth, "async_send_command")
    async def test_async_get_users_empty_list(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "sl_cmd": "sl_users_list_resp",
            "sl_data_ack_reason": 0,
            "sl_client_id": "75c6c33a",
            "sl_users_list": [],  # Empty list
        }

        users = await api.async_get_users()
        assert len(users) == 0
        assert isinstance(users, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_users_missing_key(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "sl_cmd": "sl_users_list_resp",
            "sl_data_ack_reason": 0,
            "sl_client_id": "75c6c33a",
            # "sl_users_list" key is missing
        }

        users = await api.async_get_users()
        assert len(users) == 0
        assert isinstance(users, list)


class TestAPIServerInfo:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_server_info(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = FEATURE_LIST_RESP

        server_info = await api.async_get_server_info()
        assert isinstance(server_info, ServerInfo)
        assert server_info.keycode == FEATURE_LIST_RESP["keycode"]
        assert server_info.swver == FEATURE_LIST_RESP["swver"]
        assert server_info.type == FEATURE_LIST_RESP["type"]
        assert server_info.board == FEATURE_LIST_RESP["board"]
        assert server_info.serial == FEATURE_LIST_RESP["serial"]

        features = server_info.features
        assert len(features) == len(FEATURE_LIST_RESP["list"])
        assert features[0] == "lights"
        assert features[1] == "openings"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_server_info_missing_essential_keys(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "feature_list_resp",
            "cseq": 1,
            # "keycode": "0000FFFF9999AAAA", # Missing keycode
            "swver": "1.2.3",
            "type": "0",
            "board": "3",
            "serial": "0011ffee",
            "list": ["lights"],
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(
            ValueError, match="Missing required ServerInfo properties: keycode"
        ):
            await api.async_get_server_info()

        # Test missing 'list'
        mock_send_command.return_value = {
            "cmd_name": "feature_list_resp",
            "cseq": 1,
            "keycode": "0000FFFF9999AAAA",
            "swver": "1.2.3",
            "serial": "0011ffee",
            # "list": ["lights"], # Missing list
            "sl_data_ack_reason": 0,
        }
        with pytest.raises(
            ValueError, match="Missing required ServerInfo properties: features"
        ):
            await api.async_get_server_info()

        # Test multiple missing fields
        mock_send_command.return_value = {
            "cmd_name": "feature_list_resp",
            "cseq": 1,
            # "keycode": "0000FFFF9999AAAA", # Missing keycode
            "swver": "1.2.3",
            "type": "0",
            "board": "3",
            # "serial": "0011ffee", # Missing serial
            # "list": ["lights"], # Missing list
            "sl_data_ack_reason": 0,
        }
        with pytest.raises(
            ValueError,
            match="Missing required ServerInfo properties: keycode, serial, features",
        ):
            await api.async_get_server_info()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_server_info_empty_feature_list(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "feature_list_resp",
            "cseq": 1,
            "keycode": "0000FFFF9999AAAA",
            "swver": "1.2.3",
            "type": "0",
            "board": "3",
            "serial": "0011ffee",
            "list": [],  # Empty feature list
            "recovery_status": 0,
            "sl_data_ack_reason": 0,
        }

        server_info = await api.async_get_server_info()
        assert len(server_info.features) == 0


class TestAPIFloors:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_floors(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "floor_list": [
                {"floor_ind": 1, "name": "Ground Floor"},
                {"floor_ind": 2, "name": "First Floor"},
            ],
            "cmd_name": "floor_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        floors = await api.async_get_floors()
        assert len(floors) == 2
        assert isinstance(floors[0], Floor)
        assert isinstance(floors[1], Floor)
        assert floors[0].id == 1
        assert floors[0].name == "Ground Floor"
        assert floors[1].id == 2
        assert floors[1].name == "First Floor"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_floors_empty(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "floor_list": [],
            "cmd_name": "floor_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        floors = await api.async_get_floors()
        assert len(floors) == 0
        assert isinstance(floors, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_floors_missing_key(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            # "floor_list" key is missing
            "cmd_name": "floor_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        floors = await api.async_get_floors()
        assert len(floors) == 0
        assert isinstance(floors, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_floors_malformed_data(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "floor_list": [
                {"name": "Ground Floor"},  # Missing floor_ind
            ],
            "cmd_name": "floor_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(
            ValueError, match="Data is missing required keys: floor_ind"
        ):
            await api.async_get_floors()


class TestAPIRooms:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_rooms(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "room_list": [
                {"room_ind": 5, "name": "Living Room", "floor_ind": 1},
                {"room_ind": 6, "name": "Kitchen", "floor_ind": 1},
            ],
            "cmd_name": "room_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        rooms = await api.async_get_rooms()
        assert len(rooms) == 2
        assert isinstance(rooms[0], Room)
        assert isinstance(rooms[1], Room)
        assert rooms[0].id == 5
        assert rooms[0].name == "Living Room"
        assert rooms[0].floor_id == 1
        assert rooms[1].id == 6
        assert rooms[1].name == "Kitchen"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_rooms_empty(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "room_list": [],
            "cmd_name": "room_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        rooms = await api.async_get_rooms()
        assert len(rooms) == 0
        assert isinstance(rooms, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_rooms_missing_key(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            # "room_list" key is missing
            "cmd_name": "room_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        rooms = await api.async_get_rooms()
        assert len(rooms) == 0
        assert isinstance(rooms, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_rooms_malformed_data(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "room_list": [
                {"name": "Living Room", "floor_ind": 1},  # Missing room_ind
            ],
            "cmd_name": "room_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: room_ind"):
            await api.async_get_rooms()


class TestAPILights:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_lights(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = LIGHT_LIST_RESP

        lights = await api.async_get_lights()
        assert len(lights) == len(LIGHT_LIST_RESP["array"])
        assert isinstance(lights[0], Light)
        assert isinstance(lights[1], Light)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_lights_empty_array(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],  # Empty array
            "cmd_name": "light_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        lights = await api.async_get_lights()
        assert len(lights) == 0
        assert isinstance(lights, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_lights_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            # "array" key is missing
            "cmd_name": "light_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        lights = await api.async_get_lights()
        assert len(lights) == 0
        assert isinstance(lights, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_lights_missing_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    # Missing "act_id"
                    "floor_ind": 19,
                    "name": "light_ChQQs",
                    "room_ind": 23,
                    "status": 1,
                    "type": "STEP_STEP",
                }
            ],
            "cmd_name": "light_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            await api.async_get_lights()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_lights_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 1,
                    "floor_ind": 19,
                    # Missing "name"
                    "room_ind": 23,
                    "status": 1,
                    "type": "STEP_STEP",
                }
            ],
            "cmd_name": "light_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_lights()


class TestAPIOpenings:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "open_act_id": 1,
                    "close_act_id": 2,
                    "floor_ind": 19,
                    "name": "opening_ChQQs",
                    "room_ind": 23,
                    "status": 0,
                    "type": 0,
                },
                {
                    "open_act_id": 3,
                    "close_act_id": 4,
                    "floor_ind": 19,
                    "name": "opening_vdAEA",
                    "room_ind": 23,
                    "status": 1,
                    "type": 0,
                },
                {
                    "open_act_id": 5,
                    "close_act_id": 6,
                    "floor_ind": 19,
                    "name": "opening_onbFB",
                    "room_ind": 23,
                    "status": 2,
                    "type": 0,
                    "partial": ["20%", "50%", "80%"],
                },
            ],
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        openings = await api.async_get_openings()
        assert len(openings) == 3
        assert isinstance(openings[0], Opening)
        assert isinstance(openings[1], Opening)
        assert isinstance(openings[2], Opening)
        # Check properties of first opening
        assert openings[0].name == "opening_ChQQs"
        assert openings[0].open_act_id == 1
        assert openings[0].close_act_id == 2
        assert openings[0].status.value == 0  # STOPPED
        assert openings[0].type.value == 0  # SHUTTER

        # Check properties of second opening
        assert openings[1].name == "opening_vdAEA"
        assert openings[1].status.value == 1  # OPENING

        # Check properties of third opening with partial positions
        assert openings[2].name == "opening_onbFB"
        assert openings[2].status.value == 2  # CLOSING
        assert openings[2].partial_positions == ["20%", "50%", "80%"]

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],  # Empty array
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        openings = await api.async_get_openings()
        assert len(openings) == 0
        assert isinstance(openings, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            # "array" key is missing
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        openings = await api.async_get_openings()
        assert len(openings) == 0
        assert isinstance(openings, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_missing_open_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    # Missing "open_act_id"
                    "close_act_id": 2,
                    "floor_ind": 19,
                    "name": "opening_ChQQs",
                    "room_ind": 23,
                    "status": 0,
                    "type": 0,
                }
            ],
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(
            ValueError, match="Data is missing required keys: open_act_id"
        ):
            await api.async_get_openings()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_missing_close_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "open_act_id": 1,
                    # Missing "close_act_id"
                    "floor_ind": 19,
                    "name": "opening_ChQQs",
                    "room_ind": 23,
                    "status": 0,
                    "type": 0,
                }
            ],
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(
            ValueError, match="Data is missing required keys: close_act_id"
        ):
            await api.async_get_openings()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "open_act_id": 1,
                    "close_act_id": 2,
                    "floor_ind": 19,
                    # Missing "name"
                    "room_ind": 23,
                    "status": 0,
                    "type": 0,
                }
            ],
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_openings()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_openings_unknown_enums(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "open_act_id": 1,
                    "close_act_id": 2,
                    "floor_ind": 19,
                    "name": "opening_ChQQs",
                    "room_ind": 23,
                    "status": 99,  # Unknown status value
                    "type": 99,  # Unknown type value
                }
            ],
            "cmd_name": "openings_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        # Should not raise an exception, but instead return UNKNOWN enum values
        openings = await api.async_get_openings()
        assert len(openings) == 1
        assert openings[0].status.value == -1  # OpeningStatus.UNKNOWN
        assert openings[0].type.value == -1  # OpeningType.UNKNOWN


class TestAPIScenarios:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_scenarios(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = SCENARIOS_LIST_RESP

        scenarios = await api.async_get_scenarios()
        assert len(scenarios) == len(SCENARIOS_LIST_RESP["array"])
        assert isinstance(scenarios[0], Scenario)
        assert isinstance(scenarios[1], Scenario)
        assert isinstance(scenarios[2], Scenario)
        # Check properties of first scenario
        assert scenarios[0].name == "scenario_SGgbR"
        assert scenarios[0].id == 0
        assert scenarios[1].name == "scenario_OjEUl"
        assert scenarios[1].id == 1

    @patch.object(Auth, "async_send_command")
    async def test_async_get_scenarios_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "scenarios_list_resp",
            "cseq": 2,
            "sl_data_ack_reason": 0,
        }

        scenarios = await api.async_get_scenarios()
        assert len(scenarios) == 0
        assert isinstance(scenarios, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_scenarios_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            # "array" key is missing
            "cmd_name": "scenarios_list_resp",
            "cseq": 2,
            "sl_data_ack_reason": 0,
        }

        scenarios = await api.async_get_scenarios()
        assert len(scenarios) == 0
        assert isinstance(scenarios, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_scenarios_missing_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    # Missing "id"
                    "icon_id": 14,
                    "name": "scenario_SGgbR",
                    "scenario_status": 0,
                    "status": 0,
                    "user-defined": 0,
                }
            ],
            "cmd_name": "scenarios_list_resp",
            "cseq": 2,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            await api.async_get_scenarios()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_scenarios_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "icon_id": 14,
                    "id": 0,
                    # Missing "name"
                    "scenario_status": 0,
                    "status": 0,
                    "user-defined": 0,
                }
            ],
            "cmd_name": "scenarios_list_resp",
            "cseq": 2,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_scenarios()


class TestAPIUpdates:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_updates_success(self, mock_send_command, auth_instance):
        """Test successful retrieval of status updates."""
        api = CameDomoticAPI(auth_instance)

        mock_response_data = {
            "update_list": [
                {
                    "device_id": 1,
                    "status": "on",
                    "timestamp": "2024-01-01T12:00:00Z",
                },
                {
                    "device_id": 2,
                    "status": "off",
                    "timestamp": "2024-01-01T12:01:00Z",
                },
            ]
        }

        mock_send_command.return_value = mock_response_data

        result = await api.async_get_updates()

        assert isinstance(result, UpdateList)
        mock_send_command.assert_called_once()
        _, kwargs = mock_send_command.call_args
        assert kwargs["timeout"] == 120

    @patch.object(Auth, "async_send_command")
    async def test_async_get_updates_custom_timeout(
        self, mock_send_command, auth_instance
    ):
        """Test that a custom timeout is passed to async_send_command."""
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {}

        await api.async_get_updates(timeout=60)

        _, kwargs = mock_send_command.call_args
        assert kwargs["timeout"] == 60

    @patch.object(
        Auth,
        "async_get_valid_client_id",
        side_effect=CameDomoticAuthError("Auth failed"),
    )
    async def test_async_get_updates_auth_error(
        self, mock_get_client_id, auth_instance
    ):
        """Test async_get_updates when authentication fails."""
        api = CameDomoticAPI(auth_instance)

        with pytest.raises(CameDomoticAuthError, match="Auth failed"):
            await api.async_get_updates()

    @patch.object(Auth, "async_get_valid_client_id", return_value="test_client_id")
    @patch.object(
        Auth,
        "async_send_command",
        side_effect=CameDomoticServerError("Server error"),
    )
    async def test_async_get_updates_server_error(
        self, mock_send_command, mock_get_client_id, auth_instance
    ):
        """Test async_get_updates when server returns an error."""
        api = CameDomoticAPI(auth_instance)

        with pytest.raises(CameDomoticServerError, match="Server error"):
            await api.async_get_updates()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock, return_value={})
    async def test_async_get_updates_empty_response(
        self, mock_send_command, auth_instance
    ):
        """Test async_get_updates with empty server response."""
        api = CameDomoticAPI(auth_instance)

        result = await api.async_get_updates()

        assert isinstance(result, UpdateList)
        assert result.data == []


class TestAPIThermoZones:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = THERMO_LIST_RESP

        zones = await api.async_get_thermo_zones()
        assert len(zones) == len(THERMO_LIST_RESP["array"])
        assert isinstance(zones[0], ThermoZone)
        assert isinstance(zones[1], ThermoZone)
        assert zones[0].act_id == 1
        assert zones[0].name == "Room 1"
        assert zones[0].temperature == 20.0
        assert zones[0].set_point == 34.8
        assert zones[0].mode.name == "AUTO"
        assert zones[0].season.name == "WINTER"
        assert zones[1].act_id == 52
        assert zones[1].name == "Room 2"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        zones = await api.async_get_thermo_zones()
        assert len(zones) == 0
        assert isinstance(zones, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        zones = await api.async_get_thermo_zones()
        assert len(zones) == 0
        assert isinstance(zones, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones_missing_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "name": "Zone Without ID",
                    "floor_ind": 37,
                    "room_ind": 57,
                    "status": 0,
                    "temp": 200,
                    "mode": 2,
                    "season": "winter",
                }
            ],
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            await api.async_get_thermo_zones()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 1,
                    "floor_ind": 37,
                    "room_ind": 57,
                    "status": 0,
                    "temp": 200,
                    "mode": 2,
                    "season": "winter",
                }
            ],
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_thermo_zones()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_thermo_zones_unknown_enums(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 1,
                    "name": "Unknown Zone",
                    "status": 0,
                    "temp": 200,
                    "mode": 99,
                    "season": "nonexistent",
                }
            ],
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        zones = await api.async_get_thermo_zones()
        assert len(zones) == 1
        assert (
            zones[0].mode
            == ThermoZone({"act_id": 1, "name": "x", "mode": 99}, auth_instance).mode
        )
        assert zones[0].mode.value == -1
        assert zones[0].season.value == "unknown"


class TestAPIAnalogSensors:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_analog_sensors(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "array": [],
            "sl_data_ack_reason": 0,
            "temperature": {
                "name": "Outdoor Temp",
                "value": 215,
                "unit": "\u00b0C",
                "act_id": 100,
            },
            "humidity": {
                "name": "Indoor Humidity",
                "value": 55,
                "unit": "%",
                "act_id": 101,
            },
            "pressure": {
                "name": "Barometric Pressure",
                "value": 1013,
                "unit": "hPa",
                "act_id": 102,
            },
        }

        sensors = await api.async_get_analog_sensors()
        assert len(sensors) == 3
        assert isinstance(sensors[0], AnalogSensor)
        assert sensors[0].name == "Outdoor Temp"
        assert sensors[0].value == 21.5
        assert sensors[0].unit == "\u00b0C"
        assert sensors[1].name == "Indoor Humidity"
        assert sensors[1].value == 55.0
        assert sensors[2].name == "Barometric Pressure"
        assert sensors[2].value == 1013.0

    @patch.object(Auth, "async_send_command")
    async def test_async_get_analog_sensors_partial(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "array": [],
            "sl_data_ack_reason": 0,
            "temperature": {
                "name": "Outdoor Temp",
                "value": 215,
                "unit": "\u00b0C",
                "act_id": 100,
            },
        }

        sensors = await api.async_get_analog_sensors()
        assert len(sensors) == 1
        assert sensors[0].name == "Outdoor Temp"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_analog_sensors_none_present(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "array": [],
            "sl_data_ack_reason": 0,
        }

        sensors = await api.async_get_analog_sensors()
        assert len(sensors) == 0
        assert isinstance(sensors, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_analog_sensors_missing_required_field(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "thermo_list_resp",
            "cseq": 1,
            "array": [],
            "sl_data_ack_reason": 0,
            "temperature": {
                "value": 215,
                "unit": "\u00b0C",
                "act_id": 100,
            },
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_analog_sensors()
