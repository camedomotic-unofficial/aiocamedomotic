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

"""Tests for aiocamedomotic error classes."""

import pytest


def test_all_error_classes_instantiation():
    """Test that all error classes can be instantiated properly."""
    from aiocamedomotic.errors import (
        CameDomoticError,
        CameDomoticAuthError,
        CameDomoticServerError,
        CameDomoticServerNotFoundError,
    )

    # Test base error
    base_error = CameDomoticError("Base error message")
    assert str(base_error) == "Base error message"

    # Test auth error
    auth_error = CameDomoticAuthError("Auth error message")
    assert str(auth_error) == "Auth error message"
    assert isinstance(auth_error, CameDomoticError)

    # Test server error
    server_error = CameDomoticServerError("Server error message")
    assert str(server_error) == "Server error message"
    assert isinstance(server_error, CameDomoticError)

    # Test server not found error
    not_found_error = CameDomoticServerNotFoundError("Not found error message")
    assert str(not_found_error) == "Not found error message"
    assert isinstance(not_found_error, CameDomoticError)


def test_error_inheritance_chain():
    """Test that error inheritance chain is correct."""
    from aiocamedomotic.errors import (
        CameDomoticError,
        CameDomoticAuthError,
        CameDomoticServerError,
        CameDomoticServerNotFoundError,
    )

    # Test inheritance
    assert issubclass(CameDomoticAuthError, CameDomoticError)
    assert issubclass(CameDomoticServerError, CameDomoticError)
    assert issubclass(CameDomoticServerNotFoundError, CameDomoticError)

    # Test that all inherit from Exception
    assert issubclass(CameDomoticError, Exception)


def test_error_with_none_message():
    """Test error classes with None message."""
    from aiocamedomotic.errors import CameDomoticError

    error = CameDomoticError(None)
    assert str(error) == "None"


def test_error_with_empty_message():
    """Test error classes with empty message."""
    from aiocamedomotic.errors import CameDomoticError

    error = CameDomoticError("")
    assert str(error) == ""


def test_error_with_non_string_message():
    """Test error classes with non-string message."""
    from aiocamedomotic.errors import CameDomoticError

    error = CameDomoticError(123)
    assert str(error) == "123"


def test_all_errors_with_args():
    """Test all error classes with args."""
    from aiocamedomotic.errors import (
        CameDomoticError,
        CameDomoticAuthError,
        CameDomoticServerError,
        CameDomoticServerNotFoundError,
    )

    # Test with multiple args
    base_error = CameDomoticError("Error", "Additional info")
    assert base_error.args == ("Error", "Additional info")

    auth_error = CameDomoticAuthError("Auth error", "Details")
    assert auth_error.args == ("Auth error", "Details")

    server_error = CameDomoticServerError("Server error", "Code: 500")
    assert server_error.args == ("Server error", "Code: 500")

    not_found_error = CameDomoticServerNotFoundError("Not found", "URL error")
    assert not_found_error.args == ("Not found", "URL error")


def test_error_repr():
    """Test error representation."""
    from aiocamedomotic.errors import CameDomoticError

    error = CameDomoticError("Test error")
    repr_str = repr(error)
    assert "CameDomoticError" in repr_str
    assert "Test error" in repr_str


def test_format_ack_error():
    """Test the format_ack_error static method."""
    from aiocamedomotic.errors import CameDomoticServerError

    # Test known ACK error codes
    assert CameDomoticServerError.format_ack_error(1) == "ACK error 1: Invalid user."
    assert (
        CameDomoticServerError.format_ack_error(3)
        == "ACK error 3: Too many sessions during login."
    )
    assert (
        CameDomoticServerError.format_ack_error(4)
        == "ACK error 4: Error occurred in JSON Syntax."
    )
    assert (
        CameDomoticServerError.format_ack_error(11)
        == "ACK error 11: Wrong application data."
    )

    # Test unknown ACK error code
    assert (
        CameDomoticServerError.format_ack_error(99)
        == "ACK error 99: Unknown error code: 99"
    )


def test_create_ack_error():
    """Test the create_ack_error static method."""
    from aiocamedomotic.errors import CameDomoticServerError, CameDomoticAuthError

    # Test authentication error codes (1, 3) return CameDomoticAuthError
    auth_error_1 = CameDomoticServerError.create_ack_error(1)
    assert isinstance(auth_error_1, CameDomoticAuthError)
    assert str(auth_error_1) == "ACK error 1: Invalid user."

    auth_error_3 = CameDomoticServerError.create_ack_error(3)
    assert isinstance(auth_error_3, CameDomoticAuthError)
    assert str(auth_error_3) == "ACK error 3: Too many sessions during login."

    # Test server error codes (4-11) return CameDomoticServerError
    server_error_4 = CameDomoticServerError.create_ack_error(4)
    assert isinstance(server_error_4, CameDomoticServerError)
    assert not isinstance(server_error_4, CameDomoticAuthError)
    assert str(server_error_4) == "ACK error 4: Error occurred in JSON Syntax."

    server_error_11 = CameDomoticServerError.create_ack_error(11)
    assert isinstance(server_error_11, CameDomoticServerError)
    assert not isinstance(server_error_11, CameDomoticAuthError)
    assert str(server_error_11) == "ACK error 11: Wrong application data."

    # Test unknown error code returns CameDomoticServerError
    unknown_error = CameDomoticServerError.create_ack_error(99)
    assert isinstance(unknown_error, CameDomoticServerError)
    assert not isinstance(unknown_error, CameDomoticAuthError)
    assert str(unknown_error) == "ACK error 99: Unknown error code: 99"


def test_create_ack_error_all_known_codes():
    """Test create_ack_error with all known ACK error codes."""
    from aiocamedomotic.errors import CameDomoticServerError, CameDomoticAuthError

    # All known ACK error codes and their expected exception types
    test_cases = [
        (1, CameDomoticAuthError, "Invalid user."),
        (3, CameDomoticAuthError, "Too many sessions during login."),
        (4, CameDomoticServerError, "Error occurred in JSON Syntax."),
        (5, CameDomoticServerError, "No session layer command tag."),
        (6, CameDomoticServerError, "Unrecognized session layer command."),
        (7, CameDomoticServerError, "No client ID in request."),
        (8, CameDomoticServerError, "Wrong client ID in request."),
        (9, CameDomoticServerError, "Wrong application command."),
        (
            10,
            CameDomoticServerError,
            "No reply to application command, maybe service down.",
        ),
        (11, CameDomoticServerError, "Wrong application data."),
    ]

    for ack_code, expected_type, expected_message in test_cases:
        error = CameDomoticServerError.create_ack_error(ack_code)
        assert isinstance(error, expected_type)
        assert str(error) == f"ACK error {ack_code}: {expected_message}"
