# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

from unittest.mock import patch

import pytest

from aiocamedomotic import Auth, CameDomoticAPI
from aiocamedomotic.models import EnergyMeter, EnergyMeterType
from tests.aiocamedomotic.mocked_responses import METERS_LIST_RESP


class TestEnergyMeter:
    def test_properties(self, energy_meter_data):
        meter = EnergyMeter(energy_meter_data)
        assert meter.id == 4
        assert meter.name == "Consumed Energy"
        assert meter.meter_type == EnergyMeterType.POWER
        assert meter.instant_power == 595
        assert meter.unit == "W"
        assert meter.energy_unit == "Wh"
        assert meter.produced == 0
        assert meter.last_24h_avg == 5813270
        assert meter.last_month_avg == 5813270

    def test_defaults_for_optional_fields(self):
        meter = EnergyMeter({"name": "Minimal Meter", "id": 1})
        assert meter.instant_power == 0
        assert meter.unit == "W"
        assert meter.energy_unit == "Wh"
        assert meter.produced == 0
        assert meter.last_24h_avg == 0
        assert meter.last_month_avg == 0

    def test_meter_type_unknown_value(self, energy_meter_data):
        energy_meter_data["meter_type"] = 99
        meter = EnergyMeter(energy_meter_data)
        assert meter.meter_type == EnergyMeterType.UNKNOWN

    def test_meter_type_missing(self):
        meter = EnergyMeter({"name": "Meter", "id": 1})
        assert meter.meter_type == EnergyMeterType.UNKNOWN

    def test_missing_name(self):
        with pytest.raises(ValueError, match="Data is missing required keys: name"):
            EnergyMeter({"id": 4})

    def test_missing_id(self):
        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            EnergyMeter({"name": "Meter"})

    def test_invalid_id_type(self):
        with pytest.raises(ValueError):
            EnergyMeter({"name": "Meter", "id": "not-an-int"})


class TestAPIEnergyMeters:
    @patch.object(Auth, "async_send_command")
    async def test_async_get_energy_meters(self, mock_send_command, auth_instance):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = METERS_LIST_RESP

        meters = await api.async_get_energy_meters()

        mock_send_command.assert_called_once_with(
            {"cmd_name": "meters_list_req"},
            response_command="meters_list_resp",
        )
        assert len(meters) == 2
        assert all(isinstance(m, EnergyMeter) for m in meters)
        assert meters[0].id == 1
        assert meters[0].name == "Meter 1"
        assert meters[0].instant_power == 144
        assert meters[1].id == 2

    @patch.object(Auth, "async_send_command")
    async def test_async_get_energy_meters_empty_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": [],
            "cmd_name": "meters_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        meters = await api.async_get_energy_meters()
        assert meters == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_energy_meters_missing_array_key(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "meters_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        meters = await api.async_get_energy_meters()
        assert meters == []

    @patch.object(Auth, "async_send_command")
    async def test_async_get_energy_meters_null_array(
        self, mock_send_command, auth_instance
    ):
        api = CameDomoticAPI(auth_instance)
        mock_send_command.return_value = {
            "array": None,
            "cmd_name": "meters_list_resp",
            "cseq": 1,
            "sl_data_ack_reason": 0,
        }

        meters = await api.async_get_energy_meters()
        assert meters == []
