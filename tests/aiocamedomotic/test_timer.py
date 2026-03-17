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
from aiocamedomotic.models.timer import Timer, TimerTimeSlot


class TestTimerTimeSlot:
    def test_init_full(self):
        data = {
            "start": {"hour": 18, "min": 30, "sec": 0},
            "stop": {"hour": 22, "min": 0, "sec": 0},
            "active": 1,
            "index": 1,
        }
        slot = TimerTimeSlot(data)
        assert slot.index == 1
        assert slot.start_hour == 18
        assert slot.start_min == 30
        assert slot.start_sec == 0
        assert slot.stop_hour == 22
        assert slot.stop_min == 0
        assert slot.stop_sec == 0
        assert slot.active is True

    def test_init_minimal(self):
        data = {"start": {"hour": 10, "min": 0, "sec": 0}, "index": 0}
        slot = TimerTimeSlot(data)
        assert slot.index == 0
        assert slot.start_hour == 10
        assert slot.start_min == 0
        assert slot.start_sec == 0
        assert slot.stop_hour is None
        assert slot.stop_min is None
        assert slot.stop_sec is None
        assert slot.active is None

    def test_missing_start_raises(self):
        with pytest.raises(ValueError, match="'index' and 'start'"):
            TimerTimeSlot({"index": 0})

    def test_missing_index_raises(self):
        with pytest.raises(ValueError, match="'index' and 'start'"):
            TimerTimeSlot({"start": {"hour": 0, "min": 0, "sec": 0}})

    def test_start_time_defaults(self):
        data = {"start": {}, "index": 0}
        slot = TimerTimeSlot(data)
        assert slot.start_hour == 0
        assert slot.start_min == 0
        assert slot.start_sec == 0

    def test_active_false(self):
        data = {
            "start": {"hour": 0, "min": 0, "sec": 0},
            "active": 0,
            "index": 0,
        }
        slot = TimerTimeSlot(data)
        assert slot.active is False

    def test_frozen(self):
        data = {"start": {"hour": 0, "min": 0, "sec": 0}, "index": 0}
        slot = TimerTimeSlot(data)
        with pytest.raises(AttributeError):
            slot.raw_data = {}  # type: ignore[misc]


class TestTimer:
    def test_init_valid(self, timer_data, auth_instance):
        timer = Timer(timer_data, auth_instance)
        assert timer.raw_data == timer_data
        assert timer.auth == auth_instance

    def test_init_minimal(self, timer_data_minimal, auth_instance):
        timer = Timer(timer_data_minimal, auth_instance)
        assert timer.id == 163
        assert timer.name == "Test timer"
        assert timer.enabled is True
        assert timer.days == 21

    def test_missing_name_raises(self, auth_instance):
        with pytest.raises(ValueError):
            Timer({"id": 1}, auth_instance)

    def test_missing_id_raises(self, auth_instance):
        with pytest.raises(ValueError):
            Timer({"name": "Test"}, auth_instance)

    def test_none_data_raises(self, auth_instance):
        with pytest.raises((ValueError, TypeError)):
            Timer(None, auth_instance)  # type: ignore[arg-type]

    def test_invalid_auth_raises(self, timer_data):
        with pytest.raises(ValueError, match="'auth' must be an instance of Auth"):
            Timer(timer_data, "not_auth")  # type: ignore[arg-type]

    def test_enabled_true(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "enabled": 1}, auth_instance)
        assert timer.enabled is True

    def test_enabled_false(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "enabled": 0}, auth_instance)
        assert timer.enabled is False

    def test_enabled_missing(self, auth_instance):
        timer = Timer({"name": "T", "id": 1}, auth_instance)
        assert timer.enabled is False

    def test_properties(self, timer_data, auth_instance):
        timer = Timer(timer_data, auth_instance)
        assert timer.id == 117
        assert timer.name == "Temporizzatore"
        assert timer.enabled is False
        assert timer.days == 1
        assert timer.bars == 2

    def test_days_bitmask(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 85}, auth_instance)
        assert timer.active_days == ["Monday", "Wednesday", "Friday", "Sunday"]

    def test_days_zero(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 0}, auth_instance)
        assert timer.active_days == []

    def test_days_all(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 127}, auth_instance)
        assert len(timer.active_days) == 7
        assert timer.active_days[0] == "Monday"
        assert timer.active_days[6] == "Sunday"

    def test_days_missing(self, auth_instance):
        timer = Timer({"name": "T", "id": 1}, auth_instance)
        assert timer.days == 0
        assert timer.active_days == []

    def test_is_active_on_day(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 85}, auth_instance)
        assert timer.is_active_on_day(0) is True  # Monday
        assert timer.is_active_on_day(1) is False  # Tuesday
        assert timer.is_active_on_day(2) is True  # Wednesday
        assert timer.is_active_on_day(4) is True  # Friday
        assert timer.is_active_on_day(6) is True  # Sunday

    def test_is_active_on_day_invalid_index(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 127}, auth_instance)
        assert timer.is_active_on_day(-1) is False
        assert timer.is_active_on_day(7) is False

    def test_timetable_full(self, timer_data, auth_instance):
        timer = Timer(timer_data, auth_instance)
        timetable = timer.timetable
        assert len(timetable) == 2
        assert isinstance(timetable[0], TimerTimeSlot)
        assert timetable[0].start_hour == 2
        assert timetable[0].stop_hour == 8
        assert timetable[0].active is False
        assert timetable[1].start_hour == 18
        assert timetable[1].active is True

    def test_timetable_minimal(self, timer_data_minimal, auth_instance):
        timer = Timer(timer_data_minimal, auth_instance)
        timetable = timer.timetable
        assert len(timetable) == 1
        assert timetable[0].start_hour == 10
        assert timetable[0].stop_hour is None
        assert timetable[0].active is None

    def test_timetable_empty(self, auth_instance):
        data = {"name": "T", "id": 1, "timetable": []}
        timer = Timer(data, auth_instance)
        assert timer.timetable == []

    def test_timetable_missing(self, auth_instance):
        data = {"name": "T", "id": 1}
        timer = Timer(data, auth_instance)
        assert timer.timetable == []

    def test_timetable_not_list(self, auth_instance):
        data = {"name": "T", "id": 1, "timetable": "invalid"}
        timer = Timer(data, auth_instance)
        assert timer.timetable == []

    def test_timetable_malformed_entry_skipped(self, auth_instance):
        data = {
            "name": "T",
            "id": 1,
            "timetable": [
                {"start": {"hour": 10, "min": 0, "sec": 0}, "index": 0},
                "not_a_dict",
                {"missing": "start_key"},
            ],
        }
        timer = Timer(data, auth_instance)
        timetable = timer.timetable
        assert len(timetable) == 1
        assert timetable[0].start_hour == 10

    def test_bars_property(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "bars": 3}, auth_instance)
        assert timer.bars == 3

    def test_bars_missing(self, auth_instance):
        timer = Timer({"name": "T", "id": 1}, auth_instance)
        assert timer.bars == 0


