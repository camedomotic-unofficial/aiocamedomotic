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


from unittest.mock import AsyncMock, patch
import pytest
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


class TestServerInfo:
    def test_initialization(self):
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

    def test_initialization_nullable(self):
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

    def test_initialization_invalid(self):
        with pytest.raises(TypeError):
            server_info = (  # pylint: disable=unused-variable # noqa: F841
                ServerInfo()  # pylint: disable=no-value-for-parameter
            )

    def test_missing_keycode(self):
        with pytest.raises(
            ValueError, match="Missing required ServerInfo properties: keycode"
        ):
            ServerInfo(keycode=None, serial="12345", features=["lights", "openings"])

    def test_missing_serial(self):
        with pytest.raises(
            ValueError, match="Missing required ServerInfo properties: serial"
        ):
            ServerInfo(
                keycode="001122AABBCC",
                serial=None,
                features=["lights", "openings"],
            )

    def test_missing_features(self):
        with pytest.raises(
            ValueError, match="Missing required ServerInfo properties: features"
        ):
            ServerInfo(keycode="001122AABBCC", serial="12345", features=None)

    def test_missing_multiple_fields(self):
        with pytest.raises(
            ValueError,
            match="Missing required ServerInfo properties: keycode, serial",
        ):
            ServerInfo(keycode=None, serial=None, features=["lights", "openings"])

    def test_all_optional_fields_none(self):
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


class TestUser:
    def test_initialization(self, auth_instance):
        raw_data = {"name": "Test User"}
        user = User(raw_data, auth_instance)

        assert user.auth == auth_instance
        assert user.raw_data == raw_data
        assert user.name == "Test User"

    def test_invalid_input(self, auth_instance):
        # Test null raw_data
        raw_data = None
        with pytest.raises(ValueError):
            User(raw_data, auth_instance)

        # Test missing "name" key in raw_data
        raw_data = {"unknown_key": "Invalid value"}
        with pytest.raises(ValueError):
            User(raw_data, auth_instance)

    @pytest.mark.asyncio
    async def test_async_set_as_current_user_success(self):
        mock_auth = AsyncMock(spec=Auth)
        backup_credentials = ("old_user", "old_pass", "client_id", 123, 30, 1)
        mock_auth.backup_auth_credentials.return_value = backup_credentials

        user_data = {"name": "new_user", "id": 123}
        user = User(user_data, mock_auth)

        await user.async_set_as_current_user("new_password")

        mock_auth.backup_auth_credentials.assert_called_once()
        mock_auth.async_logout.assert_called_once()
        mock_auth.update_auth_credentials.assert_called_once_with(
            "new_user", "new_password"
        )
        mock_auth.async_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_attempt_login_as_current_user(self):
        mock_auth = AsyncMock(spec=Auth)

        user_data = {"name": "test_user", "id": 123}
        user = User(user_data, mock_auth)

        await user._attempt_login_as_current_user("test_password")

        mock_auth.async_logout.assert_called_once()
        mock_auth.update_auth_credentials.assert_called_once_with(
            "test_user", "test_password"
        )
        mock_auth.async_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_attempt_login_as_current_user_login_failure(self):
        mock_auth = AsyncMock(spec=Auth)
        mock_auth.async_login.side_effect = CameDomoticAuthError("Login failed")

        user_data = {"name": "test_user", "id": 123}
        user = User(user_data, mock_auth)

        with pytest.raises(CameDomoticAuthError, match="Login failed"):
            await user._attempt_login_as_current_user("test_password")

        mock_auth.async_logout.assert_called_once()
        mock_auth.update_auth_credentials.assert_called_once_with(
            "test_user", "test_password"
        )


class TestUpdateList:
    def test_init_with_data(self):
        updates = UpdateList(STATUS_UPDATE_RESP.get("result"))
        assert updates.data == STATUS_UPDATE_RESP.get("result")

    def test_init_without_data(self):
        updates = UpdateList()
        assert updates.data == []

    def test_init_with_empty_data(self):
        updates = UpdateList({})
        assert updates.data == []

    def test_init_with_non_dict_data(self):
        updates = UpdateList(12345)
        assert updates.data == []


