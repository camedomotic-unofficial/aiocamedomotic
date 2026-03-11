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
from aiocamedomotic.const import (
    _DEVICE_TYPE_TO_FEATURE,
    _UPDATE_CMD_TO_DEVICE_TYPE,
    DeviceType,
    UpdateIndicator,
    _ServerFeature,
)
from aiocamedomotic.errors import CameDomoticAuthError
from aiocamedomotic.models import (
    AnalogSensor,
    DeviceUpdate,
    DigitalInput,
    DigitalInputStatus,
    DigitalInputType,
    DigitalInputUpdate,
    Floor,
    Light,
    LightStatus,
    LightType,
    LightUpdate,
    Opening,
    OpeningStatus,
    OpeningType,
    OpeningUpdate,
    PlantUpdate,
    Room,
    Scenario,
    ScenarioStatus,
    ScenarioUpdate,
    ServerInfo,
    ThermoZone,
    ThermoZoneFanSpeed,
    ThermoZoneMode,
    ThermoZoneSeason,
    ThermoZoneStatus,
    ThermoZoneUpdate,
    UpdateList,
    User,
    get_update_device_type,
    parse_update,
)
from tests.aiocamedomotic.mocked_responses import STATUS_UPDATE_RESP


class TestDeviceType:
    def test_enum_values(self):
        assert DeviceType.ENERGY_SENSOR == -2
        assert DeviceType.ANALOG_SENSOR == -1
        assert DeviceType.LIGHT == 0
        assert DeviceType.OPENING == 1
        assert DeviceType.THERMOSTAT == 2
        assert DeviceType.PAGE == 3
        assert DeviceType.SCENARIO == 4
        assert DeviceType.CAMERA == 5
        assert DeviceType.SECURITY_PANEL == 6
        assert DeviceType.SECURITY_AREA == 7
        assert DeviceType.SECURITY_SCENARIO == 8
        assert DeviceType.SECURITY_INPUT == 9
        assert DeviceType.SECURITY_OUTPUT == 10
        assert DeviceType.GENERIC_RELAY == 11
        assert DeviceType.GENERIC_TEXT == 12
        assert DeviceType.SOUND_ZONE == 13
        assert DeviceType.DIGITAL_INPUT == 14

    def test_lookup_by_value(self):
        assert DeviceType(0) == DeviceType.LIGHT
        assert DeviceType(-2) == DeviceType.ENERGY_SENSOR
        assert DeviceType(14) == DeviceType.DIGITAL_INPUT

    def test_unknown_value_raises(self):
        with pytest.raises(ValueError):
            DeviceType(99)

    def test_update_cmd_to_device_type_mapping(self):
        # Traffic-observed indicator names
        assert _UPDATE_CMD_TO_DEVICE_TYPE["light_switch_ind"] == DeviceType.LIGHT
        assert _UPDATE_CMD_TO_DEVICE_TYPE["opening_move_ind"] == DeviceType.OPENING
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["thermo_zone_info_ind"] == DeviceType.THERMOSTAT
        )
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["digitalin_status_ind"]
            == DeviceType.DIGITAL_INPUT
        )
        assert _UPDATE_CMD_TO_DEVICE_TYPE["scenario_status_ind"] == DeviceType.SCENARIO
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["scenario_activation_ind"] == DeviceType.SCENARIO
        )
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["meter_instant_power_ind"]
            == DeviceType.ENERGY_SENSOR
        )
        # API_reference.md variant names (firmware compatibility)
        assert _UPDATE_CMD_TO_DEVICE_TYPE["light_update_ind"] == DeviceType.LIGHT
        assert _UPDATE_CMD_TO_DEVICE_TYPE["opening_update_ind"] == DeviceType.OPENING
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["relay_update_ind"] == DeviceType.GENERIC_RELAY
        )
        assert _UPDATE_CMD_TO_DEVICE_TYPE["thermo_update_ind"] == DeviceType.THERMOSTAT
        assert (
            _UPDATE_CMD_TO_DEVICE_TYPE["digitalin_update_ind"]
            == DeviceType.DIGITAL_INPUT
        )
        assert _UPDATE_CMD_TO_DEVICE_TYPE["scenario_user_ind"] == DeviceType.SCENARIO

    def test_device_type_to_feature_mapping(self):
        assert _DEVICE_TYPE_TO_FEATURE[DeviceType.LIGHT] == _ServerFeature.LIGHTS
        assert _DEVICE_TYPE_TO_FEATURE[DeviceType.OPENING] == _ServerFeature.OPENINGS
        assert (
            _DEVICE_TYPE_TO_FEATURE[DeviceType.GENERIC_RELAY] == _ServerFeature.RELAYS
        )
        assert (
            _DEVICE_TYPE_TO_FEATURE[DeviceType.THERMOSTAT]
            == _ServerFeature.THERMOREGULATION
        )
        assert _DEVICE_TYPE_TO_FEATURE[DeviceType.SCENARIO] == _ServerFeature.SCENARIOS
        assert (
            _DEVICE_TYPE_TO_FEATURE[DeviceType.DIGITAL_INPUT]
            == _ServerFeature.DIGITALIN
        )
        assert (
            _DEVICE_TYPE_TO_FEATURE[DeviceType.ENERGY_SENSOR] == _ServerFeature.ENERGY
        )


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
    async def test_async_set_as_current_user_failure_restores_credentials(self):
        mock_auth = AsyncMock(spec=Auth)
        backup_credentials = ("old_user", "old_pass", "client_id", 123, 30, 1)
        mock_auth.backup_auth_credentials.return_value = backup_credentials

        user_data = {"name": "new_user", "id": 123}
        user = User(user_data, mock_auth)

        mock_auth.async_logout.side_effect = CameDomoticAuthError("Login failed")

        with pytest.raises(CameDomoticAuthError, match="Login failed"):
            await user.async_set_as_current_user("new_password")

        mock_auth.backup_auth_credentials.assert_called_once()
        mock_auth.restore_auth_credentials.assert_called_once_with(backup_credentials)

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

    def test_get_update_device_type_known(self):
        # Traffic-observed names
        assert (
            get_update_device_type({"cmd_name": "light_switch_ind"}) == DeviceType.LIGHT
        )
        assert (
            get_update_device_type({"cmd_name": "opening_move_ind"})
            == DeviceType.OPENING
        )
        assert (
            get_update_device_type({"cmd_name": "thermo_zone_info_ind"})
            == DeviceType.THERMOSTAT
        )
        assert (
            get_update_device_type({"cmd_name": "digitalin_status_ind"})
            == DeviceType.DIGITAL_INPUT
        )
        assert (
            get_update_device_type({"cmd_name": "scenario_status_ind"})
            == DeviceType.SCENARIO
        )
        # Legacy names
        assert (
            get_update_device_type({"cmd_name": "light_update_ind"}) == DeviceType.LIGHT
        )
        assert (
            get_update_device_type({"cmd_name": "opening_update_ind"})
            == DeviceType.OPENING
        )

    def test_get_update_device_type_unknown(self):
        assert get_update_device_type({"cmd_name": "plant_update_ind"}) is None

    def test_get_update_device_type_missing_cmd_name(self):
        assert get_update_device_type({}) is None


