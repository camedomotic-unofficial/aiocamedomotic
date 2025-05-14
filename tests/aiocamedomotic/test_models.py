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
    ServerInfo,
    User,
    Light,
    UpdateList,
    LightStatus,
    LightType,
    Opening,
    OpeningStatus,
    OpeningType,
)

from tests.aiocamedomotic.mocked_responses import STATUS_UPDATE_RESP
from tests.aiocamedomotic.const import auth_instance  # noqa: F401


# region CameFeature and ServerInfo tests


def test_came_server_info_initialization():
    features = ["Feature1", "Feature2"]
    server_info = ServerInfo(
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
    server_info = ServerInfo(
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
            ServerInfo()  # pylint: disable=no-value-for-parameter
        )


# endregion
# region User tests


def test_came_user_initialization(auth_instance):
    raw_data = {"name": "Test User"}
    user = User(raw_data, auth_instance)

    assert user.auth == auth_instance
    assert user.raw_data == raw_data
    assert user.name == "Test User"


def test_came_user_invalid_input(auth_instance):
    # Test null raw_data
    raw_data = None
    with pytest.raises(ValueError):
        User(raw_data, auth_instance)

    # Test missing "name" key in raw_data
    raw_data = {"unknown_key": "Invalid value"}
    with pytest.raises(ValueError):
        User(raw_data, auth_instance)


# endregion
# region UpdateList tests


def test_updatelist_init_with_data():
    updates = UpdateList(STATUS_UPDATE_RESP)
    assert updates._raw_data == STATUS_UPDATE_RESP
    assert updates.data == STATUS_UPDATE_RESP.get("result")


def test_updatelist_init_without_data():
    updates = UpdateList()
    assert updates._raw_data is None
    assert updates.data == []


def test_updatelist_init_with_empty_data():
    updates = UpdateList({})
    assert updates._raw_data == {}
    assert updates.data == []


def test_updatelist_init_with_non_dict_data():
    updates = UpdateList("non-dict data")
    assert updates._raw_data == "non-dict data"
    assert updates.data == []


# region Light tests


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


def test_came_light_initialization(light_data_on_off, auth_instance):
    light = Light(light_data_on_off, auth_instance)
    assert light.raw_data == light_data_on_off
    assert light.auth == auth_instance

    # Test post_init validation
    with pytest.raises(ValueError):
        Opening({"name": "Test"}, auth_instance)  # Missing act_id


def test_came_light_properties(light_data_dimmable, auth_instance):
    light = Light(light_data_dimmable, auth_instance)
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
    light = Light(light_data_on_off, auth_instance)
    light_dimm = Light(light_data_dimmable, auth_instance)

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
    light = Light(light_data_on_off, auth_instance)
    light_dimm = Light(light_data_dimmable, auth_instance)

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

# region Opening tests


@pytest.fixture
def opening_data_shutter_stopped():
    """Mock data for a stopped shutter opening."""
    return {
        "open_act_id": 10,
        "close_act_id": 11,
        "floor_ind": 1,
        "name": "Living Room Shutter",
        "room_ind": 2,
        "status": 0,  # Corresponds to OpeningStatus.STOPPED
        "type": 0,  # Corresponds to OpeningType.SHUTTER
        "partial": [],
    }


@pytest.fixture
def opening_data_awning_opening():
    """Mock data for an opening awning."""
    return {
        "open_act_id": 20,
        "close_act_id": 21,
        "floor_ind": 1,
        "name": "Patio Shutter",
        "room_ind": 3,
        "status": 1,  # Corresponds to OpeningStatus.OPENING
        "type": 0,  # OpeningType.SHUTTER
        "partial": [],
    }


def test_opening_status_enum():
    """Test the OpeningStatus enum values."""
    assert OpeningStatus.STOPPED.value == 0
    assert OpeningStatus.OPENING.value == 1
    assert OpeningStatus.CLOSING.value == 2


def test_opening_type_enum():
    """Test the OpeningType enum values."""
    assert OpeningType.SHUTTER.value == 0


def test_came_opening_initialization(opening_data_shutter_stopped, auth_instance):
    """Test Opening class initialization."""
    opening = Opening(opening_data_shutter_stopped, auth_instance)
    assert opening.raw_data == opening_data_shutter_stopped
    assert opening.auth == auth_instance

    # Test post_init validation
    with pytest.raises(ValueError):
        Opening({"open_act_id": 1}, auth_instance)  # Missing close_act_id
    with pytest.raises(ValueError):
        Opening({"close_act_id": 2}, auth_instance)  # Missing open_act_id


def test_came_opening_properties(opening_data_awning_opening, auth_instance):
    """Test Opening class properties."""
    opening = Opening(opening_data_awning_opening, auth_instance)
    assert opening.open_act_id == opening_data_awning_opening["open_act_id"]
    assert opening.close_act_id == opening_data_awning_opening["close_act_id"]
    assert opening.name == opening_data_awning_opening["name"]
    assert opening.status == OpeningStatus.OPENING
    assert opening.type == OpeningType.SHUTTER
    assert opening.floor_ind == opening_data_awning_opening["floor_ind"]
    assert opening.room_ind == opening_data_awning_opening["room_ind"]
    assert len(opening.partial_positions) == 0


@pytest.mark.asyncio
@patch.object(
    Auth,
    "async_get_valid_client_id",
    new_callable=AsyncMock,
    return_value="mock_client_id",
)
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_came_opening_async_set_status(
    mock_send_command,
    mock_get_client_id,  # pylint: disable=unused-argument
    opening_data_shutter_stopped,
    auth_instance,
):
    """Test Opening.async_set_status method."""
    opening = Opening(opening_data_shutter_stopped, auth_instance)
    initial_cseq = auth_instance.cseq

    # Test setting status to OPENING
    await opening.async_set_status(OpeningStatus.OPENING)

    expected_payload_opening = {
        "sl_appl_msg": {
            "act_id": opening.open_act_id,
            "client": "mock_client_id",
            "cmd_name": "opening_move_req",
            "cseq": initial_cseq + 1,
            "wanted_status": OpeningStatus.OPENING.value,
        },
        "sl_appl_msg_type": "domo",
        "sl_client_id": "mock_client_id",
        "sl_cmd": "sl_data_req",
    }
    mock_send_command.assert_called_with(expected_payload_opening)
    assert opening.status == OpeningStatus.OPENING  # Check internal state update

    # Test setting status to CLOSING
    await opening.async_set_status(OpeningStatus.CLOSING)

    expected_payload_closing = {
        "sl_appl_msg": {
            "act_id": opening.close_act_id,
            "client": "mock_client_id",
            "cmd_name": "opening_move_req",
            "cseq": mock_send_command.call_args_list[-1][0][0]["sl_appl_msg"]["cseq"],
            "wanted_status": OpeningStatus.CLOSING.value,
        },
        "sl_appl_msg_type": "domo",
        "sl_client_id": "mock_client_id",
        "sl_cmd": "sl_data_req",
    }
    mock_send_command.assert_called_with(expected_payload_closing)
    assert opening.status == OpeningStatus.CLOSING
    assert mock_send_command.call_count == 2

    # Test setting status to STOPPED
    await opening.async_set_status(OpeningStatus.STOPPED)

    expected_payload_stopped = {
        "sl_appl_msg": {
            "act_id": opening.open_act_id,
            "client": "mock_client_id",
            "cmd_name": "opening_move_req",
            "cseq": mock_send_command.call_args_list[-1][0][0]["sl_appl_msg"]["cseq"],
            "wanted_status": OpeningStatus.STOPPED.value,
        },
        "sl_appl_msg_type": "domo",
        "sl_client_id": "mock_client_id",
        "sl_cmd": "sl_data_req",
    }
    mock_send_command.assert_called_with(expected_payload_stopped)
    assert opening.status == OpeningStatus.STOPPED
    assert mock_send_command.call_count == 3


# endregion
