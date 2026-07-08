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

import copy
from unittest.mock import AsyncMock, patch

import pytest

from aiocamedomotic import Auth, CameDomoticAPI
from aiocamedomotic.models import (
    LoadsCtrlMeter,
    LoadsCtrlRelay,
    LoadsCtrlRelayStatus,
)
from tests.aiocamedomotic.mocked_responses import (
    LOADSCTRL_METER_LIST_RESP,
    LOADSCTRL_RELAY_LIST_RESP,
    LOADSCTRL_SET_ACK,
)


class TestLoadsCtrlRelay:
    def test_properties(self, loadsctrl_relay_data, auth_instance):
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        assert relay.id == 65600
        assert relay.name == "Washing machine"
        assert relay.act_id == 129
        assert relay.priority == 129
        assert relay.enabled is False
        assert relay.detached is False
        assert relay.status == LoadsCtrlRelayStatus.ON
        assert relay.loadtype == 1

    def test_enabled_bool_coercion(self, loadsctrl_relay_data, auth_instance):
        loadsctrl_relay_data["enabled"] = 1
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        assert relay.enabled is True

    def test_detached_bool_coercion(self, loadsctrl_relay_data, auth_instance):
        loadsctrl_relay_data["detached"] = 1
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        assert relay.detached is True

    def test_status_off(self, loadsctrl_relay_data, auth_instance):
        loadsctrl_relay_data["status"] = 0
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        assert relay.status == LoadsCtrlRelayStatus.OFF

    def test_status_unknown_value(self, loadsctrl_relay_data, auth_instance):
        loadsctrl_relay_data["status"] = 99
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        assert relay.status == LoadsCtrlRelayStatus.UNKNOWN

    def test_status_missing(self, auth_instance):
        relay = LoadsCtrlRelay({"name": "Load", "id": 1}, auth_instance)
        assert relay.status == LoadsCtrlRelayStatus.UNKNOWN

    def test_defaults_for_optional_fields(self, auth_instance):
        relay = LoadsCtrlRelay({"name": "Load", "id": 1}, auth_instance)
        assert relay.act_id == 0
        assert relay.priority == 0
        assert relay.enabled is False
        assert relay.detached is False
        assert relay.loadtype == 0

    def test_missing_name(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            LoadsCtrlRelay({"id": 65600}, auth_instance)

    def test_missing_id(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            LoadsCtrlRelay({"name": "Load"}, auth_instance)

    def test_invalid_id_type(self, auth_instance):
        with pytest.raises(ValueError):
            LoadsCtrlRelay({"name": "Load", "id": "not-an-int"}, auth_instance)

    def test_auth_type_validation(self, loadsctrl_relay_data):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            LoadsCtrlRelay(loadsctrl_relay_data, "not-an-auth")

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_enabled_true(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_relay_data,
        auth_instance,
    ):
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)

        await relay.async_set_enabled(True)

        # Full field set, no response_command (the ack has no cmd_name)
        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_relay_set_req",
                "id": 65600,
                "enabled": 1,
                "priority": 129,
            }
        )
        assert relay.raw_data["enabled"] == 1
        assert relay.enabled is True

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_enabled_false(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_relay_data,
        auth_instance,
    ):
        loadsctrl_relay_data["enabled"] = 1
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)

        await relay.async_set_enabled(False)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_relay_set_req",
                "id": 65600,
                "enabled": 0,
                "priority": 129,
            }
        )
        assert relay.raw_data["enabled"] == 0
        assert relay.enabled is False

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_priority(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_relay_data,
        auth_instance,
    ):
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)

        await relay.async_set_priority(130)

        # The current enabled flag is re-sent alongside the new priority
        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_relay_set_req",
                "id": 65600,
                "enabled": 0,
                "priority": 130,
            }
        )
        assert relay.raw_data["priority"] == 130
        assert relay.priority == 130

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_priority_negative(
        self, mock_send_command, loadsctrl_relay_data, auth_instance
    ):
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        with pytest.raises(ValueError, match="priority must be >= 0"):
            await relay.async_set_priority(-1)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_priority_non_int(
        self, mock_send_command, loadsctrl_relay_data, auth_instance
    ):
        relay = LoadsCtrlRelay(loadsctrl_relay_data, auth_instance)
        with pytest.raises(ValueError, match="priority must be an int"):
            await relay.async_set_priority("129")
        mock_send_command.assert_not_called()