class TestDeviceUpdate:
    def test_parse_light_update(self):
        raw = {
            "cmd_name": "light_switch_ind",
            "act_id": 32,
            "name": "Lampada studio",
            "floor_ind": 37,
            "room_ind": 42,
            "status": 0,
            "type": "DIMMER",
            "perc": 94,
        }
        update = parse_update(raw)
        assert isinstance(update, LightUpdate)
        assert update.act_id == 32
        assert update.name == "Lampada studio"
        assert update.floor_ind == 37
        assert update.room_ind == 42
        assert update.status == LightStatus.OFF
        assert update.light_type == LightType.DIMMER
        assert update.perc == 94
        assert update.rgb is None
        assert update.device_type == DeviceType.LIGHT
        assert update.device_id == 32
        assert update.update_indicator == UpdateIndicator.LIGHT

    def test_parse_light_update_rgb(self):
        raw = {
            "cmd_name": "light_switch_ind",
            "act_id": 10,
            "name": "Led RGB",
            "floor_ind": 1,
            "room_ind": 2,
            "status": 1,
            "type": "RGB",
            "perc": 50,
            "rgb": [255, 128, 0],
        }
        update = parse_update(raw)
        assert isinstance(update, LightUpdate)
        assert update.light_type == LightType.RGB
        assert update.rgb == [255, 128, 0]

    def test_parse_light_update_unknown_type(self):
        raw = {
            "cmd_name": "light_switch_ind",
            "act_id": 10,
            "name": "Led",
            "status": 1,
            "type": "SOMETHING_NEW",
        }
        update = parse_update(raw)
        assert isinstance(update, LightUpdate)
        assert update.light_type == LightType.UNKNOWN

    def test_parse_opening_update(self):
        raw = {
            "cmd_name": "opening_move_ind",
            "open_act_id": 62,
            "close_act_id": 63,
            "name": "Tapparella Bagno Camera matrimo",
            "floor_ind": 37,
            "room_ind": 54,
            "status": 2,
        }
        update = parse_update(raw)
        assert isinstance(update, OpeningUpdate)
        assert update.open_act_id == 62
        assert update.close_act_id == 63
        assert update.name == "Tapparella Bagno Camera matrimo"
        assert update.status == OpeningStatus.CLOSING
        assert update.device_type == DeviceType.OPENING
        assert update.device_id == 62
        assert update.update_indicator == UpdateIndicator.OPENING

    def test_parse_opening_update_unknown_status(self):
        raw = {
            "cmd_name": "opening_move_ind",
            "open_act_id": 1,
            "close_act_id": 2,
            "name": "Test",
            "status": 99,
        }
        update = parse_update(raw)
        assert isinstance(update, OpeningUpdate)
        assert update.status == OpeningStatus.UNKNOWN

    def test_parse_thermo_zone_update(self):
        raw = {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 76,
            "name": "Bagno",
            "floor_ind": 37,
            "room_ind": 45,
            "temp_dec": 212,
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
        }
        update = parse_update(raw)
        assert isinstance(update, ThermoZoneUpdate)
        assert update.act_id == 76
        assert update.name == "Bagno"
        assert update.temperature == 21.2
        assert update.status == ThermoZoneStatus.OFF
        assert update.mode == ThermoZoneMode.AUTO
        assert update.set_point == 34.9
        assert update.season == ThermoZoneSeason.WINTER
        assert update.device_type == DeviceType.THERMOSTAT
        assert update.device_id == 76
        assert update.update_indicator == UpdateIndicator.THERMOSTAT
        assert update.t1 == 19.0
        assert update.t2 == 20.0
        assert update.t3 == 21.0

    def test_parse_thermo_zone_update_fan_speed(self):
        raw = {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 10,
            "name": "Office",
            "fan_speed": 3,
            "dehumidifier": {"enabled": 1, "setpoint": 60},
        }
        update = parse_update(raw)
        assert isinstance(update, ThermoZoneUpdate)
        assert update.fan_speed == ThermoZoneFanSpeed.FAST
        assert update.dehumidifier_enabled is True
        assert update.dehumidifier_setpoint == 60.0

    def test_parse_thermo_zone_update_missing_optional_fields(self):
        raw = {
            "cmd_name": "thermo_zone_info_ind",
            "act_id": 10,
            "name": "Minimal",
        }
        update = parse_update(raw)
        assert isinstance(update, ThermoZoneUpdate)
        assert update.fan_speed == ThermoZoneFanSpeed.UNKNOWN
        assert update.dehumidifier_enabled is False
        assert update.dehumidifier_setpoint is None
        assert update.t1 is None
        assert update.t2 is None
        assert update.t3 is None

    def test_parse_scenario_update(self):
        raw = {
            "cmd_name": "scenario_status_ind",
            "id": 8,
            "name": "Tapparelle notte chiudi",
            "scenario_status": 1,
        }
        update = parse_update(raw)
        assert isinstance(update, ScenarioUpdate)
        assert update.id == 8
        assert update.name == "Tapparelle notte chiudi"
        assert update.scenario_status == ScenarioStatus.TRIGGERED
        assert update.device_type == DeviceType.SCENARIO
        assert update.device_id == 8
        assert update.update_indicator == UpdateIndicator.SCENARIO_STATUS

    def test_parse_scenario_update_missing_status(self):
        raw = {
            "cmd_name": "scenario_status_ind",
            "id": 1,
            "name": "Test",
        }
        update = parse_update(raw)
        assert isinstance(update, ScenarioUpdate)
        assert update.scenario_status == ScenarioStatus.UNKNOWN

    def test_parse_digitalin_update(self):
        raw = {
            "name": "Pulsante faretti sala pranzo anticamera",
            "act_id": 84,
            "type": 1,
            "addr": 96,
            "ack": 0,
            "status": 0,
            "radio_node_id": "00000000",
            "rf_radio_link_quality": 0,
            "utc_time": 1772894788,
            "cmd_name": "digitalin_status_ind",
        }
        update = parse_update(raw)
        assert isinstance(update, DigitalInputUpdate)
        assert update.act_id == 84
        assert update.name == "Pulsante faretti sala pranzo anticamera"
        assert update.status == 0
        assert update.addr == 96
        assert update.utc_time == 1772894788
        assert update.device_type == DeviceType.DIGITAL_INPUT
        assert update.device_id == 84
        assert update.update_indicator == UpdateIndicator.DIGITAL_INPUT

    def test_parse_plant_update(self):
        raw = {"cmd_name": "plant_update_ind"}
        update = parse_update(raw)
        assert isinstance(update, PlantUpdate)
        assert update.is_plant_update is True
        assert update.device_type is None
        assert update.update_indicator == UpdateIndicator.PLANT

    def test_parse_unknown_update(self):
        raw = {"cmd_name": "some_future_ind", "data": 42}
        update = parse_update(raw)
        assert isinstance(update, DeviceUpdate)
        assert not isinstance(update, LightUpdate)
        assert update.cmd_name == "some_future_ind"
        assert update.device_type is None
        assert update.update_indicator is None
        assert update.raw_data == raw

    def test_device_update_device_id_act_id(self):
        raw = {"cmd_name": "x", "act_id": 10}
        assert DeviceUpdate(raw_data=raw).device_id == 10

    def test_device_update_device_id_open_act_id(self):
        raw = {"cmd_name": "x", "open_act_id": 20}
        assert DeviceUpdate(raw_data=raw).device_id == 20

    def test_device_update_device_id_id(self):
        raw = {"cmd_name": "x", "id": 30}
        assert DeviceUpdate(raw_data=raw).device_id == 30

    def test_device_update_device_id_none(self):
        raw = {"cmd_name": "x"}
        assert DeviceUpdate(raw_data=raw).device_id is None

    def test_parse_legacy_cmd_names(self):
        assert isinstance(
            parse_update({"cmd_name": "light_update_ind", "act_id": 1, "status": 0}),
            LightUpdate,
        )
        assert isinstance(
            parse_update(
                {
                    "cmd_name": "opening_update_ind",
                    "open_act_id": 1,
                    "close_act_id": 2,
                    "status": 0,
                }
            ),
            OpeningUpdate,
        )
        assert isinstance(
            parse_update(
                {"cmd_name": "thermo_update_ind", "act_id": 1, "temp_dec": 200}
            ),
            ThermoZoneUpdate,
        )
        assert isinstance(
            parse_update(
                {"cmd_name": "digitalin_update_ind", "act_id": 1, "status": 0}
            ),
            DigitalInputUpdate,
        )
        assert isinstance(
            parse_update(
                {"cmd_name": "scenario_user_ind", "id": 1, "scenario_status": 0}
            ),
            ScenarioUpdate,
        )


