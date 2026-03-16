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
from aiocamedomotic.const import _DEFAULT_COMMAND_TIMEOUT
from aiocamedomotic.errors import (
    CameDomoticAuthError,
    CameDomoticError,
    CameDomoticServerError,
    CameDomoticServerNotFoundError,
    CameDomoticServerTimeoutError,
)
from aiocamedomotic.models import (
    AnalogSensor,
    AnalogSensorType,
    Camera,
    DigitalInput,
    Floor,
    Light,
    Opening,
    PlantTopology,
    Relay,
    Room,
    Scenario,
    ServerInfo,
    TerminalGroup,
    ThermoZone,
    ThermoZoneSeason,
    UpdateList,
    User,
)
from tests.aiocamedomotic.mocked_responses import (
    DIGITALIN_LIST_RESP,
    FEATURE_LIST_RESP,
    LIGHT_LIST_RESP,
    SCENARIOS_LIST_RESP,
    THERMO_LIST_RESP,
    TVCC_CAMERAS_LIST_RESP,
)


class TestAPIInit:
    async def test_init(self, auth_instance):
        api = CameDomoticAPI(auth_instance)
        assert api.auth == auth_instance
        assert api.auth.command_timeout == _DEFAULT_COMMAND_TIMEOUT

    async def test_init_custom_command_timeout(self, auth_instance):
        api = CameDomoticAPI(auth_instance, command_timeout=15)
        assert api.auth.command_timeout == 15

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
            command_timeout=_DEFAULT_COMMAND_TIMEOUT,
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

    @patch.object(Auth, "async_send_command")
    async def test_async_get_terminal_groups(self, mock_send_command, auth_instance):
        mock_send_command.return_value = {
            "cseq": 1,
            "cmd_name": "terminals_groups_list_resp",
            "array": [
                {"group_name": "ETI/Domo", "group_id": 1},
                {"group_name": "group2", "group_id": 2},
            ],
            "sl_data_ack_reason": 0,
        }
        api = CameDomoticAPI(auth_instance)

        groups = await api.async_get_terminal_groups()

        assert len(groups) == 2
        assert isinstance(groups[0], TerminalGroup)
        assert groups[0].name == "ETI/Domo"
        assert groups[0].id == 1
        assert groups[1].name == "group2"
        assert groups[1].id == 2
        mock_send_command.assert_called_once_with(
            {"cmd_name": "terminals_groups_list_req"},
            response_command="terminals_groups_list_resp",
        )

    @patch.object(Auth, "async_send_command")
    async def test_async_get_terminal_groups_empty_array(
        self, mock_send_command, auth_instance
    ):
        mock_send_command.return_value = {
            "cseq": 1,
            "cmd_name": "terminals_groups_list_resp",
            "array": [],
            "sl_data_ack_reason": 0,
        }
        api = CameDomoticAPI(auth_instance)

        groups = await api.async_get_terminal_groups()

        assert groups == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_terminal_groups_missing_key(
        self, mock_send_command, auth_instance
    ):
        mock_send_command.return_value = {
            "cseq": 1,
            "cmd_name": "terminals_groups_list_resp",
            "sl_data_ack_reason": 0,
        }
        api = CameDomoticAPI(auth_instance)

        groups = await api.async_get_terminal_groups()

        assert groups == []

    @patch.object(Auth, "async_send_command")
    async def test_async_add_user(self, mock_send_command, auth_instance):
        mock_send_command.return_value = {
            "sl_cmd": "sl_add_user_ack",
            "sl_data_ack_reason": 0,
        }
        api = CameDomoticAPI(auth_instance)

        user = await api.async_add_user("new_user", "new_password", group="new_group")

        assert isinstance(user, User)
        assert user.name == "new_user"
        mock_send_command.assert_called_once_with(
            {},
            command_type="sl_add_user_req",
            additional_payload={
                "sl_login": "new_user",
                "sl_pwd": "new_password",
                "sl_group": "new_group",
            },
        )

    @patch.object(Auth, "async_send_command")
    async def test_async_add_user_default_group(self, mock_send_command, auth_instance):
        mock_send_command.return_value = {
            "sl_cmd": "sl_add_user_ack",
            "sl_data_ack_reason": 0,
        }
        api = CameDomoticAPI(auth_instance)

        await api.async_add_user("new_user", "new_password")

        mock_send_command.assert_called_once_with(
            {},
            command_type="sl_add_user_req",
            additional_payload={
                "sl_login": "new_user",
                "sl_pwd": "new_password",
                "sl_group": "*",
            },
        )


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
    async def test_async_get_lights_null_array(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "light_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        lights = await api.async_get_lights()
        assert lights == []

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


class TestAPIRelays:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 31,
                    "floor_ind": 2,
                    "name": "relay_Garden",
                    "room_ind": 3,
                    "status": 1,
                },
                {
                    "act_id": 32,
                    "floor_ind": 1,
                    "name": "relay_Gate",
                    "room_ind": 4,
                    "status": 0,
                },
            ],
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        relays = await api.async_get_relays()
        assert len(relays) == 2
        assert isinstance(relays[0], Relay)
        assert isinstance(relays[1], Relay)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays_empty_array(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        relays = await api.async_get_relays()
        assert len(relays) == 0
        assert isinstance(relays, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        relays = await api.async_get_relays()
        assert len(relays) == 0
        assert isinstance(relays, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays_null_array(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        relays = await api.async_get_relays()
        assert relays == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays_missing_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "floor_ind": 2,
                    "name": "relay_Garden",
                    "room_ind": 3,
                    "status": 1,
                }
            ],
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            await api.async_get_relays()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_relays_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 31,
                    "floor_ind": 2,
                    "room_ind": 3,
                    "status": 1,
                }
            ],
            "cmd_name": "relays_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_relays()


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
        assert kwargs["timeout"] is None

    @patch.object(Auth, "async_send_command")
    async def test_async_get_updates_custom_timeout(
        self, mock_send_command, auth_instance
    ):
        """Test that a custom timeout is passed to async_send_command."""
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {}

        await api.async_get_updates(timeout=120)

        _, kwargs = mock_send_command.call_args
        assert kwargs["timeout"] == 120

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
                "unit": "C",
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
        assert sensors[0].unit == "C"
        assert sensors[0].sensor_type == AnalogSensorType.TEMPERATURE
        assert sensors[1].name == "Indoor Humidity"
        assert sensors[1].value == 55.0
        assert sensors[1].sensor_type == AnalogSensorType.HUMIDITY
        assert sensors[2].name == "Barometric Pressure"
        assert sensors[2].value == 1013.0
        assert sensors[2].sensor_type == AnalogSensorType.PRESSURE

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
                "unit": "C",
                "act_id": 100,
            },
        }

        sensors = await api.async_get_analog_sensors()
        assert len(sensors) == 1
        assert sensors[0].name == "Outdoor Temp"
        assert sensors[0].sensor_type == AnalogSensorType.TEMPERATURE

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
                "unit": "C",
                "act_id": 100,
            },
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_analog_sensors()


