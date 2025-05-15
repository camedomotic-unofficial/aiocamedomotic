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
# flake8: noqa: F811

from unittest.mock import AsyncMock, patch
import pytest

# from .mocked_responses import SL_USERS_LIST_RESP
from aiocamedomotic import Auth, CameDomoticAPI
from aiocamedomotic.models import (
    ServerInfo,
    User,
    Light,
    Opening,
)
from aiocamedomotic.errors import (
    CameDomoticServerNotFoundError,
    CameDomoticError,
)


from tests.aiocamedomotic.const import (
    auth_instance,  # noqa: F401, pylint: disable=unused-import
    auth_instance_not_logged_in,  # noqa: F401, pylint: disable=unused-import
)


# region basic tests
async def test_init(auth_instance):
    api = CameDomoticAPI(auth_instance)
    assert api.auth == auth_instance


@patch.object(Auth, "async_dispose")
async def test_aexit_calls_async_dispose(mock_async_dispose, auth_instance):
    api = CameDomoticAPI(auth_instance)
    await api.__aexit__(None, None, None)
    mock_async_dispose.assert_called_once()


@patch.object(Auth, "async_dispose")
async def test_aexit_no_exceptions(mock_async_dispose, auth_instance):
    mock_async_dispose.side_effect = CameDomoticError("error")
    api = CameDomoticAPI(auth_instance)
    try:
        await api.__aexit__(None, None, None)
    except Exception as e:  # pylint: disable=broad-except
        pytest.fail(f"__aexit__ raised an exception: {e}")


@patch.object(Auth, "async_dispose")
async def test_async_dispose_disposes_auth(mock_async_dispose, auth_instance):
    api = CameDomoticAPI(auth_instance)
    await api.async_dispose()
    mock_async_dispose.assert_called_once()


@patch.object(Auth, "async_dispose")
async def test_async_dispose_no_exceptions(mock_async_dispose, auth_instance):
    mock_async_dispose.side_effect = CameDomoticError("error")
    api = CameDomoticAPI(auth_instance)
    try:
        await api.async_dispose()
    except Exception as e:  # pylint: disable=broad-except
        pytest.fail(f"async_dispose raised an exception: {e}")


@patch.object(Auth, "async_dispose")
async def test_context_manager(mock_async_dispose, auth_instance):
    async with CameDomoticAPI(auth_instance):
        pass
    mock_async_dispose.assert_called_once()


@patch.object(Auth, "async_dispose")
async def test_context_manager_no_exceptions(mock_async_dispose, auth_instance):
    mock_async_dispose.side_effect = CameDomoticError("error")
    try:
        async with CameDomoticAPI(auth_instance):
            pass
        mock_async_dispose.assert_called_once()
    except Exception as e:  # pylint: disable=broad-except
        pytest.fail(f"__aexit__ raised an exception: {e}")


@patch.object(Auth, "async_create")
async def test_async_create_all_params(mock_async_create):
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
        mock_session, "host", "username", "password", close_websession_on_disposal=True
    )
    assert api.auth == mock_auth


@patch("aiohttp.ClientSession")
@patch.object(Auth, "async_create")
async def test_async_create_default_params(
    mock_async_create,
    mock_session,  # pylint: disable=unused-argument
):
    mock_auth = AsyncMock()
    mock_async_create.return_value = mock_auth

    # Define an AsyncMock

    api = await CameDomoticAPI.async_create("host", "username", "password")

    mock_async_create.assert_called_once()
    assert api.auth == mock_auth


@patch.object(Auth, "async_create")
async def test_async_create_exception(mock_async_create):
    mock_async_create.side_effect = CameDomoticServerNotFoundError("error")

    with pytest.raises(CameDomoticServerNotFoundError, match="error"):
        await CameDomoticAPI.async_create("host", "username", "password")


# endregion