class TestUpdateListEnhanced:
    def _make_mixed_updates(self):
        return [
            {
                "cmd_name": "thermo_zone_info_ind",
                "act_id": 76,
                "name": "Bagno",
                "floor_ind": 37,
                "room_ind": 45,
                "temp_dec": 212,
                "status": 0,
                "mode": 2,
                "set_point": 349,
                "season": "winter",
            },
            {
                "cmd_name": "light_switch_ind",
                "act_id": 32,
                "name": "Lampada studio",
                "floor_ind": 37,
                "room_ind": 42,
                "status": 0,
                "type": "DIMMER",
                "perc": 94,
            },
            {
                "cmd_name": "scenario_status_ind",
                "id": 5,
                "name": "Tapparelle apri",
                "scenario_status": 1,
            },
            {
                "cmd_name": "digitalin_status_ind",
                "act_id": 84,
                "name": "Pulsante",
                "type": 1,
                "addr": 96,
                "ack": 0,
                "status": 0,
                "radio_node_id": "00000000",
                "rf_radio_link_quality": 0,
                "utc_time": 1772894788,
            },
            {
                "cmd_name": "opening_move_ind",
                "open_act_id": 62,
                "close_act_id": 63,
                "name": "Tapparella",
                "floor_ind": 37,
                "room_ind": 54,
                "status": 2,
            },
        ]

    def test_get_by_device_type(self):
        updates = UpdateList(self._make_mixed_updates())
        thermo = updates.get_by_device_type(DeviceType.THERMOSTAT)
        assert len(thermo) == 1
        assert thermo[0]["act_id"] == 76

    def test_get_by_device_type_empty(self):
        updates = UpdateList(self._make_mixed_updates())
        relays = updates.get_by_device_type(DeviceType.GENERIC_RELAY)
        assert relays == []

    def test_get_typed_updates(self):
        updates = UpdateList(self._make_mixed_updates())
        typed = updates.get_typed_updates()
        assert len(typed) == 5
        assert isinstance(typed[0], ThermoZoneUpdate)
        assert isinstance(typed[1], LightUpdate)
        assert isinstance(typed[2], ScenarioUpdate)
        assert isinstance(typed[3], DigitalInputUpdate)
        assert isinstance(typed[4], OpeningUpdate)

    def test_get_typed_by_device_type(self):
        updates = UpdateList(self._make_mixed_updates())
        lights = updates.get_typed_by_device_type(DeviceType.LIGHT)
        assert len(lights) == 1
        assert isinstance(lights[0], LightUpdate)
        assert lights[0].act_id == 32

    def test_has_plant_update_false(self):
        updates = UpdateList(self._make_mixed_updates())
        assert updates.has_plant_update is False

    def test_has_plant_update_true(self):
        data = self._make_mixed_updates()
        data.append({"cmd_name": "plant_update_ind"})
        updates = UpdateList(data)
        assert updates.has_plant_update is True

    def test_backward_compat_iteration(self):
        raw_data = self._make_mixed_updates()
        updates = UpdateList(raw_data)
        for item in updates:
            assert isinstance(item, dict)
        assert list(updates) == raw_data

    def test_empty_update_list_methods(self):
        updates = UpdateList([])
        assert updates.get_by_device_type(DeviceType.LIGHT) == []
        assert updates.get_typed_updates() == []
        assert updates.get_typed_by_device_type(DeviceType.LIGHT) == []
        assert updates.has_plant_update is False


