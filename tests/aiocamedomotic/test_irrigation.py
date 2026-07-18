# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access

from unittest.mock import AsyncMock, patch

import pytest

from aiocamedomotic import Auth
from aiocamedomotic.models.irrigation import Irrigation

# Irrigation is absent from the reference plant, so all data below is inline
# and modelled on the field-tested third-party integration's data shape.
IRRIGATION_DATA = {
    "id": 7,
    "name": "Front lawn",
    "enabled": 1,
    "status": 0,
    "forced": 0,
    "days": 42,
    "perc": 80,
    "start": {"hour": 6, "min": 0},
    "end": {"hour": 6, "min": 30},
    "sprinklers": [1, 2, 3],
}


class TestIrrigation:
    def test_init_valid(self, auth_instance):
        irrigation = Irrigation(IRRIGATION_DATA, auth_instance)
        assert irrigation.raw_data == IRRIGATION_DATA
        assert irrigation.auth == auth_instance

    def test_missing_id_raises(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            Irrigation({"name": "No id"}, auth_instance)

    def test_id_wrong_type_raises(self, auth_instance):
        with pytest.raises(ValueError):
            Irrigation({"id": "not-an-int"}, auth_instance)

    def test_none_data_raises(self, auth_instance):
        with pytest.raises((ValueError, TypeError)):
            Irrigation(None, auth_instance)  # type: ignore[arg-type]

    def test_invalid_auth_raises(self):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            Irrigation(IRRIGATION_DATA, "not_auth")  # type: ignore[arg-type]

    def test_properties(self, auth_instance):
        irrigation = Irrigation(IRRIGATION_DATA, auth_instance)
        assert irrigation.id == 7
        assert irrigation.name == "Front lawn"
        assert irrigation.enabled is True
        assert irrigation.status == 0
        assert irrigation.forced is False
        assert irrigation.days == 42
        assert irrigation.perc == 80
        assert irrigation.start == {"hour": 6, "min": 0}
        assert irrigation.end == {"hour": 6, "min": 30}
        assert irrigation.sprinklers == [1, 2, 3]

    def test_name_missing_returns_none(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.name is None

    def test_enabled_defaults_false(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.enabled is False

    def test_status_defaults_zero(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.status == 0

    def test_forced_defaults_false(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.forced is False

    def test_days_defaults_zero(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.days == 0

    def test_perc_defaults_zero(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.perc == 0

    def test_optional_fields_default_none(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.start is None
        assert irrigation.end is None
        assert irrigation.sprinklers is None

    def test_is_running_idle(self, auth_instance):
        irrigation = Irrigation({"id": 1, "status": 0, "forced": 0}, auth_instance)
        assert irrigation.is_running is False

    def test_is_running_by_status(self, auth_instance):
        irrigation = Irrigation({"id": 1, "status": 1, "forced": 0}, auth_instance)
        assert irrigation.is_running is True

    def test_is_running_by_forced(self, auth_instance):
        irrigation = Irrigation({"id": 1, "status": 0, "forced": 1}, auth_instance)
        assert irrigation.is_running is True
        assert irrigation.forced is True

    def test_is_running_missing_fields(self, auth_instance):
        irrigation = Irrigation({"id": 1}, auth_instance)
        assert irrigation.is_running is False


class TestIrrigationControl:
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_force(self, mock_send_command, auth_instance):
        irrigation = Irrigation(IRRIGATION_DATA, auth_instance)

        await irrigation.async_force()

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "irrigation_force_req",
                "id": 7,
            }
        )

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_enabled_true(self, mock_send_command, auth_instance):
        irrigation = Irrigation({"id": 3, "enabled": 0}, auth_instance)
        assert irrigation.enabled is False

        await irrigation.async_set_enabled(True)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "irrigation_set_req",
                "id": 3,
                "enabled": 1,
            }
        )
        assert irrigation.enabled is True

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_enabled_false(self, mock_send_command, auth_instance):
        irrigation = Irrigation({"id": 3, "enabled": 1}, auth_instance)
        assert irrigation.enabled is True

        await irrigation.async_set_enabled(False)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "irrigation_set_req",
                "id": 3,
                "enabled": 0,
            }
        )
        assert irrigation.enabled is False
