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

"""Shared fixtures for aiocamedomotic tests."""

import configparser
import time
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch

import aiohttp
import pytest

from aiocamedomotic import Auth, CameDomoticAPI

# region Auth fixtures


@pytest.fixture
async def auth_instance_not_logged_in() -> AsyncGenerator[Auth, None]:
    with patch("aiocamedomotic.Auth.async_validate_host", return_value=True):
        async with aiohttp.ClientSession() as session:
            async with await Auth.async_create(
                session, "192.168.x.x", "username", "password"
            ) as auth:
                yield auth
                await auth.async_dispose()


@pytest.fixture
async def auth_instance() -> AsyncGenerator[Auth, None]:
    with patch("aiocamedomotic.Auth.async_validate_host", return_value=True):
        async with aiohttp.ClientSession() as session:
            async with await Auth.async_create(
                session, "192.168.x.x", "username", "password"
            ) as auth:
                auth.client_id = "test_client_id"
                auth.keep_alive_timeout_sec = 900  # 15min
                auth.session_expiration_timestamp = time.monotonic() + 3600  # 1h
                yield auth


# endregion

# region Real server fixtures


@pytest.fixture(scope="session")
def real_server_config():
    """Loads real server configuration from test_config.ini."""
    config_path = Path(__file__).parent / "test_config.ini"
    if not config_path.is_file():
        pytest.skip(
            "Real server configuration file (test_config.ini) not found. Skipping real server tests."
        )
        return None

    config = configparser.ConfigParser()
    config.read(config_path)

    if "came_server" not in config:
        pytest.skip(
            "Missing [came_server] section in test_config.ini. Skipping real server tests."
        )
        return None

    required_keys = ["host", "username", "password"]
    if not all(key in config["came_server"] for key in required_keys):
        pytest.skip(
            f"Missing one or more required keys ({', '.join(required_keys)}) in [came_server] section. Skipping real server tests."
        )
        return None

    return config


@pytest.fixture
async def api_instance_real(real_server_config) -> AsyncGenerator[CameDomoticAPI, None]:
    """
    Create an API instance for testing with a real CAME Domotic server
    using settings from test_config.ini.

    Returns:
        AsyncGenerator[CameDomoticAPI, None]: The API instance for testing.
    """
    if real_server_config is None:
        pytest.skip("Real server configuration not available.")
        yield None  # Make it a generator
        return

    host = real_server_config["came_server"]["host"]
    username = real_server_config["came_server"]["username"]
    password = real_server_config["came_server"]["password"]

    if not host or not username:  # Password could technically be empty for some setups
        pytest.skip(
            "Host or username not configured in test_config.ini for real server tests."
        )
        yield None
        return

    async with await CameDomoticAPI.async_create(host, username, password) as api:
        yield api


# endregion

# region Model fixtures


@pytest.fixture
def light_data_on_off():
    return {
        "act_id": 1,
        "floor_ind": 2,
        "name": "Test Light",
        "room_ind": 3,
        "status": 1,
        "type": "STEP_STEP",
    }


@pytest.fixture
def light_data_dimmable():
    return {
        "act_id": 1,
        "floor_ind": 2,
        "name": "Test Light",
        "room_ind": 3,
        "status": 1,
        "type": "DIMMER",
        "perc": 80,
    }


@pytest.fixture
def opening_data_shutter_stopped():
    """Mock data for a stopped shutter opening."""
    return {
        "open_act_id": 10,
        "close_act_id": 11,
        "floor_ind": 1,
        "name": "Living Room Shutter",
        "room_ind": 2,
        "status": 0,  # Corresponds to OpeningStatus.STOPPED
        "type": 0,  # Corresponds to OpeningType.SHUTTER
        "partial": [],
    }


@pytest.fixture
def opening_data_awning_opening():
    """Mock data for an opening awning."""
    return {
        "open_act_id": 20,
        "close_act_id": 21,
        "floor_ind": 1,
        "name": "Patio Shutter",
        "room_ind": 3,
        "status": 1,  # Corresponds to OpeningStatus.OPENING
        "type": 0,  # OpeningType.SHUTTER
        "partial": [],
    }


@pytest.fixture
def scenario_data_off():
    """Mock data for an inactive scenario."""
    return {
        "icon_id": 14,
        "id": 0,
        "name": "Test Scenario",
        "scenario_status": 0,
        "status": 0,
        "user-defined": 0,
    }


@pytest.fixture
def scenario_data_on():
    """Mock data for an active scenario."""
    return {
        "icon_id": 5,
        "id": 7,
        "name": "Evening Lights",
        "scenario_status": 1,
        "status": 0,
        "user-defined": 1,
    }


# endregion