class TestUpdateClassesRealWorld:
    """Tests using anonymized payloads derived from real API traffic patterns."""

    @pytest.mark.parametrize(
        "raw, exp_status, exp_type, exp_perc, exp_floor, exp_room",
        [
            pytest.param(
                {
                    "cmd_name": "light_switch_ind",
                    "act_id": 201,
                    "name": "My ceiling spots",
                    "floor_ind": 5,
                    "room_ind": 11,
                    "status": 0,
                    "type": "STEP_STEP",
                },
                LightStatus.OFF,
                LightType.STEP_STEP,
                100,
                5,
                11,
                id="step_step_off_no_perc",
            ),
            pytest.param(
                {
                    "cmd_name": "light_switch_ind",
                    "act_id": 202,
                    "name": "My dimmable lamp",
                    "floor_ind": 3,
                    "room_ind": 7,
                    "status": 1,
                    "type": "DIMMER",
                    "perc": 14,
                },
                LightStatus.ON,
                LightType.DIMMER,
                14,
                3,
                7,
                id="dimmer_on_low_brightness",
            ),
            pytest.param(
                {
                    "cmd_name": "light_switch_ind",
                    "act_id": 203,
                    "name": "My desk lamp",
                    "floor_ind": 8,
                    "room_ind": 12,
                    "status": 1,
                    "type": "DIMMER",
                    "perc": 94,
                },
                LightStatus.ON,
                LightType.DIMMER,
                94,
                8,
                12,
                id="dimmer_on_high_brightness",
            ),
            pytest.param(
                {
                    "cmd_name": "light_switch_ind",
                    "act_id": 204,
                    "name": "My living room light",
                    "floor_ind": 3,
                    "room_ind": 7,
                    "status": 0,
                    "type": "DIMMER",
                    "perc": 54,
                },
                LightStatus.OFF,
                LightType.DIMMER,
                54,
                3,
                7,
                id="dimmer_off_retains_perc",
            ),
        ],
    )
    def test_light_update_real_world(
        self, raw, exp_status, exp_type, exp_perc, exp_floor, exp_room
    ):
        update = parse_update(raw)
        assert isinstance(update, LightUpdate)
        assert update.act_id == raw["act_id"]
        assert update.name == raw["name"]
        assert update.floor_ind == exp_floor
        assert update.room_ind == exp_room
        assert update.status == exp_status
        assert update.light_type == exp_type
        assert update.perc == exp_perc
        assert update.rgb is None
        assert update.device_type == DeviceType.LIGHT
        assert update.device_id == raw["act_id"]
        assert update.cmd_name == "light_switch_ind"
        assert update.update_indicator == UpdateIndicator.LIGHT

    @pytest.mark.parametrize(
        "raw, exp_status",
        [
            pytest.param(
                {
                    "cmd_name": "opening_move_ind",
                    "open_act_id": 301,
                    "close_act_id": 302,
                    "name": "My office shutter",
                    "floor_ind": 8,
                    "room_ind": 12,
                    "status": 2,
                },
                OpeningStatus.CLOSING,
                id="closing",
            ),
            pytest.param(
                {
                    "cmd_name": "opening_move_ind",
                    "open_act_id": 303,
                    "close_act_id": 304,
                    "name": "My kitchen window shutter",
                    "floor_ind": 5,
                    "room_ind": 9,
                    "status": 0,
                },
                OpeningStatus.STOPPED,
                id="stopped",
            ),
            pytest.param(
                {
                    "cmd_name": "opening_move_ind",
                    "open_act_id": 303,
                    "close_act_id": 304,
                    "name": "My kitchen window shutter",
                    "floor_ind": 5,
                    "room_ind": 9,
                    "status": 1,
                },
                OpeningStatus.OPENING,
                id="opening_same_device",
            ),
            pytest.param(
                {
                    "cmd_name": "opening_move_ind",
                    "open_act_id": 305,
                    "close_act_id": 306,
                    "name": "My living room shutter",
                    "floor_ind": 5,
                    "room_ind": 7,
                    "status": 1,
                },
                OpeningStatus.OPENING,
                id="opening_different_device",
            ),
        ],
    )
    def test_opening_update_real_world(self, raw, exp_status):
        update = parse_update(raw)
        assert isinstance(update, OpeningUpdate)
        assert update.open_act_id == raw["open_act_id"]
        assert update.close_act_id == raw["close_act_id"]
        assert update.name == raw["name"]
        assert update.floor_ind == raw["floor_ind"]
        assert update.room_ind == raw["room_ind"]
        assert update.status == exp_status
        assert update.device_type == DeviceType.OPENING
        assert update.device_id == raw["open_act_id"]
        assert update.cmd_name == "opening_move_ind"
        assert update.update_indicator == UpdateIndicator.OPENING

    @pytest.mark.parametrize(
        "raw, exp_temp, exp_set_point",
        [
            pytest.param(
                {
                    "cmd_name": "thermo_zone_info_ind",
                    "act_id": 401,
                    "name": "My zone A",
                    "floor_ind": 8,
                    "room_ind": 14,
                    "temp_dec": 212,
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
                21.2,
                34.9,
                id="zone_a",
            ),
            pytest.param(
                {
                    "cmd_name": "thermo_zone_info_ind",
                    "act_id": 402,
                    "name": "My zone B",
                    "floor_ind": 5,
                    "room_ind": 11,
                    "temp_dec": 219,
                    "status": 0,
                    "mode": 2,
                    "set_point": 310,
                    "season": "winter",
                    "antifreeze": 30,
                    "t1": 185,
                    "t2": 195,
                    "t3": 205,
                    "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
                    "reason": 1,
                },
                21.9,
                31.0,
                id="zone_b",
            ),
            pytest.param(
                {
                    "cmd_name": "thermo_zone_info_ind",
                    "act_id": 403,
                    "name": "My zone C",
                    "floor_ind": 8,
                    "room_ind": 16,
                    "temp_dec": 210,
                    "status": 0,
                    "mode": 2,
                    "set_point": 341,
                    "season": "winter",
                    "antifreeze": 30,
                    "t1": 185,
                    "t2": 198,
                    "t3": 210,
                    "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
                    "reason": 1,
                },
                21.0,
                34.1,
                id="zone_c",
            ),
            pytest.param(
                {
                    "cmd_name": "thermo_zone_info_ind",
                    "act_id": 404,
                    "name": "My zone D",
                    "floor_ind": 8,
                    "room_ind": 12,
                    "temp_dec": 219,
                    "status": 0,
                    "mode": 2,
                    "set_point": 206,
                    "season": "winter",
                    "antifreeze": 30,
                    "t1": 175,
                    "t2": 200,
                    "t3": 210,
                    "thermo_algo": {"type": "D", "diff_t_dec": 2, "pi_set_in_use": 1},
                    "reason": 1,
                },
                21.9,
                20.6,
                id="zone_d",
            ),
        ],
    )
    def test_thermo_zone_update_real_world(self, raw, exp_temp, exp_set_point):
        update = parse_update(raw)
        assert isinstance(update, ThermoZoneUpdate)
        assert update.act_id == raw["act_id"]
        assert update.name == raw["name"]
        assert update.floor_ind == raw["floor_ind"]
        assert update.room_ind == raw["room_ind"]
        assert update.temperature == pytest.approx(exp_temp)
        assert update.set_point == pytest.approx(exp_set_point)
        assert update.status == ThermoZoneStatus.OFF
        assert update.mode == ThermoZoneMode.AUTO
        assert update.season == ThermoZoneSeason.WINTER
        assert update.device_type == DeviceType.THERMOSTAT
        assert update.device_id == raw["act_id"]
        assert update.cmd_name == "thermo_zone_info_ind"
        assert update.update_indicator == UpdateIndicator.THERMOSTAT

    @pytest.mark.parametrize(
        "raw, exp_scenario_status, exp_indicator",
        [
            pytest.param(
                {
                    "cmd_name": "scenario_status_ind",
                    "id": 501,
                    "name": "My scenario 1",
                    "scenario_status": 1,
                },
                ScenarioStatus.TRIGGERED,
                UpdateIndicator.SCENARIO_STATUS,
                id="status_ind_triggered",
            ),
            pytest.param(
                {
                    "cmd_name": "scenario_status_ind",
                    "id": 501,
                    "name": "My scenario 1",
                    "scenario_status": 2,
                },
                ScenarioStatus.ACTIVE,
                UpdateIndicator.SCENARIO_STATUS,
                id="status_ind_active",
            ),
            pytest.param(
                {
                    "cmd_name": "scenario_status_ind",
                    "id": 502,
                    "name": "My scenario 2",
                    "scenario_status": 0,
                },
                ScenarioStatus.OFF,
                UpdateIndicator.SCENARIO_STATUS,
                id="status_ind_off",
            ),
            pytest.param(
                {
                    "cmd_name": "scenario_activation_ind",
                    "id": 501,
                    "name": "My scenario 1",
                    "status": 0,
                },
                ScenarioStatus.UNKNOWN,
                UpdateIndicator.SCENARIO_ACTIVATION,
                id="activation_ind_no_scenario_status_key",
            ),
        ],
    )
    def test_scenario_update_real_world(self, raw, exp_scenario_status, exp_indicator):
        update = parse_update(raw)
        assert isinstance(update, ScenarioUpdate)
        assert update.id == raw["id"]
        assert update.name == raw["name"]
        assert update.scenario_status == exp_scenario_status
        assert update.device_type == DeviceType.SCENARIO
        assert update.device_id == raw["id"]
        assert update.update_indicator == exp_indicator

    @pytest.mark.parametrize(
        "raw",
        [
            pytest.param(
                {
                    "name": "My button A",
                    "act_id": 601,
                    "type": 1,
                    "addr": 30,
                    "ack": 0,
                    "status": 0,
                    "radio_node_id": "00000000",
                    "rf_radio_link_quality": 0,
                    "utc_time": 1700000001,
                    "cmd_name": "digitalin_status_ind",
                },
                id="button_pressed",
            ),
            pytest.param(
                {
                    "name": "My button A",
                    "act_id": 601,
                    "type": 1,
                    "addr": 30,
                    "ack": 0,
                    "status": 1,
                    "radio_node_id": "00000000",
                    "rf_radio_link_quality": 0,
                    "utc_time": 1700000002,
                    "cmd_name": "digitalin_status_ind",
                },
                id="button_released",
            ),
            pytest.param(
                {
                    "name": "My button B",
                    "act_id": 602,
                    "type": 1,
                    "addr": 45,
                    "ack": 0,
                    "status": 0,
                    "radio_node_id": "00000000",
                    "rf_radio_link_quality": 0,
                    "utc_time": 1700000010,
                    "cmd_name": "digitalin_status_ind",
                },
                id="different_button_pressed",
            ),
        ],
    )
    def test_digital_input_update_real_world(self, raw):
        update = parse_update(raw)
        assert isinstance(update, DigitalInputUpdate)
        assert update.act_id == raw["act_id"]
        assert update.name == raw["name"]
        assert update.status == raw["status"]
        assert update.addr == raw["addr"]
        assert update.utc_time == raw["utc_time"]
        assert update.device_type == DeviceType.DIGITAL_INPUT
        assert update.device_id == raw["act_id"]
        assert update.cmd_name == "digitalin_status_ind"
        assert update.update_indicator == UpdateIndicator.DIGITAL_INPUT


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

    def test_status_auto(self, auth_instance):
        light_data = {
            "act_id": 1,
            "name": "Auto Light",
            "status": 4,
            "type": "STEP_STEP",
        }

        light = Light(light_data, auth_instance)

        assert light.status == LightStatus.AUTO

    def test_rgb_type(self, light_data_rgb, auth_instance):
        light = Light(light_data_rgb, auth_instance)

        assert light.type == LightType.RGB
        assert light.perc == 75
        assert light.rgb == [255, 128, 0]

    def test_rgb_property_non_rgb_light(self, light_data_on_off, auth_instance):
        light = Light(light_data_on_off, auth_instance)

        assert light.rgb is None

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="my_session_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_rgb(
        self,
        mock_send_command,
        mock_get_client_id,
        light_data_rgb,
        auth_instance,
    ):
        light = Light(light_data_rgb, auth_instance)

        await light.async_set_status(LightStatus.ON, brightness=80, rgb=[0, 255, 0])

        mock_send_command.assert_called_once()
        payload = mock_send_command.call_args[0][0]
        assert payload["wanted_status"] == LightStatus.ON.value
        assert payload["perc"] == 80
        assert payload["rgb"] == [0, 255, 0]
        assert light.rgb == [0, 255, 0]
        assert light.perc == 80

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="my_session_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_rgb_ignored_for_non_rgb(
        self,
        mock_send_command,
        mock_get_client_id,
        light_data_dimmable,
        auth_instance,
    ):
        light = Light(light_data_dimmable, auth_instance)

        await light.async_set_status(LightStatus.ON, brightness=50, rgb=[0, 255, 0])

        payload = mock_send_command.call_args[0][0]
        assert "rgb" not in payload
        assert payload["perc"] == 50
        assert light.rgb is None

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="my_session_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_rgb_brightness_supported(
        self,
        mock_send_command,
        mock_get_client_id,
        light_data_rgb,
        auth_instance,
    ):
        light = Light(light_data_rgb, auth_instance)

        await light.async_set_status(LightStatus.ON, brightness=60)

        payload = mock_send_command.call_args[0][0]
        assert payload["perc"] == 60
        assert "rgb" not in payload

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="my_session_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_rgb_clamps_values(
        self,
        mock_send_command,
        mock_get_client_id,
        light_data_rgb,
        auth_instance,
    ):
        light = Light(light_data_rgb, auth_instance)

        await light.async_set_status(LightStatus.ON, rgb=[300, -10, 128])

        payload = mock_send_command.call_args[0][0]
        assert payload["rgb"] == [255, 0, 128]
        assert light.rgb == [255, 0, 128]

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="my_session_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_auto(
        self,
        mock_send_command,
        mock_get_client_id,
        light_data_on_off,
        auth_instance,
    ):
        light = Light(light_data_on_off, auth_instance)

        await light.async_set_status(LightStatus.AUTO)

        payload = mock_send_command.call_args[0][0]
        assert payload["wanted_status"] == 4
        assert light.status == LightStatus.AUTO

    def test_status_unknown_value(self, auth_instance):
        light_data = {
            "act_id": 1,
            "name": "Test Light",
            "status": 999,  # Unknown status value
            "type": "STEP_STEP",
        }

        light = Light(light_data, auth_instance)

        assert light.status == LightStatus.UNKNOWN

    def test_invalid_act_id_type(self, auth_instance):
        light_data = {
            "act_id": "not_an_int",
            "name": "Test Light",
            "status": 1,
            "type": "STEP_STEP",
        }

        with pytest.raises(ValueError, match="Key 'act_id' expected int, got str"):
            Light(light_data, auth_instance)

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
            "Attempting to set status for light "
            "'Unknown Type Light' (ID: 1) with UNKNOWN type" in caplog.text
        )
        assert "Command might fail or have unintended effects" in caplog.text

        mock_send_command.assert_called_once()


