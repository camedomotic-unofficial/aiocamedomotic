# SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import logging
from datetime import date, datetime, time

import pytest

from aiocamedomotic.models import (
    WEEKDAYS,
    LoadsCtrlProfile,
    ProfileDay,
    ProfileSpan,
    ThermoProfile,
    WeeklyProfile,
)

# Wire values captured from a real server (swver 3.0.1)
LOADSCTRL_WIRE = ["4" * 24] * 7
THERMO_MIXED_ROW = "1" * 32 + "4" * 4 + "3" * 28 + "1" * 32


class TestProfileDay:
    def test_weekday_values_match_date_weekday(self):
        # 2026-07-06 is a Monday
        for offset, day in enumerate(WEEKDAYS):
            assert ProfileDay(date(2026, 7, 6 + offset).weekday()) == day

    def test_jolly_is_row_eight(self):
        assert ProfileDay.JOLLY == 7

    def test_weekdays_excludes_jolly(self):
        assert len(WEEKDAYS) == 7
        assert ProfileDay.JOLLY not in WEEKDAYS


class TestLoadsCtrlProfileFromWire:
    def test_happy_path(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        assert profile.level_at(ProfileDay.MONDAY, 0) == 4

    def test_wrong_row_count(self):
        with pytest.raises(ValueError, match="exactly 7 strings"):
            LoadsCtrlProfile.from_wire(["4" * 24] * 6)

    def test_non_string_row(self):
        with pytest.raises(ValueError, match="must be a string"):
            LoadsCtrlProfile.from_wire([44444] + ["4" * 24] * 6)

    def test_wrong_row_length(self):
        with pytest.raises(ValueError, match="exactly 24 characters"):
            LoadsCtrlProfile.from_wire(["4" * 23] + ["4" * 24] * 6)

    def test_digit_zero_rejected(self):
        with pytest.raises(ValueError, match="only digits"):
            LoadsCtrlProfile.from_wire(["0" * 24] + ["4" * 24] * 6)

    def test_digit_six_rejected(self):
        with pytest.raises(ValueError, match="only digits"):
            LoadsCtrlProfile.from_wire(["6" * 24] + ["4" * 24] * 6)

    def test_letter_rejected(self):
        with pytest.raises(ValueError, match="only digits"):
            LoadsCtrlProfile.from_wire(["a" * 24] + ["4" * 24] * 6)

    def test_non_sequence_rejected(self):
        with pytest.raises(ValueError, match="exactly 7 strings"):
            LoadsCtrlProfile.from_wire("4" * 24)


class TestThermoProfileFromWire:
    def test_happy_path(self, thermo_profile_wire_data):
        profile = ThermoProfile.from_wire(thermo_profile_wire_data)
        assert profile.level_at(ProfileDay.JOLLY, 8) == 4

    def test_wrong_row_count(self, thermo_profile_wire_data):
        with pytest.raises(ValueError, match="exactly 8 strings"):
            ThermoProfile.from_wire(thermo_profile_wire_data[:7])

    def test_non_hour_uniform_accepted_with_warning(self, caplog):
        # Hour 0 is "1112": not app-writable, but must be preserved
        anomalous = ["1112" + "1" * 92] + ["1" * 96] * 7
        with caplog.at_level(logging.WARNING):
            profile = ThermoProfile.from_wire(anomalous)
        assert "within the same hour" in caplog.text
        assert profile.to_wire() == anomalous

    def test_hour_uniform_no_warning(self, thermo_profile_wire_data, caplog):
        with caplog.at_level(logging.WARNING):
            ThermoProfile.from_wire(thermo_profile_wire_data)
        assert caplog.text == ""


class TestToWireRoundTrip:
    def test_loadsctrl_round_trip(self):
        assert LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE).to_wire() == LOADSCTRL_WIRE

    def test_thermo_round_trip(self, thermo_profile_wire_data):
        profile = ThermoProfile.from_wire(thermo_profile_wire_data)
        assert profile.to_wire() == thermo_profile_wire_data

    def test_thermo_mixed_levels_round_trip(self):
        wire = [THERMO_MIXED_ROW] * 8
        assert ThermoProfile.from_wire(wire).to_wire() == wire

    def test_to_wire_returns_fresh_list(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        wire = profile.to_wire()
        wire[0] = "tampered"
        assert profile.to_wire() == LOADSCTRL_WIRE


class TestConstant:
    def test_all_slots_set(self):
        profile = LoadsCtrlProfile.constant(3)
        assert profile.to_wire() == ["3" * 24] * 7

    def test_thermo_includes_jolly(self):
        profile = ThermoProfile.constant(2)
        assert profile.to_wire() == ["2" * 96] * 8

    def test_invalid_level(self):
        with pytest.raises(ValueError, match="level must be one of"):
            LoadsCtrlProfile.constant(6)

    def test_non_int_level(self):
        with pytest.raises(ValueError, match="level must be an int"):
            LoadsCtrlProfile.constant("3")


class TestLevelAt:
    def test_int_hour(self):
        profile = ThermoProfile.from_wire([THERMO_MIXED_ROW] * 8)
        assert profile.level_at(ProfileDay.MONDAY, 7) == 1
        assert profile.level_at(ProfileDay.MONDAY, 8) == 4
        assert profile.level_at(ProfileDay.MONDAY, 9) == 3

    def test_time_object(self):
        profile = ThermoProfile.from_wire([THERMO_MIXED_ROW] * 8)
        assert profile.level_at(ProfileDay.MONDAY, time(8, 59)) == 4

    def test_datetime_uses_time_of_day(self):
        profile = ThermoProfile.from_wire([THERMO_MIXED_ROW] * 8)
        # The datetime's date is NOT used to pick the day
        moment = datetime(2026, 7, 10, 8, 15)
        assert profile.level_at(ProfileDay.SUNDAY, moment) == 4

    def test_mid_hour_time_on_loadsctrl(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        assert profile.level_at(ProfileDay.FRIDAY, time(14, 37)) == 4

    def test_quarter_resolution_on_anomalous_data(self):
        anomalous = ["1112" + "1" * 92] + ["1" * 96] * 7
        profile = ThermoProfile.from_wire(anomalous)
        assert profile.level_at(ProfileDay.MONDAY, time(0, 40)) == 1
        assert profile.level_at(ProfileDay.MONDAY, time(0, 45)) == 2

    def test_invalid_day(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        with pytest.raises(ValueError, match="JOLLY is not a valid day"):
            profile.level_at(ProfileDay.JOLLY, 0)

    def test_hour_out_of_range(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        with pytest.raises(ValueError, match="range 0-23"):
            profile.level_at(ProfileDay.MONDAY, 24)

    def test_invalid_at_type(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        with pytest.raises(ValueError, match="at must be"):
            profile.level_at(ProfileDay.MONDAY, "08:00")


class TestSpans:
    def test_multi_run_day(self):
        profile = ThermoProfile.from_wire([THERMO_MIXED_ROW] * 8)
        assert profile.spans(ProfileDay.MONDAY) == [
            ProfileSpan(start=time(0), end=time(8), level=1),
            ProfileSpan(start=time(8), end=time(9), level=4),
            ProfileSpan(start=time(9), end=time(16), level=3),
            ProfileSpan(start=time(16), end=time(0), level=1),
        ]

    def test_constant_day_single_span(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        assert profile.spans(ProfileDay.SUNDAY) == [
            ProfileSpan(start=time(0), end=time(0), level=4),
        ]

    def test_anomalous_data_reports_quarter_boundary(self):
        anomalous = ["1112" + "1" * 92] + ["1" * 96] * 7
        profile = ThermoProfile.from_wire(anomalous)
        assert profile.spans(ProfileDay.MONDAY) == [
            ProfileSpan(start=time(0), end=time(0, 45), level=1),
            ProfileSpan(start=time(0, 45), end=time(1), level=2),
            ProfileSpan(start=time(1), end=time(0), level=1),
        ]

    def test_invalid_day(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        with pytest.raises(ValueError, match="JOLLY is not a valid day"):
            profile.spans(ProfileDay.JOLLY)


class TestWithLevel:
    def test_single_day_and_range(self):
        profile = LoadsCtrlProfile.constant(4)
        edited = profile.with_level(2, days=ProfileDay.SUNDAY, start=8, end=18)
        expected = ["4" * 24] * 6 + ["4" * 8 + "2" * 10 + "4" * 6]
        assert edited.to_wire() == expected

    def test_original_unchanged(self):
        profile = LoadsCtrlProfile.constant(4)
        edited = profile.with_level(2, days=ProfileDay.SUNDAY)
        assert profile.to_wire() == ["4" * 24] * 7
        assert edited is not profile

    def test_days_none_targets_all_rows_including_jolly(self):
        profile = ThermoProfile.constant(1)
        edited = profile.with_level(5, start=8, end=9)
        assert edited.level_at(ProfileDay.JOLLY, 8) == 5
        assert edited.level_at(ProfileDay.MONDAY, 8) == 5

    def test_weekdays_excludes_jolly(self):
        profile = ThermoProfile.constant(1)
        edited = profile.with_level(5, days=WEEKDAYS, start=8, end=9)
        assert edited.level_at(ProfileDay.JOLLY, 8) == 1
        assert edited.level_at(ProfileDay.SUNDAY, 8) == 5

    def test_int_and_time_hours_equivalent(self):
        profile = LoadsCtrlProfile.constant(4)
        by_int = profile.with_level(2, start=8, end=18)
        by_time = profile.with_level(2, start=time(8), end=time(18))
        assert by_int == by_time

    def test_end_time_midnight_means_end_of_day(self):
        profile = LoadsCtrlProfile.constant(4)
        by_time = profile.with_level(2, start=time(18), end=time(0))
        by_none = profile.with_level(2, start=18)
        assert by_time == by_none

    def test_non_whole_hour_start_rejected_loadsctrl(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="whole hour"):
            profile.with_level(2, start=time(8, 30))

    def test_non_whole_hour_start_rejected_thermo(self):
        # Rejected on thermo too, despite its 15-min wire slots
        profile = ThermoProfile.constant(1)
        with pytest.raises(ValueError, match="whole hour"):
            profile.with_level(2, start=time(8, 30))

    def test_start_not_before_end(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="start must be before end"):
            profile.with_level(2, start=18, end=8)

    def test_level_out_of_range(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="level must be one of"):
            profile.with_level(0)

    def test_jolly_rejected_on_loadsctrl(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(
            ValueError, match="JOLLY is not a valid day for LoadsCtrlProfile"
        ):
            profile.with_level(2, days=ProfileDay.JOLLY)

    def test_thermo_hour_writes_four_quarters(self):
        profile = ThermoProfile.constant(1)
        edited = profile.with_level(5, days=ProfileDay.MONDAY, start=8, end=9)
        assert edited.to_wire()[0] == "1" * 32 + "5555" + "1" * 60

    def test_untouched_anomalous_quarters_preserved(self):
        anomalous = ["1112" + "1" * 92] + ["1" * 96] * 7
        profile = ThermoProfile.from_wire(anomalous)
        edited = profile.with_level(5, days=ProfileDay.MONDAY, start=8, end=9)
        assert edited.to_wire()[0] == "1112" + "1" * 28 + "5555" + "1" * 60

    def test_int_day_accepted(self):
        profile = LoadsCtrlProfile.constant(4)
        edited = profile.with_level(2, days=0, start=8, end=9)
        assert edited.level_at(ProfileDay.MONDAY, 8) == 2

    def test_invalid_days_type(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="days must be"):
            profile.with_level(2, days="monday")

    def test_non_int_day_in_iterable(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="day must be a ProfileDay or an int"):
            profile.with_level(2, days=["monday"])

    def test_out_of_range_int_day(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="not a valid ProfileDay value"):
            profile.with_level(2, days=9)

    def test_invalid_start_type(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="start must be an int hour"):
            profile.with_level(2, start="08:00")

    def test_start_hour_out_of_range(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="start must be in the range 0-23"):
            profile.with_level(2, start=24)


class TestWithDayCopied:
    def test_single_target(self):
        profile = LoadsCtrlProfile.constant(4).with_level(
            2, days=ProfileDay.MONDAY, start=8, end=18
        )
        edited = profile.with_day_copied(ProfileDay.MONDAY, to=ProfileDay.TUESDAY)
        assert edited.to_wire()[1] == edited.to_wire()[0]
        assert edited.to_wire()[2] == "4" * 24

    def test_multiple_targets(self):
        profile = LoadsCtrlProfile.constant(4).with_level(
            2, days=ProfileDay.MONDAY, start=8, end=18
        )
        edited = profile.with_day_copied(
            ProfileDay.MONDAY, to=[ProfileDay.SATURDAY, ProfileDay.SUNDAY]
        )
        monday_row = edited.to_wire()[0]
        assert edited.to_wire()[5] == monday_row
        assert edited.to_wire()[6] == monday_row

    def test_jolly_as_target_on_thermo(self, thermo_profile_wire_data):
        profile = ThermoProfile.from_wire(thermo_profile_wire_data).with_level(
            5, days=ProfileDay.MONDAY
        )
        edited = profile.with_day_copied(ProfileDay.MONDAY, to=ProfileDay.JOLLY)
        assert edited.to_wire()[7] == "5" * 96

    def test_jolly_rejected_on_loadsctrl(self):
        profile = LoadsCtrlProfile.constant(4)
        with pytest.raises(ValueError, match="JOLLY is not a valid day"):
            profile.with_day_copied(ProfileDay.JOLLY, to=ProfileDay.MONDAY)


class TestEqualityAndRepr:
    def test_value_equality(self):
        assert LoadsCtrlProfile.constant(4) == LoadsCtrlProfile.from_wire(
            LOADSCTRL_WIRE
        )

    def test_value_inequality(self):
        assert LoadsCtrlProfile.constant(4) != LoadsCtrlProfile.constant(5)

    def test_hashable(self):
        assert len({LoadsCtrlProfile.constant(4), LoadsCtrlProfile.constant(4)}) == 1

    def test_cross_class_inequality(self):
        assert LoadsCtrlProfile.constant(4) != ThermoProfile.constant(4)

    def test_not_equal_to_wire_list(self):
        assert LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE) != LOADSCTRL_WIRE

    def test_repr(self):
        profile = LoadsCtrlProfile.from_wire(LOADSCTRL_WIRE)
        assert repr(profile) == f"LoadsCtrlProfile.from_wire({LOADSCTRL_WIRE!r})"


class TestAbstractBase:
    def test_direct_instantiation_rejected(self):
        with pytest.raises(TypeError, match="abstract base"):
            WeeklyProfile([[4] * 24] * 7)

    def test_from_wire_on_base_rejected(self):
        with pytest.raises(TypeError, match="abstract base"):
            WeeklyProfile.from_wire(LOADSCTRL_WIRE)

    def test_constant_on_base_rejected(self):
        with pytest.raises(TypeError, match="abstract base"):
            WeeklyProfile.constant(4)

    def test_subclass_without_days_rejected(self):
        with pytest.raises(TypeError, match="non-empty DAYS"):

            class BadProfile(WeeklyProfile):  # pylint: disable=unused-variable
                WIRE_SLOTS_PER_DAY = 24

    def test_subclass_with_bad_slot_count_rejected(self):
        with pytest.raises(TypeError, match="positive multiple"):

            class BadProfile(WeeklyProfile):  # pylint: disable=unused-variable
                DAYS = WEEKDAYS
                WIRE_SLOTS_PER_DAY = 25


class TestConstructorValidation:
    def test_rows_from_ints(self):
        profile = LoadsCtrlProfile([[4] * 24] * 7)
        assert profile.to_wire() == LOADSCTRL_WIRE

    def test_wrong_row_count(self):
        with pytest.raises(ValueError, match="exactly 7 day rows"):
            LoadsCtrlProfile([[4] * 24] * 6)

    def test_wrong_row_length(self):
        with pytest.raises(ValueError, match="exactly\\s+24 levels"):
            LoadsCtrlProfile([[4] * 23] + [[4] * 24] * 6)

    def test_invalid_level_value(self):
        with pytest.raises(ValueError, match="invalid level 6"):
            LoadsCtrlProfile([[6] * 24] + [[4] * 24] * 6)

    def test_bool_level_rejected(self):
        with pytest.raises(ValueError, match="invalid level True"):
            LoadsCtrlProfile([[True] * 24] + [[4] * 24] * 6)

    def test_string_row_rejected(self):
        with pytest.raises(ValueError, match="integer levels"):
            LoadsCtrlProfile(["4" * 24] + [[4] * 24] * 6)

    def test_non_sequence_rows_rejected(self):
        with pytest.raises(ValueError, match="sequence of exactly 7 day rows"):
            LoadsCtrlProfile(42)