class TestLight:
    def test_initialization(self, light_data_on_off, auth_instance):
        light = Light(light_data_on_off, auth_instance)
        assert light.raw_data == light_data_on_off
        assert light.auth == auth_instance

        # Test post_init validation
        with pytest.raises(ValueError):
            Opening({"name": "Test"}, auth_instance)  # Missing act_id

    def test_properties(self, light_data_dimmable, auth_instance):
        light = Light(light_data_dimmable, auth_instance)
        assert light.act_id == light_data_dimmable["act_id"]
        assert light.floor_ind == light_data_dimmable["floor_ind"]
        assert light.name == light_data_dimmable["name"]
        assert light.room_ind == light_data_dimmable["room_ind"]
        assert light.status == LightStatus(light_data_dimmable["status"])
        assert light.type == LightType(light_data_dimmable["type"])
        assert light.perc == light_data_dimmable["perc"]

    def test_unknown_type(self, auth_instance):
        unknown_light_data = {
            "act_id": 1,
            "floor_ind": 2,
            "name": "Unknown Light Type",
            "room_ind": 3,
            "status": 1,
            "type": "UNKNOWN_TYPE_FROM_API",
        }

        light = Light(unknown_light_data, auth_instance)

        assert light.raw_data == unknown_light_data
        assert light.name == "Unknown Light Type"
        assert light.type == LightType.UNKNOWN
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
    async def test_async_set_status(
        self,
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
    async def test_async_set_status_invalid_brightness(
        self,
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

    def test_edge_case_missing_optional_field(self, auth_instance):
        light_data = {
            "act_id": 1,
            "name": "Test Light",
            "status": 1,
            # Missing optional fields like floor_ind, room_ind, perc, etc.
        }

        light = Light(light_data, auth_instance)

        assert light.name == "Test Light"
        assert light.act_id == 1
        assert light.status == LightStatus.ON

    def test_status_unknown_value(self, auth_instance):
        light_data = {
            "act_id": 1,
            "name": "Test Light",
            "status": 999,  # Unknown status value
            "type": "STEP_STEP",
        }

        light = Light(light_data, auth_instance)

        with pytest.raises(ValueError):
            status = light.status  # noqa: F841

    def test_auth_type_validation(self):
        light_data = {
            "act_id": 1,
            "name": "Test Light",
            "status": 1,
            "type": "STEP_STEP",
        }

        # Test with non-Auth object (string)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got str"
        ):
            Light(light_data, "not_an_auth_instance")

        # Test with non-Auth object (dict)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got dict"
        ):
            Light(light_data, {"fake": "auth"})

    @pytest.mark.asyncio
    @patch.object(Auth, "async_get_valid_client_id", return_value="test_client")
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_unknown_type_warning_in_async_set_status(
        self, mock_send_command, mock_get_client_id, auth_instance, caplog
    ):
        import logging

        light_data = {
            "act_id": 1,
            "name": "Unknown Type Light",
            "status": 1,
            "type": "UNKNOWN_TYPE_FROM_API",
        }

        light = Light(light_data, auth_instance)

        assert light.type == LightType.UNKNOWN

        with caplog.at_level(logging.WARNING):
            await light.async_set_status(LightStatus.ON)

        assert (
            "Attempting to set status for light 'Unknown Type Light' (ID: 1) with UNKNOWN type"
            in caplog.text
        )
        assert "Command might fail or have unintended effects" in caplog.text

        mock_send_command.assert_called_once()


class TestOpening:
    def test_status_enum(self):
        assert OpeningStatus.STOPPED.value == 0
        assert OpeningStatus.OPENING.value == 1
        assert OpeningStatus.CLOSING.value == 2

    def test_type_enum(self):
        assert OpeningType.SHUTTER.value == 0
        assert OpeningType.UNKNOWN.value == -1

    def test_unknown_type(self, auth_instance):
        unknown_opening_data = {
            "open_act_id": 10,
            "close_act_id": 11,
            "floor_ind": 1,
            "name": "Unknown Opening Type",
            "room_ind": 2,
            "status": 0,
            "type": 999,
            "partial": [],
        }

        opening = Opening(unknown_opening_data, auth_instance)

        assert opening.raw_data == unknown_opening_data
        assert opening.name == "Unknown Opening Type"
        assert opening.type == OpeningType.UNKNOWN
        assert opening.open_act_id == 10
        assert opening.close_act_id == 11

    def test_unknown_status(self, auth_instance):
        unknown_status_data = {
            "open_act_id": 10,
            "close_act_id": 11,
            "floor_ind": 1,
            "name": "Unknown Status Opening",
            "room_ind": 2,
            "status": 999,
            "type": 0,
            "partial": [],
        }

        opening = Opening(unknown_status_data, auth_instance)

        assert opening.raw_data == unknown_status_data
        assert opening.name == "Unknown Status Opening"
        assert opening.status == OpeningStatus.UNKNOWN
        assert opening.type == OpeningType.SHUTTER
        assert opening.open_act_id == 10
        assert opening.close_act_id == 11

    def test_initialization(self, opening_data_shutter_stopped, auth_instance):
        opening = Opening(opening_data_shutter_stopped, auth_instance)
        assert opening.raw_data == opening_data_shutter_stopped
        assert opening.auth == auth_instance

        # Test post_init validation
        with pytest.raises(ValueError):
            Opening({"open_act_id": 1}, auth_instance)  # Missing close_act_id
        with pytest.raises(ValueError):
            Opening({"close_act_id": 2}, auth_instance)  # Missing open_act_id

    def test_properties(self, opening_data_awning_opening, auth_instance):
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
    async def test_async_set_status(
        self,
        mock_send_command,
        mock_get_client_id,  # pylint: disable=unused-argument
        opening_data_shutter_stopped,
        auth_instance,
    ):
        opening = Opening(opening_data_shutter_stopped, auth_instance)
        initial_cseq = auth_instance.cseq  # noqa: F841

        # Test setting status to OPENING
        await opening.async_set_status(OpeningStatus.OPENING)

        expected_payload_opening = {
            "act_id": opening.open_act_id,
            "cmd_name": "opening_move_req",
            "wanted_status": OpeningStatus.OPENING.value,
        }
        mock_send_command.assert_called_with(expected_payload_opening)
        assert opening.status == OpeningStatus.OPENING

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

    def test_auth_type_validation(self):
        opening_data = {
            "open_act_id": 10,
            "close_act_id": 11,
            "name": "Test Opening",
            "status": 0,
            "type": 0,
        }

        # Test with non-Auth object (string)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got str"
        ):
            Opening(opening_data, "not_an_auth_instance")

        # Test with non-Auth object (dict)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got dict"
        ):
            Opening(opening_data, {"fake": "auth"})


