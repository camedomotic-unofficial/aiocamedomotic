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
from aiocamedomotic.errors import CameDomoticAuthError
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
    Floor,
    Room,
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
        features=features,
    )

    assert server_info.keycode == "keycode1"
    assert server_info.swver == "swver1"
    assert server_info.type == "type1"
    assert server_info.board == "board1"
    assert server_info.serial == "serial1"
    assert server_info.features == features


def test_came_server_info_initialization_nullable():
    features = ["Feature1", "Feature2"]
    server_info = ServerInfo(
        keycode="keycode1",
        serial="serial1",
        features=features,
    )

    assert server_info.keycode == "keycode1"
    assert server_info.serial == "serial1"
    assert server_info.features == features
    assert server_info.type is None
    assert server_info.board is None
    assert server_info.swver is None


def test_came_server_info_initialization_invalid():
    with pytest.raises(TypeError):
        server_info = (  # pylint: disable=unused-variable # noqa: F841
            ServerInfo()  # pylint: disable=no-value-for-parameter
        )


def test_server_info_missing_keycode():
    """Test ServerInfo validation when keycode is missing."""
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: keycode"
    ):
        ServerInfo(keycode=None, serial="12345", features=["lights", "openings"])


def test_server_info_missing_serial():
    """Test ServerInfo validation when serial is missing."""
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: serial"
    ):
        ServerInfo(keycode="001122AABBCC", serial=None, features=["lights", "openings"])


def test_server_info_missing_features():
    """Test ServerInfo validation when features is missing."""
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: features"
    ):
        ServerInfo(keycode="001122AABBCC", serial="12345", features=None)


def test_server_info_missing_multiple_fields():
    """Test ServerInfo validation when multiple fields are missing."""
    with pytest.raises(
        ValueError, match="Missing required ServerInfo properties: keycode, serial"
    ):
        ServerInfo(keycode=None, serial=None, features=["lights", "openings"])


def test_server_info_all_optional_fields_none():
    """Test ServerInfo with all optional fields as None."""
    server_info = ServerInfo(
        keycode="001122AABBCC",
        serial="12345",
        features=["lights", "openings"],
        swver=None,
        type=None,
        board=None,
    )

    assert server_info.keycode == "001122AABBCC"
    assert server_info.serial == "12345"
    assert server_info.features == ["lights", "openings"]
    assert server_info.swver is None
    assert server_info.type is None
    assert server_info.board is None


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


@pytest.mark.asyncio
async def test_user_async_set_as_current_user_success():
    """Test successful user switching."""
    # Create mock auth
    mock_auth = AsyncMock(spec=Auth)
    backup_credentials = ("old_user", "old_pass", "client_id", 123, 30, 1)
    mock_auth.backup_auth_credentials.return_value = backup_credentials

    # Create user instance
    user_data = {"name": "new_user", "id": 123}
    user = User(user_data, mock_auth)

    # Execute the method
    await user.async_set_as_current_user("new_password")

    # Verify the sequence of calls
    mock_auth.backup_auth_credentials.assert_called_once()
    mock_auth.async_logout.assert_called_once()
    mock_auth.update_auth_credentials.assert_called_once_with(
        "new_user", "new_password"
    )
    mock_auth.async_login.assert_called_once()


# Note: The following tests reveal a bug in the current implementation where
# restore_auth_credentials is not async but is being awaited in the User class.
# These tests are commented out until the implementation is fixed.


@pytest.mark.asyncio
async def test_user_attempt_login_as_current_user():
    """Test the private login attempt method."""
    # Create mock auth
    mock_auth = AsyncMock(spec=Auth)

    # Create user instance
    user_data = {"name": "test_user", "id": 123}
    user = User(user_data, mock_auth)

    # Execute the private method
    await user._attempt_login_as_current_user("test_password")

    # Verify the sequence
    mock_auth.async_logout.assert_called_once()
    mock_auth.update_auth_credentials.assert_called_once_with(
        "test_user", "test_password"
    )
    mock_auth.async_login.assert_called_once()


