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

"""Tests for aiocamedomotic constants."""


def test_ack_error_code_members():
    """Test that AckErrorCode contains all expected members with correct values."""
    from aiocamedomotic.const import AckErrorCode

    expected = {
        "INVALID_USER": 1,
        "TOO_MANY_SESSIONS": 3,
        "JSON_SYNTAX_ERROR": 4,
        "NO_SESSION_COMMAND_TAG": 5,
        "UNRECOGNIZED_SESSION_COMMAND": 6,
        "NO_CLIENT_ID": 7,
        "WRONG_CLIENT_ID": 8,
        "WRONG_APPLICATION_COMMAND": 9,
        "NO_REPLY": 10,
        "WRONG_APPLICATION_DATA": 11,
    }
    assert len(AckErrorCode) == 10
    for name, value in expected.items():
        assert AckErrorCode[name] == value


def test_ack_error_code_messages():
    """Test that each AckErrorCode member has the correct message."""
    from aiocamedomotic.const import AckErrorCode

    expected_messages = {
        AckErrorCode.INVALID_USER: "Invalid user.",
        AckErrorCode.TOO_MANY_SESSIONS: "Too many sessions during login.",
        AckErrorCode.JSON_SYNTAX_ERROR: "Error occurred in JSON Syntax.",
        AckErrorCode.NO_SESSION_COMMAND_TAG: "No session layer command tag.",
        AckErrorCode.UNRECOGNIZED_SESSION_COMMAND: (
            "Unrecognized session layer command."
        ),
        AckErrorCode.NO_CLIENT_ID: "No client ID in request.",
        AckErrorCode.WRONG_CLIENT_ID: "Wrong client ID in request.",
        AckErrorCode.WRONG_APPLICATION_COMMAND: "Wrong application command.",
        AckErrorCode.NO_REPLY: "No reply to application command, maybe service down.",
        AckErrorCode.WRONG_APPLICATION_DATA: "Wrong application data.",
    }
    for member, message in expected_messages.items():
        assert member.message == message


def test_ack_error_code_is_auth():
    """Test that is_auth is True only for authentication-related codes."""
    from aiocamedomotic.const import AckErrorCode

    auth_members = {AckErrorCode.INVALID_USER, AckErrorCode.TOO_MANY_SESSIONS}
    for member in AckErrorCode:
        if member in auth_members:
            assert member.is_auth is True, f"{member.name} should be auth"
        else:
            assert member.is_auth is False, f"{member.name} should not be auth"


def test_ack_error_code_int_comparison():
    """Test that AckErrorCode members compare equal to their integer value."""
    from aiocamedomotic.const import AckErrorCode

    assert AckErrorCode.INVALID_USER == 1
    assert AckErrorCode.NO_CLIENT_ID == 7
    assert isinstance(AckErrorCode.INVALID_USER, int)


def test_ack_error_code_unknown_raises():
    """Test that constructing AckErrorCode with an unknown value raises ValueError."""
    import pytest

    from aiocamedomotic.const import AckErrorCode

    with pytest.raises(ValueError):
        AckErrorCode(99)
    with pytest.raises(ValueError):
        AckErrorCode(0)
    with pytest.raises(ValueError):
        AckErrorCode(2)


def test_came_mac_prefixes_type():
    """Test that CAME_MAC_PREFIXES is a tuple of strings."""
    from aiocamedomotic.const import CAME_MAC_PREFIXES

    assert isinstance(CAME_MAC_PREFIXES, tuple)
    assert len(CAME_MAC_PREFIXES) > 0
    for prefix in CAME_MAC_PREFIXES:
        assert isinstance(prefix, str)


def test_came_mac_prefixes_format():
    """Test that each prefix matches the XX:XX:XX OUI format."""
    import re

    from aiocamedomotic.const import CAME_MAC_PREFIXES

    oui_pattern = re.compile(r"^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$")
    for prefix in CAME_MAC_PREFIXES:
        assert oui_pattern.match(prefix), f"Invalid OUI format: {prefix}"


def test_came_mac_prefixes_contains_bpt():
    """Test that the known BPT S.p.A. OUI prefix is present."""
    from aiocamedomotic.const import CAME_MAC_PREFIXES

    assert "00:1C:B2" in CAME_MAC_PREFIXES


def test_came_mac_prefixes_importable_from_package():
    """Test that CAME_MAC_PREFIXES is importable from the top-level package."""
    from aiocamedomotic import CAME_MAC_PREFIXES

    assert isinstance(CAME_MAC_PREFIXES, tuple)
    assert "00:1C:B2" in CAME_MAC_PREFIXES