class TestTimerControl:
    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_enable(self, mock_send_command, timer_data, auth_instance):
        timer = Timer(timer_data, auth_instance)
        assert timer.enabled is False

        await timer.async_enable()

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "timers_enable_req",
                "id": 117,
                "value": 1,
            }
        )
        assert timer.enabled is True

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_disable(
        self, mock_send_command, timer_data_minimal, auth_instance
    ):
        timer = Timer(timer_data_minimal, auth_instance)
        assert timer.enabled is True

        await timer.async_disable()

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "timers_enable_req",
                "id": 163,
                "value": 0,
            }
        )
        assert timer.enabled is False

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_enable_day(self, mock_send_command, auth_instance):
        data = {"name": "T", "id": 1, "days": 0}
        timer = Timer(data, auth_instance)

        await timer.async_enable_day(1)  # Tuesday

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "timers_enable_day_req",
                "id": 1,
                "day": 1,
                "value": 1,
            }
        )
        assert timer.days == 2  # bit 1 set
        assert timer.is_active_on_day(1) is True

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_disable_day(self, mock_send_command, auth_instance):
        data = {"name": "T", "id": 1, "days": 127}  # all days
        timer = Timer(data, auth_instance)

        await timer.async_disable_day(4)  # Friday

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "timers_enable_day_req",
                "id": 1,
                "day": 4,
                "value": 0,
            }
        )
        assert timer.days == 127 & ~(1 << 4)  # bit 4 cleared = 111
        assert timer.is_active_on_day(4) is False

    @pytest.mark.asyncio
    async def test_async_enable_day_invalid(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 0}, auth_instance)
        with pytest.raises(ValueError, match="day must be 0-6"):
            await timer.async_enable_day(-1)
        with pytest.raises(ValueError, match="day must be 0-6"):
            await timer.async_enable_day(7)

    @pytest.mark.asyncio
    async def test_async_disable_day_invalid(self, auth_instance):
        timer = Timer({"name": "T", "id": 1, "days": 127}, auth_instance)
        with pytest.raises(ValueError, match="day must be 0-6"):
            await timer.async_disable_day(7)

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_timetable(self, mock_send_command, auth_instance):
        timer = Timer({"name": "T", "id": 1}, auth_instance)

        await timer.async_set_timetable(
            [
                (10, 0, 0),
                None,
                (7, 3, 3),
                None,
            ]
        )

        mock_send_command.assert_called_once_with(
            {
                "cmd_name": "timers_set_req",
                "id": 1,
                "timetable": [
                    {"start": {"hour": 10, "min": 0, "sec": 0}},
                    {"start": {"hour": -1, "min": -1, "sec": -1}},
                    {"start": {"hour": 7, "min": 3, "sec": 3}},
                    {"start": {"hour": -1, "min": -1, "sec": -1}},
                ],
            }
        )
        # Verify local raw_data updated with non-empty slots only
        timetable = timer.timetable
        assert len(timetable) == 2
        assert timetable[0].index == 0
        assert timetable[0].start_hour == 10
        assert timetable[1].index == 2
        assert timetable[1].start_hour == 7

    @pytest.mark.asyncio
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_async_set_timetable_all_empty(
        self, mock_send_command, auth_instance
    ):
        timer = Timer({"name": "T", "id": 1}, auth_instance)

        await timer.async_set_timetable([None, None, None, None])

        assert timer.timetable == []

    @pytest.mark.asyncio
    async def test_async_set_timetable_wrong_count(self, auth_instance):
        timer = Timer({"name": "T", "id": 1}, auth_instance)
        with pytest.raises(ValueError, match="exactly 4 slots"):
            await timer.async_set_timetable([(10, 0, 0)])
        with pytest.raises(ValueError, match="exactly 4 slots"):
            await timer.async_set_timetable([(10, 0, 0), None, None, None, None])
