# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access

from unittest.mock import AsyncMock, patch

import pytest

from aiocamedomotic import Auth
from aiocamedomotic.models.sound_zone import SoundZone, SoundZoneAction

# Sound zones are absent from the reference plant, so all data below is inline
# and modelled on the field-tested third-party integration's data shape.
# Array-based sources format.
SOUND_ZONE_DATA = {
    "id": 3,
    "name": "Living room",
    "standby": 0,
    "mute": 0,
    "volume": 25,
    "min_volume": 0,
    "max_volume": 50,
    "source_name": "Radio",
    "sources": [
        {"source": "Radio", "id": 0},
        {"source_name": "Aux", "id": 1},
    ],
}

# Flat source_N fields format.
SOUND_ZONE_FLAT_DATA = {
    "id": 4,
    "name": "Kitchen",
    "standby": 1,
    "mute": 1,
    "volume": 10,
    "min_volume": 5,
    "max_volume": 35,
    "source": "Radio",
    "source_1": "Radio",
    "source_3": "Aux",
    "id_source_3": 7,
}


class TestSoundZone:
    def test_init_valid(self, auth_instance):
        zone = SoundZone(SOUND_ZONE_DATA, auth_instance)
        assert zone.raw_data == SOUND_ZONE_DATA
        assert zone.auth == auth_instance

    def test_missing_id_raises(self, auth_instance):
        with pytest.raises(ValueError, match="Data is missing required keys: id"):
            SoundZone({"name": "No id"}, auth_instance)

    def test_id_wrong_type_raises(self, auth_instance):
        with pytest.raises(ValueError):
            SoundZone({"id": "not-an-int"}, auth_instance)

    def test_none_data_raises(self, auth_instance):
        with pytest.raises((ValueError, TypeError)):
            SoundZone(None, auth_instance)  # type: ignore[arg-type]

    def test_invalid_auth_raises(self):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            SoundZone(SOUND_ZONE_DATA, "not_auth")  # type: ignore[arg-type]

    def test_properties(self, auth_instance):
        zone = SoundZone(SOUND_ZONE_DATA, auth_instance)
        assert zone.id == 3
        assert zone.name == "Living room"
        assert zone.is_on is True
        assert zone.is_muted is False
        assert zone.volume == 25
        assert zone.min_volume == 0
        assert zone.max_volume == 50
        assert zone.volume_level == 0.5
        assert zone.source == "Radio"

    def test_standby_zone(self, auth_instance):
        zone = SoundZone(SOUND_ZONE_FLAT_DATA, auth_instance)
        assert zone.is_on is False
        assert zone.is_muted is True

    def test_name_missing_returns_none(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.name is None

    def test_is_on_defaults_true_when_standby_missing(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.is_on is True

    def test_is_muted_defaults_false_when_mute_missing(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.is_muted is False

    def test_volume_fields_default_none(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.volume is None
        assert zone.min_volume is None
        assert zone.max_volume is None

    def test_volume_level_none_when_volume_missing(self, auth_instance):
        zone = SoundZone({"id": 1, "min_volume": 0, "max_volume": 50}, auth_instance)
        assert zone.volume_level is None

    def test_volume_level_none_when_range_missing(self, auth_instance):
        zone = SoundZone({"id": 1, "volume": 25}, auth_instance)
        assert zone.volume_level is None

    def test_volume_level_zero_when_range_empty(self, auth_instance):
        zone = SoundZone(
            {"id": 1, "volume": 20, "min_volume": 20, "max_volume": 20},
            auth_instance,
        )
        assert zone.volume_level == 0.0

    def test_volume_level_clamped_above_max(self, auth_instance):
        zone = SoundZone(
            {"id": 1, "volume": 99, "min_volume": 0, "max_volume": 50},
            auth_instance,
        )
        assert zone.volume_level == 1.0

    def test_volume_level_clamped_below_min(self, auth_instance):
        zone = SoundZone(
            {"id": 1, "volume": 2, "min_volume": 5, "max_volume": 35},
            auth_instance,
        )
        assert zone.volume_level == 0.0

    def test_source_missing_returns_none(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.source is None

    def test_source_prefers_source_name(self, auth_instance):
        zone = SoundZone(
            {"id": 1, "source_name": "Aux", "source": "Radio"}, auth_instance
        )
        assert zone.source == "Aux"

    def test_source_falls_back_to_source(self, auth_instance):
        zone = SoundZone({"id": 1, "source": "Radio"}, auth_instance)
        assert zone.source == "Radio"

    def test_sources_array_format(self, auth_instance):
        zone = SoundZone(SOUND_ZONE_DATA, auth_instance)
        assert zone.sources == [
            {"name": "Radio", "id": 0},
            {"name": "Aux", "id": 1},
        ]

    def test_sources_flat_format(self, auth_instance):
        zone = SoundZone(SOUND_ZONE_FLAT_DATA, auth_instance)
        # source_1 has no id_source_1 companion, so its id defaults to N-1.
        assert zone.sources == [
            {"name": "Radio", "id": 0},
            {"name": "Aux", "id": 7},
        ]

    def test_sources_mixed_formats_deduped(self, auth_instance):
        zone = SoundZone(
            {
                "id": 1,
                "sources": [{"source": "Radio", "id": 0}],
                "source_1": "Radio",
                "source_2": "Aux",
                "id_source_2": 5,
            },
            auth_instance,
        )
        assert zone.sources == [
            {"name": "Radio", "id": 0},
            {"name": "Aux", "id": 5},
        ]

    def test_sources_empty(self, auth_instance):
        zone = SoundZone({"id": 1}, auth_instance)
        assert zone.sources == []

    def test_sources_none_array(self, auth_instance):
        zone = SoundZone({"id": 1, "sources": None}, auth_instance)
        assert zone.sources == []


class TestSoundZoneAction:
    def test_values(self):
        assert SoundZoneAction.STANDBY.value == "standby"
        assert SoundZoneAction.MUTE.value == "mute"
        assert SoundZoneAction.VOLUME.value == "volume"
        assert SoundZoneAction.SOURCE.value == "source"


class TestSoundZoneControl:
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_turn_on(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_FLAT_DATA), auth_instance)
        assert zone.is_on is False

        await zone.async_turn_on()

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 4,
                "action": "standby",
                "value": 0,
            }
        )
        assert zone.is_on is True

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_turn_off(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)
        assert zone.is_on is True

        await zone.async_turn_off()

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 3,
                "action": "standby",
                "value": 1,
            }
        )
        assert zone.is_on is False

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_mute_true(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)
        assert zone.is_muted is False

        await zone.async_set_mute(True)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 3,
                "action": "mute",
                "value": 1,
            }
        )
        assert zone.is_muted is True

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_mute_false(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_FLAT_DATA), auth_instance)
        assert zone.is_muted is True

        await zone.async_set_mute(False)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 4,
                "action": "mute",
                "value": 0,
            }
        )
        assert zone.is_muted is False

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_volume_level(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_FLAT_DATA), auth_instance)

        # 0.5 on the 5-35 range -> 5 + 30 * 0.5 = 20
        await zone.async_set_volume_level(0.5)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 4,
                "action": "volume",
                "value": 20,
            }
        )
        assert zone.volume == 20

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_volume_level_rounds(
        self, mock_send_command, auth_instance
    ):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)

        # 0.33 on the 0-50 range -> 16.5, rounds to 16 (banker's rounding)
        await zone.async_set_volume_level(0.33)

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 3,
                "action": "volume",
                "value": 16,
            }
        )
        assert zone.volume == 16

    @pytest.mark.parametrize("level", [-0.1, 1.1])
    async def test_async_set_volume_level_out_of_range_raises(
        self, auth_instance, level
    ):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)

        with pytest.raises(ValueError, match="volume_level must be between"):
            await zone.async_set_volume_level(level)

    async def test_async_set_volume_level_missing_range_raises(self, auth_instance):
        zone = SoundZone({"id": 1, "volume": 10}, auth_instance)

        with pytest.raises(ValueError, match="does not report its"):
            await zone.async_set_volume_level(0.5)

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_select_source(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)

        await zone.async_select_source("Aux")

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 3,
                "action": "source",
                "value": 1,
            }
        )
        assert zone.source == "Aux"

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_select_source_flat_format(
        self, mock_send_command, auth_instance
    ):
        zone = SoundZone(dict(SOUND_ZONE_FLAT_DATA), auth_instance)

        await zone.async_select_source("Aux")

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "sound_switch_req",
                "id": 4,
                "action": "source",
                "value": 7,
            }
        )
        assert zone.source == "Aux"

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_select_source_unknown_raises(
        self, mock_send_command, auth_instance
    ):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)

        with pytest.raises(ValueError, match="Source 'Bluetooth' is not available"):
            await zone.async_select_source("Bluetooth")
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_select_source_none_id_raises(
        self, mock_send_command, auth_instance
    ):
        zone = SoundZone({"id": 1, "sources": [{"source": "Radio"}]}, auth_instance)

        with pytest.raises(ValueError, match="Source 'Radio' is not available"):
            await zone.async_select_source("Radio")
        mock_send_command.assert_not_called()

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_send_source_command(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)

        await zone.async_send_source_command(7, "next_track")

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "suftif_cmd_req",
                "id": 7,
                "action": "next_track",
            }
        )


class TestSoundZoneRefresh:
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_refresh(self, mock_send_command, auth_instance):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "sound_room_src_resp",
            "cseq": 5,
            "sl_data_ack_reason": 0,
            "id": 3,
            "standby": 1,
            "mute": 1,
            "volume": 30,
        }

        await zone.async_refresh()

        mock_send_command.assert_called_once_with(
            {"cmd_name": "sound_room_src_req", "value": 3},
            response_command="sound_room_src_resp",
        )
        assert zone.is_on is False
        assert zone.is_muted is True
        assert zone.volume == 30
        # Protocol envelope keys must not leak into the zone data.
        assert "cseq" not in zone.raw_data
        assert "cmd_name" not in zone.raw_data
        assert "sl_data_ack_reason" not in zone.raw_data

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_refresh_id_mismatch_ignored(
        self, mock_send_command, auth_instance
    ):
        zone = SoundZone(dict(SOUND_ZONE_DATA), auth_instance)
        mock_send_command.return_value = {
            "cmd_name": "sound_room_src_resp",
            "cseq": 5,
            "sl_data_ack_reason": 0,
            "id": 99,
            "standby": 1,
        }

        await zone.async_refresh()

        assert zone.is_on is True
        assert zone.volume == 25
