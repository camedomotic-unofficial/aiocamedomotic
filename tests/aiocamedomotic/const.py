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

import os
import time
from typing import AsyncGenerator
from unittest.mock import patch
import aiohttp
import pytest

from aiocamedomotic import Auth, CameDomoticAPI


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


@pytest.fixture
async def api_instance() -> AsyncGenerator[CameDomoticAPI, None]:
    with patch("aiocamedomotic.Auth.async_validate_host", return_value=True):
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:
            api.auth.client_id = "my_client_id"
            api.auth.keep_alive_timeout_sec = 900  # 15min
            api.auth.session_expiration_timestamp = time.monotonic() + (60 * 60)  # 1h
            yield api


@pytest.fixture
async def api_instance_real() -> AsyncGenerator[CameDomoticAPI, None]:
    """
    Create an API instance for testing with a real CAME Domotic server.

    This fixture configures the connection using environment variables:
    - CAMEDOMOTIC_HOST: The IP address of the server
    - CAMEDOMOTIC_USERNAME: The username for authentication
    - CAMEDOMOTIC_PASSWORD: The password for authentication

    For secure testing, it's recommended to set these environment variables rather
    than relying on the defaults.

    Returns:
        AsyncGenerator[CameDomoticAPI, None]: The API instance for testing.
    """
    host = os.environ.get("CAMEDOMOTIC_HOST")
    username = os.environ.get("CAMEDOMOTIC_USERNAME")
    password = os.environ.get("CAMEDOMOTIC_PASSWORD")

    async with await CameDomoticAPI.async_create(host, username, password) as api:
        yield api