# region async_get_users


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_users(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_users_empty_list(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)

    # Test empty list
    mock_send_command.return_value.json.return_value = {
        "sl_cmd": "sl_users_list_resp",
        "sl_data_ack_reason": 0,
        "sl_client_id": "75c6c33a",
        "sl_users_list": [],  # Empty list
    }

    users = await api.async_get_users()
    assert len(users) == 0
    assert isinstance(users, list)

    # Test missing key
    mock_send_command.return_value.json.return_value = {
        "sl_cmd": "sl_users_list_resp",
        "sl_data_ack_reason": 0,
        "sl_client_id": "75c6c33a",
        # "sl_users_list" key is missing
    }

    users = await api.async_get_users()
    assert len(users) == 0
    assert isinstance(users, list)

    users = await api.async_get_users()
    assert len(users) == 0
    assert isinstance(users, list)


# endregion

# region async_get_server_info


# Test for async_get_server_info method
@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_server_info(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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

    server_info = await api.async_get_server_info()
    assert isinstance(server_info, ServerInfo)
    assert server_info.keycode == "0000FFFF9999AAAA"
    assert server_info.swver == "1.2.3"
    assert server_info.type == "0"
    assert server_info.board == "3"
    assert server_info.serial == "0011ffee"

    features = server_info.list
    assert len(features) == 7
    assert features[0] == "lights"
    assert features[1] == "openings"


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_server_info_missing_essential_keys(
    mock_send_command, auth_instance
):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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

    # ServerInfo model instantiation will now raise ValueError with description
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: keycode"
    ):
        await api.async_get_server_info()

    # Test missing 'list'
    mock_send_command.return_value.json.return_value = {
        "cmd_name": "feature_list_resp",
        "cseq": 1,
        "keycode": "0000FFFF9999AAAA",
        "swver": "1.2.3",
        "serial": "0011ffee",
        # "list": ["lights"], # Missing list
        "sl_data_ack_reason": 0,
    }
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: list"
    ):
        await api.async_get_server_info()

    # Test multiple missing fields
    mock_send_command.return_value.json.return_value = {
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
        match="Missing required ServerInfo properties: keycode, serial, list",
    ):
        await api.async_get_server_info()


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_server_info_empty_feature_list(
    mock_send_command, auth_instance
):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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
    assert len(server_info.list) == 0


# endregion


# region async_get_lights


# Test for async_get_lights method
@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_lights(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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

    lights = await api.async_get_lights()
    assert len(lights) == 7
    assert isinstance(lights[0], Light)
    assert isinstance(lights[1], Light)


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_lights_empty_array(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)

    # Test empty list
    mock_send_command.return_value.json.return_value = {
        "array": [],  # Empty array
        "cmd_name": "light_list_resp",
        "cseq": 1,
        "sl_data_ack_reason": 0,
    }

    lights = await api.async_get_lights()
    assert len(lights) == 0
    assert isinstance(lights, list)

    # Test missing list
    mock_send_command.return_value.json.return_value = {
        # "array": [],
        "cmd_name": "light_list_resp",
        "cseq": 1,
        "sl_data_ack_reason": 0,
    }

    lights = await api.async_get_lights()
    assert len(lights) == 0
    assert isinstance(lights, list)


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_lights_malformed_light_data(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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

    # Test missing "name"
    mock_send_command.return_value.json.return_value = {
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


# endregion

# region async_get_openings


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_openings(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
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


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_openings_empty_array(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)

    # Test empty list
    mock_send_command.return_value.json.return_value = {
        "array": [],  # Empty array
        "cmd_name": "openings_list_resp",
        "cseq": 1,
        "sl_data_ack_reason": 0,
    }

    openings = await api.async_get_openings()
    assert len(openings) == 0
    assert isinstance(openings, list)

    # Test missing array key
    mock_send_command.return_value.json.return_value = {
        # "array": [],
        "cmd_name": "openings_list_resp",
        "cseq": 1,
        "sl_data_ack_reason": 0,
    }

    openings = await api.async_get_openings()
    assert len(openings) == 0
    assert isinstance(openings, list)


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_openings_malformed_opening_data(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    # Test missing open_act_id
    mock_send_command.return_value.json.return_value = {
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

    with pytest.raises(ValueError, match="Data is missing required keys: open_act_id"):
        await api.async_get_openings()

    # Test missing close_act_id
    mock_send_command.return_value.json.return_value = {
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

    with pytest.raises(ValueError, match="Data is missing required keys: close_act_id"):
        await api.async_get_openings()

    # Test missing name
    mock_send_command.return_value.json.return_value = {
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


@patch.object(Auth, "async_send_command", return_value=AsyncMock())
async def test_async_get_openings_unknown_enums(mock_send_command, auth_instance):
    api = CameDomoticAPI(auth_instance)
    mock_send_command.return_value.json.return_value = {
        "array": [
            {
                "open_act_id": 1,
                "close_act_id": 2,
                "floor_ind": 19,
                "name": "opening_ChQQs",
                "room_ind": 23,
                "status": 99,  # Unknown status value
                "type": 99,    # Unknown type value
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
    assert openings[0].type.value == -1    # OpeningType.UNKNOWN


# endregion
