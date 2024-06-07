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
    CameServerInfo,
    CameUser,
    CameLight,
)
from aiocamedomotic.errors import (
    CameDomoticServerNotFoundError,
    CameDomoticError,
)


from tests.aiocamedomotic.const import (
    auth_instance,  # noqa: F401
    auth_instance_not_logged_in,  # noqa: F401
)


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
    mock_async_create, mock_session  # pylint: disable=unused-argument
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
    assert isinstance(users[0], CameUser)
    assert isinstance(users[1], CameUser)
    assert users[0].name == "admin"
    assert users[1].name == "user"


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
    assert isinstance(server_info, CameServerInfo)
    assert server_info.keycode == "0000FFFF9999AAAA"
    assert server_info.swver == "1.2.3"
    assert server_info.type == "0"
    assert server_info.board == "3"
    assert server_info.serial == "0011ffee"

    features = server_info.list
    assert len(features) == 7
    assert features[0] == "lights"
    assert features[1] == "openings"


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
    assert isinstance(lights[0], CameLight)
    assert isinstance(lights[1], CameLight)
