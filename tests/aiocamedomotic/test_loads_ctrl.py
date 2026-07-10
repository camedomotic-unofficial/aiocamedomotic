# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import copy
from unittest.mock import AsyncMock, patch

import pytest

from aiocamedomotic import Auth, CameDomoticAPI
from aiocamedomotic.errors import CameDomoticServerError
from aiocamedomotic.models import (
    LoadsCtrlMeter,
    LoadsCtrlProfile,
    LoadsCtrlRelay,
    LoadsCtrlRelayStatus,
    ProfileDay,
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
        new_profile = LoadsCtrlProfile.constant(5)

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
                "profile_data": ["5" * 24] * 7,
            }
        )
        assert meter.max_power == 4800
        assert meter.hysteresis == 1000
        assert meter.profile_data == ["5" * 24] * 7

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
    async def test_async_set_config_hysteresis_negative(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="hysteresis must be a non-negative int"):
            await meter.async_set_config(hysteresis=-1)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_config_hysteresis_zero_allowed(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)

        await meter.async_set_config(hysteresis=0)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_meter_set_req",
                "id": 196612,
                "max_power": 5000,
                "hysteresis": 0,
                "profile_data": ["4" * 24] * 7,
            }
        )
        assert meter.hysteresis == 0

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_config_profile_raw_list_rejected(
        self, mock_send_command, loadsctrl_meter_data, auth_instance
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="must be a LoadsCtrlProfile"):
            await meter.async_set_config(profile_data=["5" * 24] * 7)
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_config_edited_profile(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        new_profile = meter.profile.with_level(
            2, days=ProfileDay.SUNDAY, start=8, end=18
        )

        await meter.async_set_config(profile_data=new_profile)

        expected_wire = ["4" * 24] * 6 + ["4" * 8 + "2" * 10 + "4" * 6]
        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "loadsctrl_meter_set_req",
                "id": 196612,
                "max_power": 5000,
                "hysteresis": 400,
                "profile_data": expected_wire,
            }
        )
        assert meter.profile_data == expected_wire

    def test_profile_typed_view(self, loadsctrl_meter_data, auth_instance):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        assert isinstance(meter.profile, LoadsCtrlProfile)
        assert meter.profile.to_wire() == ["4" * 24] * 7

    def test_profile_fresh_parse_per_access(self, loadsctrl_meter_data, auth_instance):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        meter.raw_data["profile_data"] = ["5" * 24] * 7
        assert meter.profile.to_wire() == ["5" * 24] * 7

    def test_profile_missing_raw_data(self, auth_instance):
        meter = LoadsCtrlMeter({"name": "Controller", "id": 1}, auth_instance)
        with pytest.raises(ValueError, match="exactly 7 strings"):
            _ = meter.profile

    def test_profile_malformed_raw_data(self, loadsctrl_meter_data, auth_instance):
        loadsctrl_meter_data["profile_data"] = ["9" * 24] * 7
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        with pytest.raises(ValueError, match="only digits"):
            _ = meter.profile

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
    async def test_async_set_detach_order_uses_fresh_enabled_state(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        # The caller's cached objects: relay 65601 believes it is enabled,
        # from an earlier fetch.
        stale_relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in LOADSCTRL_RELAY_LIST_RESP["array"]
        ]
        by_id = {r.id: r for r in stale_relays}
        assert by_id[65601].enabled is True

        # Server-side truth has since changed: another client disabled it.
        fresh_resp = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)
        for relay_data in fresh_resp["array"]:
            if relay_data["id"] == 65601:
                relay_data["enabled"] = 0

        desired = [by_id[65601], by_id[65600], by_id[65602], by_id[65537]]
        mock_send_command.side_effect = [
            fresh_resp,
            dict(LOADSCTRL_SET_ACK),
            dict(LOADSCTRL_SET_ACK),
        ]

        await meter.async_set_detach_order(desired)

        # The write for 65601 must carry the FRESH enabled value (0), not
        # the caller's stale cached value (1) - otherwise this call would
        # silently revert the other client's change.
        assert mock_send_command.call_args_list[1].args[0] == {
            "cmd_name": "loadsctrl_relay_set_req",
            "id": 65601,
            "enabled": 0,
            "priority": 129,
        }
        # The caller's object is synced to the fresh state too
        assert by_id[65601].enabled is False
        assert by_id[65601].priority == 129

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
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_detach_order_repairs_duplicate_priorities(
        self,
        mock_get_client_id,
        mock_send_command,
        loadsctrl_meter_data,
        auth_instance,
        caplog,
    ):
        meter = LoadsCtrlMeter(loadsctrl_meter_data, auth_instance)
        # Plant where every relay shares the same priority value: a full
        # detach order cannot be expressed with the existing value set, so
        # the method must repair it into a strictly increasing sequence.
        duplicate_resp = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)
        for relay_data in duplicate_resp["array"]:
            relay_data["priority"] = 82
        relays = [
            LoadsCtrlRelay(copy.deepcopy(data), auth_instance)
            for data in duplicate_resp["array"]
        ]
        mock_send_command.side_effect = [duplicate_resp] + [dict(LOADSCTRL_SET_ACK)] * 3

        await meter.async_set_detach_order(relays)

        # Repaired sequence 82, 83, 84, 85: the first relay keeps 82
        # (no write), the others are bumped in request order.
        assert mock_send_command.call_count == 4
        written = [call.args[0] for call in mock_send_command.call_args_list[1:]]
        assert [(w["id"], w["priority"]) for w in written] == [
            (relays[1].id, 83),
            (relays[2].id, 84),
            (relays[3].id, 85),
        ]
        assert "duplicate relay" in caplog.text

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_async_set_detach_order_replay_after_partial_failure(
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
        # Swap the two first loads to shed: 65601 gets 129, 65600 gets 130.
        desired = [by_id[65601], by_id[65600], by_id[65602], by_id[65537]]

        # First call: the write for 65601 (-> 129) succeeds, then the
        # write for 65600 (-> 130) fails, leaving 65600 and 65601 both
        # at priority 129 on the plant (value 130 temporarily lost).
        mock_send_command.side_effect = [
            copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP),
            dict(LOADSCTRL_SET_ACK),
            CameDomoticServerError("boom"),
        ]
        with pytest.raises(CameDomoticServerError):
            await meter.async_set_detach_order(desired)

        after_failure_resp = copy.deepcopy(LOADSCTRL_RELAY_LIST_RESP)
        for relay_data in after_failure_resp["array"]:
            if relay_data["id"] == 65601:
                relay_data["priority"] = 129

        # Replaying the same request must repair the duplicate (129, 129,
        # 131, 132 -> 129, 130, 131, 132) and finish the reorder with a
        # single write, restoring the originally intended end state.
        mock_send_command.side_effect = [
            after_failure_resp,
            dict(LOADSCTRL_SET_ACK),
        ]
        await meter.async_set_detach_order(desired)

        assert mock_send_command.call_args_list[-1].args[0] == {
            "cmd_name": "loadsctrl_relay_set_req",
            "id": 65600,
            "enabled": 0,
            "priority": 130,
        }
        assert by_id[65601].priority == 129
        assert by_id[65600].priority == 130


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
    async def test_async_get_loadsctrl_relays_invalid_controller_id(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)

        with pytest.raises(ValueError, match="controller_id must be an int"):
            await api.async_get_loadsctrl_relays("123456")
        mock_send_command.assert_not_called()