class TestOpening:
    def test_status_enum(self):
        assert OpeningStatus.STOPPED.value == 0
        assert OpeningStatus.OPENING.value == 1
        assert OpeningStatus.CLOSING.value == 2
        assert OpeningStatus.SLAT_OPEN.value == 3
        assert OpeningStatus.SLAT_CLOSE.value == 4

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

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="mock_client_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_slat_open(
        self,
        mock_send_command,
        mock_get_client_id,
        opening_data_shutter_stopped,
        auth_instance,
    ):
        opening = Opening(opening_data_shutter_stopped, auth_instance)

        await opening.async_set_status(OpeningStatus.SLAT_OPEN)

        expected_payload = {
            "act_id": opening.open_act_id,
            "cmd_name": "opening_move_req",
            "wanted_status": OpeningStatus.SLAT_OPEN.value,
        }
        mock_send_command.assert_called_with(expected_payload)
        assert opening.status == OpeningStatus.SLAT_OPEN

    @pytest.mark.asyncio
    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="mock_client_id",
    )
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_status_slat_close(
        self,
        mock_send_command,
        mock_get_client_id,
        opening_data_shutter_stopped,
        auth_instance,
    ):
        opening = Opening(opening_data_shutter_stopped, auth_instance)

        await opening.async_set_status(OpeningStatus.SLAT_CLOSE)

        expected_payload = {
            "act_id": opening.close_act_id,
            "cmd_name": "opening_move_req",
            "wanted_status": OpeningStatus.SLAT_CLOSE.value,
        }
        mock_send_command.assert_called_with(expected_payload)
        assert opening.status == OpeningStatus.SLAT_CLOSE

    def test_status_slat_open_from_raw_data(self, auth_instance):
        data = {
            "open_act_id": 10,
            "close_act_id": 11,
            "name": "Slat Opening",
            "status": 3,
            "type": 0,
            "partial": [],
        }

        opening = Opening(data, auth_instance)

        assert opening.status == OpeningStatus.SLAT_OPEN

    def test_status_slat_close_from_raw_data(self, auth_instance):
        data = {
            "open_act_id": 10,
            "close_act_id": 11,
            "name": "Slat Opening",
            "status": 4,
            "type": 0,
            "partial": [],
        }

        opening = Opening(data, auth_instance)

        assert opening.status == OpeningStatus.SLAT_CLOSE

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