class TestLoadsCtrlMeter:
    def test_properties(self, loadsctrl_meter_data, auth_instance):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        assert meter.id == 196612
        assert meter.name == "Consumed Energy"
        assert meter.meter_id == 4
        assert meter.power == 595
        assert meter.max_power == 5000
        assert meter.hysteresis == 400
        assert meter.profile_data == ["4" * 24] * 7

    def test_profile_data_returns_copy(self, loadsctrl_meter_data, auth_instance):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        profile = meter.profile_data
        profile[0] = "tampered"
        assert meter.raw_data["profile_data"][0] == "4" * 24

    def test_defaults_for_optional_fields(self, auth_instance):
        meter = LoadsCtrlMeter({"name": "Controller", "id": 1}, auth_instance)
        assert meter.meter_id == 0
        assert meter.power == 0
        assert meter.max_power == 0
        assert meter.hysteresis == 0
        assert meter.profile_data == []

    def test_missing_name(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            LoadsCtrlMeter({"id": 196612}, auth_instance)

    def test_missing_id(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            LoadsCtrlMeter({"name": "Controller"}, auth_instance)

    def test_invalid_id_type(self, auth_instance):
        with pytest.raises(ValueError):
            LoadsCtrlMeter({"name": "Controller", "id": "abc"}, auth_instance)

    def test_auth_type_validation(self, loadsctrl_meter_data):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            LoadsCtrlMeter(loadsctrl_meter_data, None)

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_get_relays(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        relays = await meter.async_get_relays()

        mock_send_command.assert_called_once_with(
            {"cmd_name": "loadsctrl_relay_list_req", "id": 196612},
            response_command="loadsctrl_relay_list_resp",
        )
        assert len(relays) == 4
        assert all(isinstance(r, LoadsCtrlRelay) for r in relays)
        assert relays[0].id == 65601
        assert relays[0].auth is auth_instance

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_get_relays_empty_array(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "loadsctrl_relay_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await meter.async_get_relays() == []

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_get_relays_missing_array_key(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "loadsctrl_relay_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await meter.async_get_relays() == []

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_config_full(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        new_profile = ["5" * 24] * 7

        await meter.async_set_config(
            max_power=4800, hysteresis=1000, profile_data=new_profile
        )

        # Full triple always sent, no response_command (the ack has no cmd_name)
        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_meter_set_req",
                "id": 196612,
                "max_power": 4800,
                "hysteresis": 1000,
                "profile_data": new_profile,
            }
        )
        assert meter.max_power == 4800
        assert meter.hysteresis == 1000
        assert meter.profile_data == new_profile

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_config_partial_max_power(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)

        await meter.async_set_config(max_power=6000)

        # Untouched values are sourced from raw_data
        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_meter_set_req",
                "id": 196612,
                "max_power": 6000,
                "hysteresis": 400,
                "profile_data": ["4" * 24] * 7,
            }
        )
        assert meter.max_power == 6000
        assert meter.hysteresis == 400

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_config_partial_hysteresis(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)

        await meter.async_set_config(hysteresis=250)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_meter_set_req",
                "id": 196612,
                "max_power": 5000,
                "hysteresis": 250,
                "profile_data": ["4" * 24] * 7,
            }
        )
        assert meter.hysteresis == 250

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_max_power_not_positive(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="max_power must be a positive int"):
            await meter.async_set_config(max_power=0)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_hysteresis_not_positive(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="hysteresis must be a positive int"):
            await meter.async_set_config(hysteresis=-1)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_profile_wrong_count(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="exactly 7 strings"):
            await meter.async_set_config(profile_data=["5" * 24] * 6)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_profile_wrong_length(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="exactly 24"):
            await meter.async_set_config(profile_data=["5" * 23] + ["5" * 24] * 6)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_profile_char_out_of_range(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="digits in the\\s+range 1-5"):
            await meter.async_set_config(profile_data=["6" * 24] + ["5" * 24] * 6)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_profile_non_string_entry(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="must be a string"):
            await meter.async_set_config(profile_data=[44444] + ["5" * 24] * 6)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_detach_order_writes_only_changed(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        by_id = {r.id: r for r in relays}
        # Current priorities: 65600 -> 129, 65601 -> 130, 65602 -> 131,
        # 65537 -> 132. Swap the two first loads to shed, keep the rest.
        desired = [by_id[65601], by_id[65600], by_id[65602], by_id[65537]]
        mock_send_command.side_effect = [
            copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP),
            dict(LOADSCTRL_SET_ACK),
            dict(LOADSCTRL_SET_ACK),
        ]

        await meter.async_set_detach_order(desired)

        # First call fetches the current relays, then one set per changed relay
        assert mock_send_command.call_count == 3
        assert mock_send_command.call_args_list[0].args[0] == {
            "cmd_name": "loadsctrl_relay_list_req",
            "id": 196612,
        }
        assert mock_send_command.call_args_list[1].args[0] == {
            "cmd_name": "loadsctrl_relay_set_req",
            "id": 65601,
            "enabled": 1,
            "priority": 129,
        }
        assert mock_send_command.call_args_list[2].args[0] == {
            "cmd_name": "loadsctrl_relay_set_req",
            "id": 65600,
            "enabled": 0,
            "priority": 130,
        }
        # The caller's objects are optimistically updated
        assert by_id[65601].priority == 129
        assert by_id[65600].priority == 130
        assert by_id[65602].priority == 131
        assert by_id[65537].priority == 132

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_detach_order_no_changes(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        by_id = {r.id: r for r in relays}
        # Current detach order: ascending priority
        desired = [by_id[65600], by_id[65601], by_id[65602], by_id[65537]]
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        await meter.async_set_detach_order(desired)

        # Only the relay list fetch, no set commands
        assert mock_send_command.call_count == 1

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_detach_order_missing_relay(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        with pytest.raises(ValueError, match="permutation"):
            await meter.async_set_detach_order(relays[:3])

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_detach_order_duplicate_relay(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        with pytest.raises(ValueError, match="permutation"):
            await meter.async_set_detach_order(relays[:3] + [relays[0]])

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_detach_order_foreign_relay(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        foreign = LoadsCtrlRelay(
            {"name": "Other load", "id": 99999, "priority": 1, "enabled": 0},
            auth_instance,
        )
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        with pytest.raises(ValueError, match="permutation"):
            await meter.async_set_detach_order(relays[:3] + [foreign])

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_detach_order_duplicate_priorities(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        # Plant with duplicate priorities (observed on some firmwares:
        # every relay at the same priority value)
        duplicate_resp = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)
        for relay_data in duplicate_resp["array"]:
            relay_data["priority"] = 82
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in duplicate_resp["array"]
        ]
        mock_send_command.return_value = duplicate_resp

        with pytest.raises(ValueError, match="duplicate priority"):
            await meter.async_set_detach_order(relays)


class TestAPILoadsCtrl:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_meters(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_METER_LIST_RESP)

        meters = await api.async_get_loadsctrl_meters()

        mock_send_command.assert_called_once_with(
            {"cmd_name": "loadsctrl_meter_list_req"},
            response_command="loadsctrl_meter_list_resp",
        )
        assert len(meters) == 1
        assert isinstance(meters[0], LoadsCtrlMeter)
        assert meters[0].id == 123456
        assert meters[0].meter_id == 1
        assert meters[0].max_power == 5000
        assert meters[0].hysteresis == 400

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_meters_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "loadsctrl_meter_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await api.async_get_loadsctrl_meters() == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_meters_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "loadsctrl_meter_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await api.async_get_loadsctrl_meters() == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_meters_null_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "loadsctrl_meter_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await api.async_get_loadsctrl_meters() == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_relays(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)

        relays = await api.async_get_loadsctrl_relays(123456)

        mock_send_command.assert_called_once_with(
            {"cmd_name": "loadsctrl_relay_list_req", "id": 123456},
            response_command="loadsctrl_relay_list_resp",
        )
        assert len(relays) == 4
        assert all(isinstance(r, LoadsCtrlRelay) for r in relays)
        assert relays[1].id == 65600
        assert relays[1].name == "Washing machine"

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_relays_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "loadsctrl_relay_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        assert await api.async_get_loadsctrl_relays(123456) == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_loadsctrl_relays_invalid_meter_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)

        with pytest.raises(ValueError, match="meter_id must be an int"):
            await api.async_get_loadsctrl_relays("123456")
        mock_send_command.assert_not_called()