class TestFloor:
    def test_initialization(self):
        floor_data = {"floor_ind": 1, "name": "Ground Floor"}

        floor = Floor(floor_data)

        assert floor.raw_data == floor_data
        assert floor.id == 1
        assert floor.name == "Ground Floor"

    def test_initialization_missing_id(self):
        floor_data = {"name": "Ground Floor"}

        with pytest.raises(
            ValueError, match="Data is missing required keys: floor_ind"
        ):
            Floor(floor_data)

    def test_initialization_missing_name(self):
        floor_data = {"floor_ind": 1}

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            Floor(floor_data)

    def test_initialization_missing_multiple_keys(self):
        floor_data = {}

        with pytest.raises(
            ValueError, match="Data is missing required keys: floor_ind, name"
        ):
            Floor(floor_data)

    def test_initialization_non_dict_data(self):
        with pytest.raises(ValueError, match="Provided data must be a dictionary"):
            Floor("not a dict")

    def test_properties_with_string_id(self):
        floor_data = {"floor_ind": "2", "name": "First Floor"}

        floor = Floor(floor_data)

        assert floor.id == "2"  # Returns as-is from raw_data
        assert floor.name == "First Floor"


class TestRoom:
    def test_initialization(self):
        room_data = {"room_ind": 5, "name": "Living Room", "floor_ind": 1}

        room = Room(room_data)

        assert room.raw_data == room_data
        assert room.id == 5
        assert room.name == "Living Room"
        assert room.floor_id == 1

    def test_initialization_missing_id(self):
        room_data = {"name": "Living Room", "floor_ind": 1}

        with pytest.raises(ValueError, match="Data is missing required keys: room_ind"):
            Room(room_data)

    def test_initialization_missing_name(self):
        room_data = {"room_ind": 5, "floor_ind": 1}

        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            Room(room_data)

    def test_initialization_missing_floor_id(self):
        room_data = {"room_ind": 5, "name": "Living Room"}

        with pytest.raises(
            ValueError, match="Data is missing required keys: floor_ind"
        ):
            Room(room_data)

    def test_initialization_missing_multiple_keys(self):
        room_data = {"name": "Living Room"}

        with pytest.raises(
            ValueError,
            match="Data is missing required keys: room_ind, floor_ind",
        ):
            Room(room_data)

    def test_initialization_missing_all_keys(self):
        room_data = {}

        with pytest.raises(
            ValueError,
            match="Data is missing required keys: room_ind, name, floor_ind",
        ):
            Room(room_data)

    def test_initialization_non_dict_data(self):
        with pytest.raises(ValueError, match="Provided data must be a dictionary"):
            Room("not a dict")

    def test_properties_with_string_ids(self):
        room_data = {"room_ind": "10", "name": "Kitchen", "floor_ind": "2"}

        room = Room(room_data)

        assert room.id == "10"  # Returns as-is from raw_data
        assert room.name == "Kitchen"
        assert room.floor_id == "2"  # Returns as-is from raw_data
