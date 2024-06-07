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
# pylint: disable=protected-access


from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
from aiohttp import ClientSession
import pytest
import pytest_asyncio
from aiocamedomotic import Auth
from aiocamedomotic.models import (
    CameServerInfo,
    CameUser,
    CameLight,
    CameUpdateList,
    LightStatus,
    LightType,
)

from tests.aiocamedomotic.mocked_responses import STATUS_UPDATE_RESP


@pytest_asyncio.fixture
async def auth_instance() -> AsyncGenerator[Auth, None]:
    session = ClientSession()
    with patch.object(Auth, "async_validate_host", return_value=True):
        auth = await Auth.async_create(session, "192.168.x.x", "user", "password")
    yield auth
    await session.close()


# region CameFeature and CameServerInfo tests


def test_came_server_info_initialization():
    features = ["Feature1", "Feature2"]
    server_info = CameServerInfo(
        keycode="keycode1",
        serial="serial1",
        swver="swver1",
        type="type1",
        board="board1",
        list=features,
    )

    assert server_info.keycode == "keycode1"
    assert server_info.swver == "swver1"
    assert server_info.type == "type1"
    assert server_info.board == "board1"
    assert server_info.serial == "serial1"
    assert server_info.list == features


def test_came_server_info_initialization_nullable():
    features = ["Feature1", "Feature2"]
    server_info = CameServerInfo(
        keycode="keycode1",
        serial="serial1",
        list=features,
    )

    assert server_info.keycode == "keycode1"
    assert server_info.serial == "serial1"
    assert server_info.list == features
    assert server_info.type is None
    assert server_info.board is None
    assert server_info.swver is None


def test_came_server_info_initialization_invalid():
    with pytest.raises(TypeError):
        server_info = (  # pylint: disable=unused-variable # noqa: F841
            CameServerInfo()  # pylint: disable=no-value-for-parameter
        )


# endregion
# region CameUser tests


def test_came_user_initialization(auth_instance):
    raw_data = {"name": "Test User"}
    user = CameUser(raw_data, auth_instance)

    assert user.auth == auth_instance
    assert user.raw_data == raw_data
    assert user.name == "Test User"


def test_came_user_invalid_input(auth_instance):
    # Test null raw_data
    raw_data = None
    with pytest.raises(ValueError):
        CameUser(raw_data, auth_instance)

    # Test missing "name" key in raw_data
    raw_data = {"unknown_key": "Invalid value"}
    with pytest.raises(ValueError):
        CameUser(raw_data, auth_instance)


# endregion
# region CameLight tests


@pytest.fixture
def light_data_on_off():
    return {
        "act_id": 1,
        "floor_ind": 2,
        "name": "Test Light",
        "room_ind": 3,
        "status": 1,
        "type": "STEP_STEP",
    }


@pytest.fixture
def light_data_dimmable():
    return {
        "act_id": 1,
        "floor_ind": 2,
        "name": "Test Light",
        "room_ind": 3,
        "status": 1,
        "type": "DIMMER",
        "perc": 80,
    }


def test_updatelist_init_with_data():
    updates = CameUpdateList(STATUS_UPDATE_RESP)
    assert updates._raw_data == STATUS_UPDATE_RESP
    assert updates.data == STATUS_UPDATE_RESP.get("result")


def test_updatelist_init_without_data():
    updates = CameUpdateList()
    assert updates._raw_data is None
    assert updates.data == []


def test_updatelist_init_with_empty_data():
    updates = CameUpdateList({})
    assert updates._raw_data == {}
    assert updates.data == []


def test_updatelist_init_with_non_dict_data():
    updates = CameUpdateList("non-dict data")
    assert updates._raw_data == "non-dict data"
    assert updates.data == []


def test_came_light_initialization(light_data_on_off, auth_instance):
    light = CameLight(light_data_on_off, auth_instance)
    assert light.raw_data == light_data_on_off
    assert light.auth == auth_instance


def test_came_light_properties(light_data_dimmable, auth_instance):
    light = CameLight(light_data_dimmable, auth_instance)
    assert light.act_id == light_data_dimmable["act_id"]
    assert light.floor_ind == light_data_dimmable["floor_ind"]
    assert light.name == light_data_dimmable["name"]
    assert light.room_ind == light_data_dimmable["room_ind"]
    assert light.status == LightStatus(light_data_dimmable["status"])
    assert light.type == LightType(light_data_dimmable["type"])
    assert light.perc == light_data_dimmable["perc"]


@pytest.mark.asyncio
@patch.object(
    Auth,
    "async_get_valid_client_id",
    new_callable=AsyncMock,
    return_value="my_session_id",
)
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_came_light_async_set_status(
    mock_send_command,
    mock_get_client_id,  # pylint: disable=unused-argument
    light_data_dimmable,
    light_data_on_off,
    auth_instance,
):
    light = CameLight(light_data_on_off, auth_instance)
    light_dimm = CameLight(light_data_dimmable, auth_instance)

    # Test non-dimmable light
    await light.async_set_status(LightStatus.ON)
    mock_send_command.assert_called_once()
    assert light.status == LightStatus.ON
    assert light.perc == 100

    # Test dimmable light
    await light_dimm.async_set_status(LightStatus.OFF, 50)
    assert mock_send_command.call_count == 2
    assert light_dimm.status == LightStatus.OFF
    assert light_dimm.perc == 50


@pytest.mark.asyncio
@patch.object(Auth, "async_get_valid_client_id", return_value=1)
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_came_light_async_set_status_invalid_brightness(
    mock_send_command,
    mock_get_client_id,  # pylint: disable=unused-argument
    light_data_dimmable,
    light_data_on_off,
    auth_instance,
):
    light = CameLight(light_data_on_off, auth_instance)
    light_dimm = CameLight(light_data_dimmable, auth_instance)

    # Test non-dimmable light
    await light.async_set_status(LightStatus.ON, 50)
    mock_send_command.assert_called_once()
    assert light.perc == 100  # brightness is ignored for non-dimmable lights

    # Test dimmable light
    await light_dimm.async_set_status(LightStatus.OFF, 150)
    assert mock_send_command.call_count == 2
    assert light_dimm.perc == 100  # brightness is capped at 100

    await light_dimm.async_set_status(LightStatus.OFF, -50)
    assert mock_send_command.call_count == 3
    assert light_dimm.perc == 0  # brightness is capped at 0


# endregion