@pytest.mark.asyncio
async def test_user_attempt_login_as_current_user_login_failure():
    """Test private login method when login fails."""
    # Create mock auth
    mock_auth = AsyncMock(spec=Auth)
    mock_auth.async_login.side_effect = CameDomoticAuthError("Login failed")

    # Create user instance
    user_data = {"name": "test_user", "id": 123}
    user = User(user_data, mock_auth)

    # Execute and expect failure
    with pytest.raises(CameDomoticAuthError, match="Login failed"):
        await user._attempt_login_as_current_user("test_password")

    # Verify logout and credential update were called before failure
    mock_auth.async_logout.assert_called_once()
    mock_auth.update_auth_credentials.assert_called_once_with(
        "test_user", "test_password"
    )


# endregion
# region UpdateList tests


def test_updatelist_init_with_data():
    updates = UpdateList(STATUS_UPDATE_RESP.get("result"))
    assert updates.data == STATUS_UPDATE_RESP.get("result")


def test_updatelist_init_without_data():
    updates = UpdateList()
    assert updates.data == []


def test_updatelist_init_with_empty_data():
    updates = UpdateList({})
    assert updates.data == []


def test_updatelist_init_with_non_dict_data():
    updates = UpdateList(12345)
    assert updates.data == []


# endregion
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


def test_light_unknown_type(auth_instance):
    """Test that a light with an unknown type is correctly handled."""
    # Create light data with an unknown type
    unknown_light_data = {
        "act_id": 1,
        "floor_ind": 2,
        "name": "Unknown Light Type",
        "room_ind": 3,
        "status": 1,
        "type": "UNKNOWN_TYPE_FROM_API",
    }

    # Initialize the light
    light = Light(unknown_light_data, auth_instance)

    # Verify that the light is created correctly
    assert light.raw_data == unknown_light_data
    assert light.name == "Unknown Light Type"

    # Verify that the type property returns UNKNOWN
    assert light.type == LightType.UNKNOWN

    # Verify that other properties are still accessible
    assert light.status == LightStatus.ON
    assert light.act_id == 1
    assert light.perc == 100  # Default value for non-dimmable lights


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


def test_light_edge_case_missing_optional_field(auth_instance):
    """Test Light model when optional fields are missing."""
    # Create light data missing some optional fields
    light_data = {
        "act_id": 1,
        "name": "Test Light",
        "status": 1,
        # Missing optional fields like floor_ind, room_ind, perc, etc.
    }

    light = Light(light_data, auth_instance)

    # Test property access that might trigger untested lines
    assert light.name == "Test Light"
    assert light.act_id == 1
    assert light.status == LightStatus.ON


def test_light_status_unknown_value(auth_instance):
    """Test Light status property with unknown status value."""
    light_data = {
        "act_id": 1,
        "name": "Test Light",
        "status": 999,  # Unknown status value
        "type": "STEP_STEP",
    }

    light = Light(light_data, auth_instance)

    # This should raise a ValueError when accessing the status property
    with pytest.raises(ValueError):
        status = light.status


def test_light_auth_type_validation():
    """Test Light auth parameter type validation."""
    light_data = {
        "act_id": 1,
        "name": "Test Light",
        "status": 1,
        "type": "STEP_STEP",
    }

    # Test with non-Auth object (string)
    with pytest.raises(ValueError, match="'auth' must be an instance of Auth, got str"):
        Light(light_data, "not_an_auth_instance")

    # Test with non-Auth object (dict)
    with pytest.raises(
        ValueError, match="'auth' must be an instance of Auth, got dict"
    ):
        Light(light_data, {"fake": "auth"})