class TestScenario:
    def test_initialization(self, scenario_data_off, auth_instance):
        scenario = Scenario(scenario_data_off, auth_instance)
        assert scenario.raw_data == scenario_data_off
        assert scenario.auth == auth_instance

        # Test post_init validation - missing id
        with pytest.raises(ValueError):
            Scenario({"name": "Test"}, auth_instance)
        # Test post_init validation - missing name
        with pytest.raises(ValueError):
            Scenario({"id": 1}, auth_instance)

    def test_properties(self, scenario_data_on, auth_instance):
        scenario = Scenario(scenario_data_on, auth_instance)
        assert scenario.id == scenario_data_on["id"]
        assert scenario.name == scenario_data_on["name"]
        assert scenario.icon_id == scenario_data_on["icon_id"]
        assert scenario.scenario_status == ScenarioStatus(
            scenario_data_on["scenario_status"]
        )
        assert scenario.status == scenario_data_on["status"]
        assert scenario.user_defined == scenario_data_on["user-defined"]

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_activate(
        self,
        mock_send_command,
        scenario_data_off,
        auth_instance,
    ):
        scenario = Scenario(scenario_data_off, auth_instance)

        await scenario.async_activate()

        expected_payload = {
            "cmd_name": "scenario_activation_req",
            "id": scenario.id,
        }
        mock_send_command.assert_called_once_with(expected_payload)

    def test_active_status(self, auth_instance):
        active_status_data = {
            "id": 5,
            "name": "Tapparelle apri",
            "scenario_status": 2,
            "status": 0,
            "user-defined": 0,
        }

        scenario = Scenario(active_status_data, auth_instance)

        assert scenario.scenario_status == ScenarioStatus.ACTIVE

    def test_triggered_status(self, auth_instance):
        triggered_status_data = {
            "id": 3,
            "name": "Luci notte spente",
            "scenario_status": 1,
            "status": 0,
            "user-defined": 0,
        }

        scenario = Scenario(triggered_status_data, auth_instance)

        assert scenario.scenario_status == ScenarioStatus.TRIGGERED

    def test_unknown_status(self, auth_instance):
        unknown_status_data = {
            "id": 5,
            "name": "Unknown Status Scenario",
            "scenario_status": 999,
            "status": 0,
            "user-defined": 0,
        }

        scenario = Scenario(unknown_status_data, auth_instance)

        assert scenario.raw_data == unknown_status_data
        assert scenario.name == "Unknown Status Scenario"
        assert scenario.scenario_status == ScenarioStatus.UNKNOWN

    def test_auth_type_validation(self):
        scenario_data = {
            "id": 1,
            "name": "Test Scenario",
            "scenario_status": 0,
            "status": 0,
            "user-defined": 0,
        }

        # Test with non-Auth object (string)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got str"
        ):
            Scenario(scenario_data, "not_an_auth_instance")

        # Test with non-Auth object (dict)
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got dict"
        ):
            Scenario(scenario_data, {"fake": "auth"})

    def test_edge_case_missing_optional_field(self, auth_instance):
        scenario_data = {
            "id": 1,
            "name": "Minimal Scenario",
        }

        scenario = Scenario(scenario_data, auth_instance)

        assert scenario.name == "Minimal Scenario"
        assert scenario.id == 1
        assert scenario.icon_id == 0
        assert scenario.scenario_status == ScenarioStatus.UNKNOWN
        assert scenario.status == 0
        assert scenario.user_defined == 0


