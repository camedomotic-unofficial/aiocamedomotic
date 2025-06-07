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
        CameDomoticServerNotFoundError
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
        CameDomoticServerNotFoundError
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
        CameDomoticServerNotFoundError
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


# Note: format_ack_error method doesn't exist in current implementation
# Removing this test as it was based on incorrect assumption