class TestAPIDigitalInputs:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = DIGITALIN_LIST_RESP

        digital_inputs = await api.async_get_digital_inputs()
        assert len(digital_inputs) == len(DIGITALIN_LIST_RESP["array"])
        assert isinstance(digital_inputs[0], DigitalInput)
        assert isinstance(digital_inputs[1], DigitalInput)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "digitalin_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        digital_inputs = await api.async_get_digital_inputs()
        assert len(digital_inputs) == 0
        assert isinstance(digital_inputs, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "digitalin_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        digital_inputs = await api.async_get_digital_inputs()
        assert len(digital_inputs) == 0
        assert isinstance(digital_inputs, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs_null_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "digitalin_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        digital_inputs = await api.async_get_digital_inputs()
        assert digital_inputs == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs_missing_act_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "name": "digitalin_test",
                    "type": 1,
                    "addr": 200,
                }
            ],
            "cmd_name": "digitalin_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            await api.async_get_digital_inputs()

    @patch.object(Auth, "async_send_command")
    async def test_async_get_digital_inputs_missing_name(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [
                {
                    "act_id": 0,
                    "type": 1,
                    "addr": 200,
                }
            ],
            "cmd_name": "digitalin_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            await api.async_get_digital_inputs()


class TestAPICameras:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_cameras(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = TVCC_CAMERAS_LIST_RESP

        cameras = await api.async_get_cameras()
        assert len(cameras) == len(TVCC_CAMERAS_LIST_RESP["array"])
        assert isinstance(cameras[0], Camera)
        assert isinstance(cameras[1], Camera)

        # Verify the payload includes username
        call_args = mock_send_command.call_args
        payload = call_args[0][0]
        assert "username" in payload

    @patch.object(Auth, "async_send_command")
    async def test_async_get_cameras_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "tvcc_cameras_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        cameras = await api.async_get_cameras()
        assert len(cameras) == 0
        assert isinstance(cameras, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_cameras_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "tvcc_cameras_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        cameras = await api.async_get_cameras()
        assert len(cameras) == 0
        assert isinstance(cameras, list)

    @patch.object(Auth, "async_send_command")
    async def test_async_get_cameras_null_array(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "tvcc_cameras_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        cameras = await api.async_get_cameras()
        assert cameras == []


class TestAPIThermoSeason:
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_thermo_season_winter(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        await api.async_set_thermo_season(ThermoZoneSeason.WINTER)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["cmd_name"] == "thermo_season_req"
        assert call_payload["season"] == "winter"

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_thermo_season_summer(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        await api.async_set_thermo_season(ThermoZoneSeason.SUMMER)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["season"] == "summer"

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_thermo_season_plant_off(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        await api.async_set_thermo_season(ThermoZoneSeason.PLANT_OFF)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["season"] == "plant_off"

    async def test_async_set_thermo_season_unknown_raises(self, auth_instance):
        api = CameDomoticAPI(auth_instance)
        with pytest.raises(ValueError, match="Cannot set season to UNKNOWN"):
            await api.async_set_thermo_season(ThermoZoneSeason.UNKNOWN)


class TestAPIPing:
    """Tests for the async_ping method."""

    @patch.object(Auth, "async_keep_alive", new_callable=AsyncMock)
    async def test_async_ping_returns_latency(self, mock_keep_alive, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_keep_alive.return_value = None

        latency = await api.async_ping()

        assert isinstance(latency, float)
        assert latency >= 0
        mock_keep_alive.assert_called_once()

    @patch.object(Auth, "async_keep_alive", new_callable=AsyncMock)
    async def test_async_ping_server_not_found(self, mock_keep_alive, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_keep_alive.side_effect = CameDomoticServerNotFoundError("unreachable")

        with pytest.raises(CameDomoticServerNotFoundError):
            await api.async_ping()

    @patch.object(Auth, "async_keep_alive", new_callable=AsyncMock)
    async def test_async_ping_auth_error(self, mock_keep_alive, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_keep_alive.side_effect = CameDomoticAuthError("auth failed")

        with pytest.raises(CameDomoticAuthError):
            await api.async_ping()

    @patch.object(Auth, "async_keep_alive", new_callable=AsyncMock)
    async def test_async_ping_timeout(self, mock_keep_alive, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_keep_alive.side_effect = CameDomoticServerTimeoutError("timeout")

        with pytest.raises(CameDomoticServerTimeoutError):
            await api.async_ping()


# region Topology test data

_NESTED_LIGHTS_RESP = {
    "cseq": 1,
    "cmd_name": "light_list_resp",
    "array": [
        {
            "name": "Ground Floor",
            "floor_ind": 1,
            "status": 0,
            "array": [
                {
                    "name": "Kitchen",
                    "room_ind": 10,
                    "status": 0,
                    "array": [
                        {
                            "act_id": 100,
                            "name": "Ceiling light",
                            "floor_ind": 1,
                            "room_ind": 10,
                            "status": 0,
                            "type": "STEP_STEP",
                            "leaf": True,
                        }
                    ],
                },
                {
                    "name": "Living Room",
                    "room_ind": 11,
                    "status": 0,
                    "array": [
                        {
                            "act_id": 101,
                            "name": "Wall light",
                            "floor_ind": 1,
                            "room_ind": 11,
                            "status": 0,
                            "type": "DIMMER",
                            "perc": 50,
                            "leaf": True,
                        }
                    ],
                },
            ],
        },
        {
            "name": "First Floor",
            "floor_ind": 2,
            "status": 0,
            "array": [
                {
                    "name": "Bedroom",
                    "room_ind": 20,
                    "status": 0,
                    "array": [
                        {
                            "act_id": 200,
                            "name": "Bedside lamp",
                            "floor_ind": 2,
                            "room_ind": 20,
                            "status": 0,
                            "type": "STEP_STEP",
                            "leaf": True,
                        }
                    ],
                },
            ],
        },
    ],
    "sl_data_ack_reason": 0,
}

_NESTED_OPENINGS_RESP = {
    "cseq": 1,
    "cmd_name": "openings_list_resp",
    "array": [
        {
            "name": "Ground Floor",
            "floor_ind": 1,
            "status": 0,
            "array": [
                {
                    "name": "Kitchen",
                    "room_ind": 10,
                    "status": 0,
                    "array": [
                        {
                            "open_act_id": 300,
                            "close_act_id": 301,
                            "name": "Kitchen shutter",
                            "floor_ind": 1,
                            "room_ind": 10,
                            "status": 0,
                            "type": 0,
                            "leaf": True,
                        }
                    ],
                },
                {
                    "name": "Hallway",
                    "room_ind": 12,
                    "status": 0,
                    "array": [
                        {
                            "open_act_id": 302,
                            "close_act_id": 303,
                            "name": "Front door",
                            "floor_ind": 1,
                            "room_ind": 12,
                            "status": 0,
                            "type": 0,
                            "leaf": True,
                        }
                    ],
                },
            ],
        },
    ],
    "sl_data_ack_reason": 0,
}

_NESTED_THERMO_RESP = {
    "cseq": 1,
    "cmd_name": "thermo_list_resp",
    "array": [
        {
            "name": "First Floor",
            "floor_ind": 2,
            "array": [
                {
                    "act_id": 400,
                    "name": "Bedroom thermostat",
                    "floor_ind": 2,
                    "room_ind": 20,
                    "status": 0,
                    "temp": 210,
                    "leaf": True,
                },
                {
                    "act_id": 401,
                    "name": "Bathroom thermostat",
                    "floor_ind": 2,
                    "room_ind": 21,
                    "status": 0,
                    "temp": 220,
                    "leaf": True,
                },
            ],
        },
    ],
    "sl_data_ack_reason": 0,
}

_SERVER_INFO_ALL_FEATURES = ServerInfo(
    keycode="0000FFFF9999AAAA",
    serial="0011ffee",
    features=["lights", "openings", "thermoregulation", "scenarios"],
)

_SERVER_INFO_LIGHTS_ONLY = ServerInfo(
    keycode="0000FFFF9999AAAA",
    serial="0011ffee",
    features=["lights"],
)

_SERVER_INFO_THERMO_ONLY = ServerInfo(
    keycode="0000FFFF9999AAAA",
    serial="0011ffee",
    features=["thermoregulation"],
)

_SERVER_INFO_NO_NESTED_FEATURES = ServerInfo(
    keycode="0000FFFF9999AAAA",
    serial="0011ffee",
    features=["scenarios", "digitalin"],
)

# endregion


class TestAPITopology:
    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_all_sources_merged(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_ALL_FEATURES
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []
        mock_send_command.side_effect = [
            _NESTED_LIGHTS_RESP,
            _NESTED_OPENINGS_RESP,
            _NESTED_THERMO_RESP,
        ]

        topology = await api.async_get_topology()

        assert isinstance(topology, PlantTopology)
        assert len(topology.floors) == 2

        gf = topology.floors[0]
        assert gf.id == 1
        assert gf.name == "Ground Floor"
        assert len(gf.rooms) == 3
        room_names = {r.name for r in gf.rooms}
        assert room_names == {"Kitchen", "Living Room", "Hallway"}

        ff = topology.floors[1]
        assert ff.id == 2
        assert ff.name == "First Floor"
        assert len(ff.rooms) == 2
        room_ids = {r.id for r in ff.rooms}
        assert room_ids == {20, 21}

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_flat_endpoints_provide_data(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_NO_NESTED_FEATURES
        mock_get_floors.return_value = [
            Floor({"floor_ind": 1, "name": "Piano Terra"}),
        ]
        mock_get_rooms.return_value = [
            Room({"room_ind": 10, "name": "Cucina", "floor_ind": 1}),
        ]

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        assert topology.floors[0].name == "Piano Terra"
        assert len(topology.floors[0].rooms) == 1
        assert topology.floors[0].rooms[0].name == "Cucina"

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_flat_empty_nested_provide_data(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_LIGHTS_ONLY
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []
        mock_send_command.return_value = _NESTED_LIGHTS_RESP

        topology = await api.async_get_topology()

        assert len(topology.floors) == 2
        assert topology.floors[0].name == "Ground Floor"
        assert topology.floors[1].name == "First Floor"
        room_names = [r.name for f in topology.floors for r in f.rooms]
        assert "Kitchen" in room_names
        assert "Living Room" in room_names
        assert "Bedroom" in room_names

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_thermo_only_room_names_fallback(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_THERMO_ONLY
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []
        mock_send_command.return_value = _NESTED_THERMO_RESP

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        ff = topology.floors[0]
        assert ff.id == 2
        assert ff.name == "First Floor"
        assert len(ff.rooms) == 2
        # Room names should be fallback since thermo doesn't provide them
        room_names = {r.name for r in ff.rooms}
        assert room_names == {"Room 20", "Room 21"}

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_thermo_plus_lights_rooms_get_names(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = ServerInfo(
            keycode="0000FFFF9999AAAA",
            serial="0011ffee",
            features=["lights", "thermoregulation"],
        )
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []
        mock_send_command.side_effect = [
            _NESTED_LIGHTS_RESP,
            _NESTED_THERMO_RESP,
        ]

        topology = await api.async_get_topology()

        ff = next(f for f in topology.floors if f.id == 2)
        room_map = {r.id: r.name for r in ff.rooms}
        # room_ind 20 should get "Bedroom" from lights, not fallback
        assert room_map[20] == "Bedroom"
        # room_ind 21 only exists in thermo, should get fallback
        assert room_map[21] == "Room 21"

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_all_empty_returns_empty_topology(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_NO_NESTED_FEATURES
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []

        topology = await api.async_get_topology()

        assert isinstance(topology, PlantTopology)
        assert topology.floors == []

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_nested_command_failure_graceful_degradation(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_ALL_FEATURES
        mock_get_floors.return_value = [
            Floor({"floor_ind": 1, "name": "Ground Floor"}),
        ]
        mock_get_rooms.return_value = [
            Room({"room_ind": 10, "name": "Kitchen", "floor_ind": 1}),
        ]
        # All nested commands fail
        mock_send_command.side_effect = CameDomoticServerError("server error")

        topology = await api.async_get_topology()

        # Should still have data from flat endpoints
        assert len(topology.floors) == 1
        assert topology.floors[0].name == "Ground Floor"
        assert len(topology.floors[0].rooms) == 1
        assert topology.floors[0].rooms[0].name == "Kitchen"

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_no_nested_features_flat_only(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_NO_NESTED_FEATURES
        mock_get_floors.return_value = [
            Floor({"floor_ind": 5, "name": "Basement"}),
        ]
        mock_get_rooms.return_value = [
            Room({"room_ind": 50, "name": "Storage", "floor_ind": 5}),
            Room({"room_ind": 51, "name": "Laundry", "floor_ind": 5}),
        ]

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        assert topology.floors[0].name == "Basement"
        assert len(topology.floors[0].rooms) == 2
        room_names = {r.name for r in topology.floors[0].rooms}
        assert room_names == {"Storage", "Laundry"}

    # --- Server info error handling ---

    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_server_info_auth_error_propagates(
        self,
        mock_server_info,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.side_effect = CameDomoticAuthError("auth failed")

        with pytest.raises(CameDomoticAuthError):
            await api.async_get_topology()

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_server_info_generic_error_skips_nested(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.side_effect = RuntimeError("unexpected")
        mock_get_floors.return_value = [
            Floor({"floor_ind": 1, "name": "Ground Floor"}),
        ]
        mock_get_rooms.return_value = [
            Room({"room_ind": 10, "name": "Kitchen", "floor_ind": 1}),
        ]

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        assert topology.floors[0].name == "Ground Floor"
        assert len(topology.floors[0].rooms) == 1
        assert topology.floors[0].rooms[0].name == "Kitchen"

    # --- Unknown feature string ---

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(Auth, "async_send_command")
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_unknown_feature_string_silently_skipped(
        self,
        mock_server_info,
        mock_send_command,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = ServerInfo(
            keycode="0000FFFF9999AAAA",
            serial="0011ffee",
            features=["lights", "unknown_xyz"],
        )
        mock_get_floors.return_value = []
        mock_get_rooms.return_value = []
        mock_send_command.return_value = _NESTED_LIGHTS_RESP

        topology = await api.async_get_topology()

        assert len(topology.floors) == 2
        mock_send_command.assert_called_once()

    # --- Flat endpoint failures ---

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_flat_floors_failure_graceful(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_NO_NESTED_FEATURES
        mock_get_floors.side_effect = CameDomoticServerError("floors error")
        mock_get_rooms.return_value = [
            Room({"room_ind": 10, "name": "Kitchen", "floor_ind": 1}),
        ]

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        assert topology.floors[0].id == 1
        assert topology.floors[0].rooms[0].name == "Kitchen"

    @patch.object(CameDomoticAPI, "async_get_rooms", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_floors", new_callable=AsyncMock)
    @patch.object(CameDomoticAPI, "async_get_server_info", new_callable=AsyncMock)
    async def test_flat_rooms_failure_graceful(
        self,
        mock_server_info,
        mock_get_floors,
        mock_get_rooms,
        auth_instance,
    ):
        api = CameDomoticAPI(auth_instance)
        mock_server_info.return_value = _SERVER_INFO_NO_NESTED_FEATURES
        mock_get_floors.return_value = [
            Floor({"floor_ind": 1, "name": "Ground Floor"}),
        ]
        mock_get_rooms.side_effect = CameDomoticServerError("rooms error")

        topology = await api.async_get_topology()

        assert len(topology.floors) == 1
        assert topology.floors[0].name == "Ground Floor"
        assert topology.floors[0].rooms == []

    # --- _parse_nested_3level edge cases ---

    def test_parse_nested_3level_leaf_at_floor_level(self):
        response = {
            "array": [
                {"leaf": True, "name": "Stray device", "floor_ind": 99},
                {
                    "name": "Floor 1",
                    "floor_ind": 1,
                    "array": [
                        {"name": "Room A", "room_ind": 10, "array": []},
                    ],
                },
            ]
        }

        floors, rooms = CameDomoticAPI._parse_nested_3level(response)

        assert 99 not in floors
        assert floors == {1: "Floor 1"}
        assert rooms == {(1, 10): "Room A"}

    def test_parse_nested_3level_missing_floor_ind(self):
        response = {
            "array": [
                {
                    "name": "No Index Floor",
                    "array": [
                        {"name": "Room X", "room_ind": 10, "array": []},
                    ],
                },
                {"name": "Good Floor", "floor_ind": 2, "array": []},
            ]
        }

        floors, rooms = CameDomoticAPI._parse_nested_3level(response)

        assert floors == {2: "Good Floor"}
        assert rooms == {}

    def test_parse_nested_3level_leaf_at_room_level(self):
        response = {
            "array": [
                {
                    "name": "Floor 1",
                    "floor_ind": 1,
                    "array": [
                        {"leaf": True, "name": "Stray device", "room_ind": 77},
                        {"name": "Real Room", "room_ind": 10, "array": []},
                    ],
                },
            ]
        }

        floors, rooms = CameDomoticAPI._parse_nested_3level(response)

        assert floors == {1: "Floor 1"}
        assert (1, 77) not in rooms
        assert rooms == {(1, 10): "Real Room"}

    # --- _parse_nested_2level edge cases ---

    def test_parse_nested_2level_leaf_at_floor_level(self):
        response = {
            "array": [
                {"leaf": True, "floor_ind": 99, "name": "Stray"},
                {
                    "name": "Floor 1",
                    "floor_ind": 1,
                    "array": [
                        {"room_ind": 10, "floor_ind": 1, "leaf": True},
                    ],
                },
            ]
        }

        floors, rooms = CameDomoticAPI._parse_nested_2level(response)

        assert 99 not in floors
        assert floors == {1: "Floor 1"}
        assert rooms == {(1, 10): ""}

    def test_parse_nested_2level_missing_floor_ind(self):
        response = {
            "array": [
                {
                    "name": "No Index",
                    "array": [
                        {"room_ind": 10, "floor_ind": 1, "leaf": True},
                    ],
                },
                {"name": "Good Floor", "floor_ind": 2, "array": []},
            ]
        }

        floors, rooms = CameDomoticAPI._parse_nested_2level(response)

        assert floors == {2: "Good Floor"}
        assert rooms == {}
