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

import time
from typing import AsyncGenerator
from unittest.mock import patch
import aiohttp
import pytest

from aiocamedomotic import Auth, CameDomoticAPI


@pytest.fixture
@patch("aiocamedomotic.Auth.async_validate_host", return_value=True)
async def auth_instance_not_logged_in(
    mock_async_validate_host,  # pylint: disable=unused-argument
) -> AsyncGenerator[Auth, None]:
    async with aiohttp.ClientSession() as session:
        async with await Auth.async_create(
            session, "192.168.x.x", "username", "password"
        ) as auth:
            return auth


@pytest.fixture
@patch("aiocamedomotic.Auth.async_validate_host", return_value=True)
async def auth_instance(
    mock_async_validate_host,  # pylint: disable=unused-argument
) -> AsyncGenerator[Auth, None]:
    async with aiohttp.ClientSession() as session:
        async with await Auth.async_create(
            session, "192.168.x.x", "username", "password"
        ) as auth:
            auth.client_id = "test_client_id"
            auth.keep_alive_timeout_sec = 900  # 15min
            auth.session_expiration_timestamp = time.monotonic() + (60 * 60)  # 1h
            return auth


@pytest.fixture
@patch("aiocamedomotic.Auth.async_validate_host", return_value=True)
async def api_instance(
    mock_async_validate_host,  # pylint: disable=unused-argument
) -> AsyncGenerator[CameDomoticAPI, None]:
    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password"
    ) as api:
        api.auth.client_id = "my_client_id"
        api.auth.keep_alive_timeout_sec = 900  # 15min
        api.auth.session_expiration_timestamp = time.monotonic() + (60 * 60)  # 1h
        return api


@pytest.fixture
async def api_instance_real() -> AsyncGenerator[CameDomoticAPI, None]:
    async with await CameDomoticAPI.async_create(
        "192.168.1.3", "admin", "admin"
    ) as api:
        yield api
        await api.auth.async_dispose()