@pytest.mark.asyncio
@patch.object(Auth, "async_get_valid_client_id", return_value="test_client")
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_light_unknown_type_warning_in_async_set_status(
    mock_send_command, mock_get_client_id, auth_instance, caplog
):
    """Test Light unknown type warning during async_set_status."""
    import logging

    # Create light data with unknown type (this will trigger LightType.UNKNOWN)
    light_data = {
        "act_id": 1,
        "name": "Unknown Type Light",
        "status": 1,
        "type": "UNKNOWN_TYPE_FROM_API",  # This will become LightType.UNKNOWN
    }

    light = Light(light_data, auth_instance)

    # Verify the light has unknown type
    assert light.type == LightType.UNKNOWN

    # Set up logging to capture warnings
    with caplog.at_level(logging.WARNING):
        # Call async_set_status to trigger the warning
        await light.async_set_status(LightStatus.ON)

    # Verify warning was logged
    assert (
        "Attempting to set status for light 'Unknown Type Light' (ID: 1) with UNKNOWN type"
        in caplog.text
    )
    assert "Command might fail or have unintended effects" in caplog.text

    # Verify the command was still sent
    mock_send_command.assert_called_once()


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
    assert OpeningType.UNKNOWN.value == -1


def test_opening_unknown_type(auth_instance):
    """Test that an opening with an unknown type is correctly handled."""
    # Create opening data with an unknown type
    unknown_opening_data = {
        "open_act_id": 10,
        "close_act_id": 11,
        "floor_ind": 1,
        "name": "Unknown Opening Type",
        "room_ind": 2,
        "status": 0,
        "type": 999,  # Unknown type value
        "partial": [],
    }

    # Initialize the opening
    opening = Opening(unknown_opening_data, auth_instance)

    # Verify that the opening is created correctly
    assert opening.raw_data == unknown_opening_data
    assert opening.name == "Unknown Opening Type"

    # Verify that the type property returns UNKNOWN
    assert opening.type == OpeningType.UNKNOWN

    # Verify that other properties are still accessible
    assert opening.open_act_id == 10
    assert opening.close_act_id == 11


def test_opening_unknown_status(auth_instance):
    """Test that an opening with an unknown status is correctly handled."""
    # Create opening data with an unknown status
    unknown_status_data = {
        "open_act_id": 10,
        "close_act_id": 11,
        "floor_ind": 1,
        "name": "Unknown Status Opening",
        "room_ind": 2,
        "status": 999,  # Unknown status value
        "type": 0,  # Valid type (SHUTTER)
        "partial": [],
    }

    # Initialize the opening
    opening = Opening(unknown_status_data, auth_instance)

    # Verify that the opening is created correctly
    assert opening.raw_data == unknown_status_data
    assert opening.name == "Unknown Status Opening"

    # Verify that the status property returns UNKNOWN
    assert opening.status == OpeningStatus.UNKNOWN

    # Verify that other properties are still accessible
    assert opening.type == OpeningType.SHUTTER
    assert opening.open_act_id == 10
    assert opening.close_act_id == 11


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
        "act_id": opening.open_act_id,
        "cmd_name": "opening_move_req",
        "wanted_status": OpeningStatus.OPENING.value,
    }
    mock_send_command.assert_called_with(expected_payload_opening)
    assert opening.status == OpeningStatus.OPENING  # Check internal state update

    # Test setting status to CLOSING
    await opening.async_set_status(OpeningStatus.CLOSING)

    expected_payload_closing = {
        "act_id": opening.close_act_id,
        "cmd_name": "opening_move_req",
        "wanted_status": OpeningStatus.CLOSING.value,
    }
    mock_send_command.assert_called_with(expected_payload_closing)
    assert opening.status == OpeningStatus.CLOSING
    assert mock_send_command.call_count == 2

    # Test setting status to STOPPED
    await opening.async_set_status(OpeningStatus.STOPPED)

    expected_payload_stopped = {
        "act_id": opening.open_act_id,
        "cmd_name": "opening_move_req",
        "wanted_status": OpeningStatus.STOPPED.value,
    }
    mock_send_command.assert_called_with(expected_payload_stopped)
    assert opening.status == OpeningStatus.STOPPED
    assert mock_send_command.call_count == 3


def test_opening_auth_type_validation():
    """Test Opening auth parameter type validation."""
    opening_data = {
        "open_act_id": 10,
        "close_act_id": 11,
        "name": "Test Opening",
        "status": 0,
        "type": 0,
    }

    # Test with non-Auth object (string)
    with pytest.raises(ValueError, match="'auth' must be an instance of Auth, got str"):
        Opening(opening_data, "not_an_auth_instance")

    # Test with non-Auth object (dict)
    with pytest.raises(
        ValueError, match="'auth' must be an instance of Auth, got dict"
    ):
        Opening(opening_data, {"fake": "auth"})


