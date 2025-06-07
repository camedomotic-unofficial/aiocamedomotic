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

"""Tests for aiocamedomotic package initialization."""

import sys
import logging
from unittest.mock import patch, MagicMock
import pytest


def test_get_logger_returns_package_logger():
    """Test that get_logger returns the package logger."""
    from aiocamedomotic import get_logger
    from aiocamedomotic.utils import LOGGER
    
    result = get_logger()
    assert result is LOGGER


def test_version_when_package_not_found():
    """Test version handling when package is not installed."""
    # Mock importlib.metadata.version to raise PackageNotFoundError
    with patch('importlib.metadata.version') as mock_version:
        from importlib.metadata import PackageNotFoundError
        mock_version.side_effect = PackageNotFoundError("Package not found")
        
        # Reload the module to trigger the exception handling
        import importlib
        import aiocamedomotic
        importlib.reload(aiocamedomotic)
        
        # Check that __version__ is set to "unknown"
        assert aiocamedomotic.__version__ == "unknown"


def test_version_when_package_found():
    """Test version handling when package is properly installed."""
    with patch('importlib.metadata.version') as mock_version:
        mock_version.return_value = "1.2.3"
        
        # Reload the module
        import importlib
        import aiocamedomotic
        importlib.reload(aiocamedomotic)
        
        assert aiocamedomotic.__version__ == "1.2.3"


def test_logger_configuration():
    """Test that the logger is properly configured."""
    from aiocamedomotic.utils import LOGGER
    
    # Check logger has handlers
    assert len(LOGGER.handlers) > 0
    
    # Check log level is set to WARNING
    assert LOGGER.level == logging.WARNING
    
    # Check handler is StreamHandler to stdout
    handler = LOGGER.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream is sys.stdout


def test_logger_formatter():
    """Test that the logger formatter is correctly configured."""
    from aiocamedomotic.utils import LOGGER
    
    handler = LOGGER.handlers[0]
    formatter = handler.formatter
    
    # Check formatter format string contains required elements
    format_string = formatter._fmt
    assert "%(asctime)s" in format_string
    assert "%(name)s" in format_string
    assert "%(levelname)s" in format_string
    assert "%(message)s" in format_string
    assert "%(module)s" in format_string
    assert "%(lineno)d" in format_string
    assert "%(funcName)s" in format_string