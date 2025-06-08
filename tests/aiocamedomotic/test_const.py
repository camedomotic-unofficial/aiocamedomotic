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

import pytest


def test_ack_error_codes_exist():
    """Test that ACK_ERROR_CODES dictionary contains all expected error codes."""
    from aiocamedomotic.const import ACK_ERROR_CODES

    expected_codes = {1, 3, 4, 5, 6, 7, 8, 9, 10, 11}
    assert set(ACK_ERROR_CODES.keys()) == expected_codes


def test_ack_error_codes_messages():
    """Test that ACK_ERROR_CODES contains correct error messages."""
    from aiocamedomotic.const import ACK_ERROR_CODES

    expected_messages = {
        1: "Invalid user.",
        3: "Too many sessions during login.",
        4: "Error occurred in JSON Syntax.",
        5: "No session layer command tag.",
        6: "Unrecognized session layer command.",
        7: "No client ID in request.",
        8: "Wrong client ID in request.",
        9: "Wrong application command.",
        10: "No reply to application command, maybe service down.",
        11: "Wrong application data.",
    }

    assert ACK_ERROR_CODES == expected_messages


def test_auth_error_codes():
    """Test that AUTH_ERROR_CODES contains the correct authentication error codes."""
    from aiocamedomotic.const import AUTH_ERROR_CODES

    expected_auth_codes = {1, 3}
    assert AUTH_ERROR_CODES == expected_auth_codes


def test_get_ack_error_message_known_codes():
    """Test get_ack_error_message function with known error codes."""
    from aiocamedomotic.const import get_ack_error_message

    # Test known error codes
    assert get_ack_error_message(1) == "Invalid user."
    assert get_ack_error_message(3) == "Too many sessions during login."
    assert get_ack_error_message(4) == "Error occurred in JSON Syntax."
    assert get_ack_error_message(11) == "Wrong application data."


def test_get_ack_error_message_unknown_code():
    """Test get_ack_error_message function with unknown error code."""
    from aiocamedomotic.const import get_ack_error_message

    # Test unknown error code
    assert get_ack_error_message(99) == "Unknown error code: 99"
    assert get_ack_error_message(0) == "Unknown error code: 0"
    assert get_ack_error_message(-1) == "Unknown error code: -1"


def test_get_ack_error_message_edge_cases():
    """Test get_ack_error_message function with edge cases."""
    from aiocamedomotic.const import get_ack_error_message

    # Test edge cases
    assert get_ack_error_message(1000) == "Unknown error code: 1000"
    assert get_ack_error_message(2) == "Unknown error code: 2"  # Code 2 is not defined


def test_is_auth_error_true_cases():
    """Test is_auth_error function with authentication error codes."""
    from aiocamedomotic.const import is_auth_error

    # Test authentication error codes
    assert is_auth_error(1) is True
    assert is_auth_error(3) is True


def test_is_auth_error_false_cases():
    """Test is_auth_error function with non-authentication error codes."""
    from aiocamedomotic.const import is_auth_error

    # Test non-authentication error codes
    assert is_auth_error(4) is False
    assert is_auth_error(5) is False
    assert is_auth_error(6) is False
    assert is_auth_error(7) is False
    assert is_auth_error(8) is False
    assert is_auth_error(9) is False
    assert is_auth_error(10) is False
    assert is_auth_error(11) is False

    # Test unknown codes
    assert is_auth_error(0) is False
    assert is_auth_error(2) is False
    assert is_auth_error(99) is False
    assert is_auth_error(-1) is False


def test_is_auth_error_edge_cases():
    """Test is_auth_error function with edge cases."""
    from aiocamedomotic.const import is_auth_error

    # Test edge cases
    assert is_auth_error(1000) is False
    assert is_auth_error(2) is False  # Code 2 is not defined


def test_constants_immutability():
    """Test that constants can be imported and used without modification."""
    from aiocamedomotic.const import ACK_ERROR_CODES, AUTH_ERROR_CODES

    # Test that we can access the constants
    assert len(ACK_ERROR_CODES) == 10
    assert len(AUTH_ERROR_CODES) == 2

    # Test that constants are the expected types
    assert isinstance(ACK_ERROR_CODES, dict)
    assert isinstance(AUTH_ERROR_CODES, set)


def test_all_auth_codes_in_ack_codes():
    """Test that all authentication error codes are also in ACK_ERROR_CODES."""
    from aiocamedomotic.const import ACK_ERROR_CODES, AUTH_ERROR_CODES

    for auth_code in AUTH_ERROR_CODES:
        assert auth_code in ACK_ERROR_CODES