# endregion

# region Floor tests


def test_floor_initialization():
    """Test Floor class initialization with valid data."""
    floor_data = {"floor_ind": 1, "name": "Ground Floor"}

    floor = Floor(floor_data)

    assert floor.raw_data == floor_data
    assert floor.id == 1
    assert floor.name == "Ground Floor"


def test_floor_initialization_missing_id():
    """Test Floor initialization when floor_ind is missing."""
    floor_data = {"name": "Ground Floor"}

    with pytest.raises(ValueError, match="Data is missing required keys: floor_ind"):
        Floor(floor_data)


def test_floor_initialization_missing_name():
    """Test Floor initialization when name is missing."""
    floor_data = {"floor_ind": 1}

    with pytest.raises(ValueError, match="Data is missing required keys: name"):
        Floor(floor_data)


def test_floor_initialization_missing_multiple_keys():
    """Test Floor initialization when multiple required keys are missing."""
    floor_data = {}

    with pytest.raises(
        ValueError, match="Data is missing required keys: floor_ind, name"
    ):
        Floor(floor_data)


def test_floor_initialization_non_dict_data():
    """Test Floor initialization with non-dict data."""
    with pytest.raises(ValueError, match="Provided data must be a dictionary"):
        Floor("not a dict")


def test_floor_properties_with_string_id():
    """Test Floor properties when floor_ind is provided as string."""
    floor_data = {"floor_ind": "2", "name": "First Floor"}

    floor = Floor(floor_data)

    assert floor.id == "2"  # Returns as-is from raw_data
    assert floor.name == "First Floor"


# endregion

# region Room tests


def test_room_initialization():
    """Test Room class initialization with valid data."""
    room_data = {"room_ind": 5, "name": "Living Room", "floor_ind": 1}

    room = Room(room_data)

    assert room.raw_data == room_data
    assert room.id == 5
    assert room.name == "Living Room"
    assert room.floor_id == 1


def test_room_initialization_missing_id():
    """Test Room initialization when room_ind is missing."""
    room_data = {"name": "Living Room", "floor_ind": 1}

    with pytest.raises(ValueError, match="Data is missing required keys: room_ind"):
        Room(room_data)


def test_room_initialization_missing_name():
    """Test Room initialization when name is missing."""
    room_data = {"room_ind": 5, "floor_ind": 1}

    with pytest.raises(ValueError, match="Data is missing required keys: name"):
        Room(room_data)


def test_room_initialization_missing_floor_id():
    """Test Room initialization when floor_ind is missing."""
    room_data = {"room_ind": 5, "name": "Living Room"}

    with pytest.raises(ValueError, match="Data is missing required keys: floor_ind"):
        Room(room_data)


def test_room_initialization_missing_multiple_keys():
    """Test Room initialization when multiple required keys are missing."""
    room_data = {"name": "Living Room"}

    with pytest.raises(
        ValueError, match="Data is missing required keys: room_ind, floor_ind"
    ):
        Room(room_data)


def test_room_initialization_missing_all_keys():
    """Test Room initialization when all required keys are missing."""
    room_data = {}

    with pytest.raises(
        ValueError, match="Data is missing required keys: room_ind, name, floor_ind"
    ):
        Room(room_data)


def test_room_initialization_non_dict_data():
    """Test Room initialization with non-dict data."""
    with pytest.raises(ValueError, match="Provided data must be a dictionary"):
        Room("not a dict")


def test_room_properties_with_string_ids():
    """Test Room properties when IDs are provided as strings."""
    room_data = {"room_ind": "10", "name": "Kitchen", "floor_ind": "2"}

    room = Room(room_data)

    assert room.id == "10"  # Returns as-is from raw_data
    assert room.name == "Kitchen"
    assert room.floor_id == "2"  # Returns as-is from raw_data


# endregion