class TestThermoZone:
    def test_initialization(self, thermo_zone_data_winter_auto, auth_instance):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        assert zone.raw_data == thermo_zone_data_winter_auto
        assert zone.auth == auth_instance

    def test_properties_winter_auto(self, thermo_zone_data_winter_auto, auth_instance):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        assert zone.act_id == 1
        assert zone.name == "Living Room"
        assert zone.floor_ind == 37
        assert zone.room_ind == 57
        assert zone.status == ThermoZoneStatus.OFF
        assert zone.temperature == 20.0
        assert zone.mode == ThermoZoneMode.AUTO
        assert zone.set_point == 34.8
        assert zone.season == ThermoZoneSeason.WINTER
        assert zone.leaf is True

    def test_properties_summer_manual(
        self, thermo_zone_data_summer_manual, auth_instance
    ):
        zone = ThermoZone(thermo_zone_data_summer_manual, auth_instance)
        assert zone.act_id == 52
        assert zone.name == "Bedroom"
        assert zone.status == ThermoZoneStatus.ON
        assert zone.temperature == 26.5
        assert zone.mode == ThermoZoneMode.MANUAL
        assert zone.set_point == 25.0
        assert zone.season == ThermoZoneSeason.SUMMER
        assert zone.antifreeze == 6.0

    def test_temperature_from_temp_dec(self, auth_instance):
        zone_data = {
            "act_id": 10,
            "name": "Indication Zone",
            "temp_dec": 185,
        }
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.temperature == 18.5

    def test_unknown_mode(self, auth_instance):
        zone_data = {
            "act_id": 1,
            "name": "Test Zone",
            "mode": 99,
        }
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.mode == ThermoZoneMode.UNKNOWN

    def test_unknown_status(self, auth_instance):
        zone_data = {
            "act_id": 1,
            "name": "Test Zone",
            "status": 99,
        }
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.status == ThermoZoneStatus.OFF

    def test_unknown_season(self, auth_instance):
        zone_data = {
            "act_id": 1,
            "name": "Test Zone",
            "season": "foo",
        }
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.season == ThermoZoneSeason.UNKNOWN

    def test_missing_act_id(self, auth_instance):
        zone_data = {"name": "Test Zone"}
        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            ThermoZone(zone_data, auth_instance)

    def test_missing_name(self, auth_instance):
        zone_data = {"act_id": 1}
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            ThermoZone(zone_data, auth_instance)

    def test_auth_type_validation(self):
        zone_data = {"act_id": 1, "name": "Test Zone"}
        with pytest.raises(
            ValueError, match="'auth' must be an instance of Auth, got dict"
        ):
            ThermoZone(zone_data, {"fake": "auth"})

    def test_optional_fields_missing(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Minimal Zone"}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.act_id == 1
        assert zone.name == "Minimal Zone"
        assert zone.temperature == 0.0
        assert zone.set_point == 0.0
        assert zone.mode == ThermoZoneMode.UNKNOWN
        assert zone.season == ThermoZoneSeason.UNKNOWN
        assert zone.antifreeze is None
        assert zone.leaf is True

    def test_antifreeze_none(self, thermo_zone_data_winter_auto, auth_instance):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        assert zone.antifreeze is None

    def test_status_on(self, thermo_zone_data_summer_manual, auth_instance):
        zone = ThermoZone(thermo_zone_data_summer_manual, auth_instance)
        assert zone.status == ThermoZoneStatus.ON

    def test_plant_off_season(self, auth_instance):
        zone_data = {
            "act_id": 1,
            "name": "Test Zone",
            "season": "plant_off",
        }
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.season == ThermoZoneSeason.PLANT_OFF

    def test_fan_speed(self, thermo_zone_data_with_fan_dehumidifier, auth_instance):
        zone = ThermoZone(thermo_zone_data_with_fan_dehumidifier, auth_instance)
        assert zone.fan_speed == ThermoZoneFanSpeed.MEDIUM

    def test_fan_speed_missing(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Minimal Zone"}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.fan_speed == ThermoZoneFanSpeed.UNKNOWN

    def test_fan_speed_unknown_value(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Test Zone", "fan_speed": 99}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.fan_speed == ThermoZoneFanSpeed.UNKNOWN

    def test_dehumidifier_enabled(
        self, thermo_zone_data_with_fan_dehumidifier, auth_instance
    ):
        zone = ThermoZone(thermo_zone_data_with_fan_dehumidifier, auth_instance)
        assert zone.dehumidifier_enabled is True

    def test_dehumidifier_enabled_missing(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Minimal Zone"}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.dehumidifier_enabled is False

    def test_dehumidifier_setpoint(
        self, thermo_zone_data_with_fan_dehumidifier, auth_instance
    ):
        zone = ThermoZone(thermo_zone_data_with_fan_dehumidifier, auth_instance)
        assert zone.dehumidifier_setpoint == 55.0

    def test_dehumidifier_setpoint_missing(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Minimal Zone"}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.dehumidifier_setpoint is None

    def test_t1_t2_t3(self, thermo_zone_data_with_fan_dehumidifier, auth_instance):
        zone = ThermoZone(thermo_zone_data_with_fan_dehumidifier, auth_instance)
        assert zone.t1 == 19.0
        assert zone.t2 == 20.0
        assert zone.t3 == 21.0

    def test_t1_t2_t3_missing(self, auth_instance):
        zone_data = {"act_id": 1, "name": "Minimal Zone"}
        zone = ThermoZone(zone_data, auth_instance)
        assert zone.t1 is None
        assert zone.t2 is None
        assert zone.t3 is None

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_config(mode=ThermoZoneMode.MANUAL, set_point=22.5)
        mock_send_command.assert_called_once()
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["cmd_name"] == "thermo_zone_config_req"
        assert call_payload["act_id"] == 1
        assert call_payload["mode"] == 1
        assert call_payload["set_point"] == 225
        assert call_payload["extended_infos"] == 0
        assert zone.raw_data["mode"] == 1
        assert zone.raw_data["set_point"] == 225

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_with_season_and_fan_speed(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_config(
            mode=ThermoZoneMode.AUTO,
            set_point=21.0,
            season=ThermoZoneSeason.SUMMER,
            fan_speed=ThermoZoneFanSpeed.FAST,
        )
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["extended_infos"] == 1
        assert call_payload["season"] == "summer"
        assert call_payload["fan_speed"] == 3
        assert zone.raw_data["season"] == "summer"
        assert zone.raw_data["fan_speed"] == 3

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_without_extended(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_config(mode=ThermoZoneMode.OFF, set_point=20.0)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["extended_infos"] == 0
        assert "season" not in call_payload
        assert "fan_speed" not in call_payload

    async def test_async_set_config_unknown_mode_raises(
        self,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        with pytest.raises(ValueError, match="Cannot set mode to UNKNOWN"):
            await zone.async_set_config(mode=ThermoZoneMode.UNKNOWN, set_point=20.0)

    async def test_async_set_config_unknown_season_raises(
        self, thermo_zone_data_winter_auto, auth_instance
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        with pytest.raises(ValueError, match="Cannot set season to UNKNOWN"):
            await zone.async_set_config(
                mode=ThermoZoneMode.AUTO,
                set_point=20.0,
                season=ThermoZoneSeason.UNKNOWN,
            )

    async def test_async_set_config_unknown_fan_speed_raises(
        self, thermo_zone_data_winter_auto, auth_instance
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        with pytest.raises(ValueError, match="Cannot set fan_speed to UNKNOWN"):
            await zone.async_set_config(
                mode=ThermoZoneMode.AUTO,
                set_point=20.0,
                fan_speed=ThermoZoneFanSpeed.UNKNOWN,
            )

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_temperature(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_temperature(22.0)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["set_point"] == 220
        assert call_payload["mode"] == 2  # preserves current AUTO mode

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_mode(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_mode(ThermoZoneMode.MANUAL)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["mode"] == 1
        assert call_payload["set_point"] == 348  # preserves current setpoint

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_fan_speed_method(
        self,
        mock_send_command,
        thermo_zone_data_winter_auto,
        auth_instance,
    ):
        zone = ThermoZone(thermo_zone_data_winter_auto, auth_instance)
        await zone.async_set_fan_speed(ThermoZoneFanSpeed.SLOW)
        call_payload = mock_send_command.call_args[0][0]
        assert call_payload["fan_speed"] == 1
        assert call_payload["extended_infos"] == 1
        assert call_payload["mode"] == 2  # preserves current AUTO mode
        assert call_payload["set_point"] == 348  # preserves current setpoint


class TestThermoZoneFanSpeed:
    def test_enum_values(self):
        assert ThermoZoneFanSpeed.OFF.value == 0
        assert ThermoZoneFanSpeed.SLOW.value == 1
        assert ThermoZoneFanSpeed.MEDIUM.value == 2
        assert ThermoZoneFanSpeed.FAST.value == 3
        assert ThermoZoneFanSpeed.AUTO.value == 4
        assert ThermoZoneFanSpeed.UNKNOWN.value == -1


class TestAnalogSensor:
    def test_initialization(self, analog_sensor_data_temperature):
        sensor = AnalogSensor(analog_sensor_data_temperature)
        assert sensor.raw_data == analog_sensor_data_temperature

    def test_properties(self, analog_sensor_data_temperature):
        sensor = AnalogSensor(analog_sensor_data_temperature)
        assert sensor.act_id == 100
        assert sensor.name == "Outdoor Temperature"
        assert sensor.value == 21.5
        assert sensor.unit == "\u00b0C"

    def test_humidity_properties(self, analog_sensor_data_humidity):
        sensor = AnalogSensor(analog_sensor_data_humidity)
        assert sensor.act_id == 101
        assert sensor.name == "Indoor Humidity"
        assert sensor.value == 55.0
        assert sensor.unit == "%"

    def test_missing_name(self):
        sensor_data = {"act_id": 100, "value": 215}
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            AnalogSensor(sensor_data)

    def test_missing_act_id(self):
        sensor_data = {"name": "Test Sensor", "value": 215}
        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            AnalogSensor(sensor_data)

    def test_optional_fields_missing(self):
        sensor_data = {"name": "Minimal Sensor", "act_id": 200}
        sensor = AnalogSensor(sensor_data)
        assert sensor.name == "Minimal Sensor"
        assert sensor.act_id == 200
        assert sensor.value == 0.0
        assert sensor.unit == ""


class TestDigitalInput:
    def test_init_with_status(self, auth_instance, digital_input_data_with_status):
        di = DigitalInput(digital_input_data_with_status, auth_instance)
        assert di.act_id == 1
        assert di.name == "digitalin_BuTbB"
        assert di.status == DigitalInputStatus.IDLE
        assert di.type == DigitalInputType.STATUS
        assert di.addr == 201
        assert di.utc_time == 1708366780

    def test_init_without_status(
        self, auth_instance, digital_input_data_without_status
    ):
        di = DigitalInput(digital_input_data_without_status, auth_instance)
        assert di.act_id == 0
        assert di.name == "digitalin_PvGCT"
        assert di.status == DigitalInputStatus.UNKNOWN
        assert di.addr == 200
        assert di.utc_time == 0

    def test_status_active(self, auth_instance, digital_input_data_with_status):
        digital_input_data_with_status["status"] = 0
        di = DigitalInput(digital_input_data_with_status, auth_instance)
        assert di.status == DigitalInputStatus.ACTIVE

    def test_unknown_status_value(self, auth_instance, digital_input_data_with_status):
        digital_input_data_with_status["status"] = 99
        di = DigitalInput(digital_input_data_with_status, auth_instance)
        assert di.status == DigitalInputStatus.UNKNOWN

    def test_unknown_type_value(self, auth_instance, digital_input_data_with_status):
        digital_input_data_with_status["type"] = 99
        di = DigitalInput(digital_input_data_with_status, auth_instance)
        assert di.type == DigitalInputType.UNKNOWN

    def test_missing_name_raises(self, auth_instance):
        data = {"act_id": 0, "type": 1}
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            DigitalInput(data, auth_instance)

    def test_missing_act_id_raises(self, auth_instance):
        data = {"name": "test", "type": 1}
        with pytest.raises(ValueError, match="Data is missing required keys: act_id"):
            DigitalInput(data, auth_instance)

    def test_invalid_auth_raises(self, digital_input_data_with_status):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            DigitalInput(digital_input_data_with_status, "not_an_auth")

    def test_optional_fields_defaults(self, auth_instance):
        data = {"act_id": 5, "name": "Minimal Input"}
        di = DigitalInput(data, auth_instance)
        assert di.addr == 0
        assert di.utc_time == 0
        assert di.status == DigitalInputStatus.UNKNOWN
        assert di.type == DigitalInputType.UNKNOWN
