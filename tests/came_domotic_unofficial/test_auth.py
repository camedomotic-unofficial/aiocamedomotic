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
# flake8: noqa: F811

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

from cryptography.fernet import Fernet

import aiohttp
from aiohttp import ClientSession, ClientTimeout
import pytest
import freezegun

from came_domotic_unofficial.auth import Auth
from came_domotic_unofficial.errors import (
    CameDomoticServerError,
    CameDomoticAuthError,
    CameDomoticServerNotFoundError,
)
from tests.came_domotic_unofficial.const import (
    auth_instance,  # noqa: F401
    auth_instance_not_logged_in,  # noqa: F401
)


@freezegun.freeze_time(
    "2022-01-01 12:00:00"
)  # To ensure that the session expiration timestamp is in the past
async def test_init():
    session = ClientSession()
    auth = Auth(session, "192.168.x.x", "user", "password")
    assert auth.websession == session
    assert auth.host == "192.168.x.x"
    assert auth.cipher_suite.decrypt(auth.username).decode() == "user"
    assert auth.cipher_suite.decrypt(auth.password).decode() == "password"
    assert auth.session_expiration_timestamp < time.monotonic()
    assert auth.client_id == ""
    assert auth.keep_alive_timeout_sec == 0
    assert auth.cseq == 0
    assert auth.close_websession_on_disposal is True
    assert isinstance(auth._lock, asyncio.Lock)  # pylint: disable=protected-access
    assert isinstance(auth.cipher_suite, Fernet)


@freezegun.freeze_time("2022-01-01 12:00:00")
@patch.object(Auth, "async_validate_host", return_value=True)
async def test_async_create(mock_validate_host):
    session = ClientSession()
    auth_create = await Auth.async_create(session, "192.168.x.x", "user", "password")
    auth_init = Auth(session, "192.168.x.x", "user", "password")
    assert auth_init.websession == auth_create.websession
    assert auth_init.host == auth_create.host
    assert (
        auth_init.cipher_suite.decrypt(auth_init.username).decode()
        == auth_create.cipher_suite.decrypt(auth_create.username).decode()
    )
    assert (
        auth_init.cipher_suite.decrypt(auth_init.password).decode()
        == auth_create.cipher_suite.decrypt(auth_create.password).decode()
    )
    assert (
        auth_init.session_expiration_timestamp
        == auth_create.session_expiration_timestamp
    )
    assert auth_init.client_id == auth_create.client_id
    assert auth_init.keep_alive_timeout_sec == auth_create.keep_alive_timeout_sec
    assert auth_init.cseq == auth_create.cseq
    assert (
        auth_init.close_websession_on_disposal
        == auth_create.close_websession_on_disposal
    )
    assert isinstance(
        auth_create._lock, asyncio.Lock  # pylint: disable=protected-access
    )
    assert isinstance(auth_create.cipher_suite, Fernet)

    mock_validate_host.assert_called_once()


@patch.object(Auth, "async_validate_host", side_effect=CameDomoticServerNotFoundError)
async def test_create_invalid_host(mock_validate_host):
    session = ClientSession()
    with pytest.raises(CameDomoticServerNotFoundError):
        await Auth.async_create(session, "192.168.x.x", "user", "password")
    mock_validate_host.assert_called_once()


async def test_get_endpoint_url(auth_instance):
    assert auth_instance.get_endpoint_url() == "http://192.168.x.x/domo/"


@patch.object(Auth, "validate_session", return_value=True)
@patch.object(Auth, "async_login", new_callable=AsyncMock)
async def test_async_get_valid_client_id_valid_session(
    mock_login, mock_validate_session, auth_instance
):
    auth_instance.client_id = "test_client_id"
    client_id = await auth_instance.async_get_valid_client_id()
    assert client_id == "test_client_id"
    mock_validate_session.assert_called_once()
    mock_login.assert_not_called()


@patch.object(Auth, "validate_session", return_value=False)
@patch.object(Auth, "async_login", new_callable=AsyncMock)
async def test_async_get_valid_client_id_invalid_session_successful_login(
    mock_login, mock_validate_session, auth_instance
):
    auth_instance.client_id = "test_client_id"
    client_id = await auth_instance.async_get_valid_client_id()
    assert client_id == "test_client_id"
    mock_validate_session.assert_called_once()
    mock_login.assert_called_once()


@patch.object(Auth, "validate_session", return_value=False)
@patch.object(
    Auth, "async_login", new_callable=AsyncMock, side_effect=CameDomoticAuthError
)
async def test_async_get_valid_client_id_invalid_session_unsuccessful_login(
    mock_login, mock_validate_session, auth_instance
):
    with pytest.raises(CameDomoticAuthError):
        await auth_instance.async_get_valid_client_id()
    mock_validate_session.assert_called_once()
    mock_login.assert_called_once()


@patch.object(ClientSession, "post", new_callable=AsyncMock)
@freezegun.freeze_time("2020-01-01")
async def test_async_send_command_success(mock_post, auth_instance):
    # Setup mock response with async json method returning the desired dictionary
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"sl_data_ack_reason": 0}
    mock_post.return_value = mock_response

    auth_instance.keep_alive_timeout_sec = 900

    payload = {"command": "test_command"}
    response = await auth_instance.async_send_command(payload)

    assert response == mock_response
    assert auth_instance.cseq == 1
    assert (
        auth_instance.session_expiration_timestamp
        == time.monotonic() + auth_instance.keep_alive_timeout_sec - 30
    )

    mock_post.assert_called_once_with(
        "http://192.168.x.x/domo/",
        data={"command": json.dumps(payload)},
        headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
        timeout=10,
    )


@patch.object(ClientSession, "post", new_callable=AsyncMock)
@freezegun.freeze_time("2020-01-01")
async def test_async_send_command_bad_ack(mock_post, auth_instance):
    # Setup mock response with async json method returning the desired dictionary
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"sl_data_ack_reason": 1}
    mock_post.return_value = mock_response

    auth_instance.keep_alive_timeout_sec = 900

    payload = {"command": "test_command"}
    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_send_command(payload)

    assert auth_instance.cseq == 1
    assert (
        auth_instance.session_expiration_timestamp
        == time.monotonic() + auth_instance.keep_alive_timeout_sec - 30
    )
    mock_post.assert_called_once_with(
        "http://192.168.x.x/domo/",
        data={"command": json.dumps(payload)},
        headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
        timeout=10,
    )


@patch.object(ClientSession, "post", new_callable=AsyncMock)
async def test_async_send_command_failure(mock_post, auth_instance):
    mock_post.side_effect = Exception()

    payload = {"command": "test_command"}
    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_send_command(payload)

    mock_post.assert_called_once_with(
        "http://192.168.x.x/domo/",
        data={"command": json.dumps(payload)},
        headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
        timeout=10,
    )


@patch.object(ClientSession, "post", new_callable=AsyncMock)
async def test_async_send_command_timeout(mock_post, auth_instance):
    mock_post.side_effect = ClientTimeout()

    payload = {"command": "test_command"}
    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_send_command(payload)

    mock_post.assert_called_once_with(
        "http://192.168.x.x/domo/",
        data={"command": json.dumps(payload)},
        headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
        timeout=10,
    )


@patch.object(ClientSession, "post", new_callable=AsyncMock)
@patch.object(
    Auth,
    "async_raise_for_status_and_ack",
    new_callable=AsyncMock,
    side_effect=CameDomoticServerError,
)
async def test_async_send_command_non_2xx_status(
    mock_raise_for_status_and_ack, mock_post, auth_instance: Auth
):
    mock_response = Mock()
    mock_response.status = 500
    mock_post.return_value = mock_response

    payload = {"command": "test_command"}

    previous_session_expiration_timestamp = auth_instance.session_expiration_timestamp

    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_send_command(payload)

    mock_post.assert_called_once_with(
        "http://192.168.x.x/domo/",
        data={"command": json.dumps(payload)},
        headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
        timeout=10,
    )
    mock_raise_for_status_and_ack.assert_called_once()
    assert auth_instance.cseq == 0
    assert (
        auth_instance.session_expiration_timestamp
        == previous_session_expiration_timestamp
    )


async def test_validate_host_success(auth_instance):
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Setup mock response with status code 200 for aiohttp.ClientSession.get method
        mock_response = Mock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        await auth_instance.async_validate_host()
        mock_get.assert_called_once_with(auth_instance.get_endpoint_url(), timeout=10)


async def test_validate_host_failure_status_code(auth_instance):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(CameDomoticServerNotFoundError):
            await auth_instance.async_validate_host()

        mock_get.assert_called_once_with(auth_instance.get_endpoint_url(), timeout=10)


async def test_validate_host_failure_exception(auth_instance):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = aiohttp.ClientError()

        with pytest.raises(CameDomoticServerNotFoundError):
            await auth_instance.async_validate_host()

        mock_get.assert_called_once_with(auth_instance.get_endpoint_url(), timeout=10)


@freezegun.freeze_time("2020-01-01")
async def test_async_login_success(auth_instance_not_logged_in: Auth):
    with patch.object(
        Auth, "async_send_command", new_callable=AsyncMock
    ) as mock_send_command, patch.object(
        Auth, "validate_session", return_value=False
    ) as mock_validate_session:
        # Setup mock response with async json method returning the desired dictionary
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "sl_data_ack_reason": 0,
            "sl_client_id": "test_client_id",
            "sl_keep_alive_timeout_sec": 900,
        }
        mock_send_command.return_value = mock_response

        await auth_instance_not_logged_in.async_login()

        mock_validate_session.assert_called_once()
        mock_send_command.assert_called_once_with(
            {
                "sl_cmd": "sl_registration_req",
                "sl_login": auth_instance_not_logged_in.cipher_suite.decrypt(
                    auth_instance_not_logged_in.username
                ).decode(),
                "sl_pwd": auth_instance_not_logged_in.cipher_suite.decrypt(
                    auth_instance_not_logged_in.password
                ).decode(),
            },
            skip_ack_check=True,
        )
        assert auth_instance_not_logged_in.client_id == "test_client_id"
        assert auth_instance_not_logged_in.keep_alive_timeout_sec == 900
        assert (
            auth_instance_not_logged_in.session_expiration_timestamp
            == time.monotonic() + 900 - 30
        )


@freezegun.freeze_time("2020-01-01")
async def test_async_login_already_authenticated(auth_instance: Auth):
    with patch.object(
        Auth, "validate_session", return_value=True
    ) as mock_validate_session, patch.object(
        Auth, "async_send_command", new_callable=AsyncMock
    ) as mock_send_command, patch.object(
        Auth, "async_keep_alive", new_callable=AsyncMock
    ) as mock_keep_alive:
        await auth_instance.async_login()
        mock_validate_session.assert_called_once()
        mock_keep_alive.assert_called_once()
        mock_send_command.assert_not_called()


async def test_async_login_send_command_failure(
    auth_instance_not_logged_in: Auth,
):
    with patch.object(
        Auth,
        "async_send_command",
        new_callable=AsyncMock,
    ) as mock_send_command:
        mock_send_command.side_effect = Exception()

        with pytest.raises(CameDomoticAuthError):
            await auth_instance_not_logged_in.async_login()


async def test_async_login_bad_ack(
    auth_instance_not_logged_in: Auth,
):
    with patch.object(
        ClientSession, "post", new_callable=AsyncMock
    ) as mock_send_command, patch.object(
        Auth, "validate_session", return_value=None
    ) as mock_validate_session:
        # Setup mock response with async json method returning the desired dictionary
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "sl_data_ack_reason": 1,
            "sl_client_id": "bad_client_id",
            "sl_keep_alive_timeout_sec": 900,
        }
        mock_send_command.return_value = mock_response

        mock_validate_session.assert_not_called()
        with pytest.raises(CameDomoticAuthError):
            await auth_instance_not_logged_in.async_login()


async def test_async_login_json_decode_error(auth_instance_not_logged_in: Auth):
    with patch.object(
        ClientSession, "post", new_callable=AsyncMock
    ) as mock_send_command:
        # Setup mock response with async json method returning the desired dictionary
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Error", "", 0)
        mock_send_command.return_value = mock_response

        with pytest.raises(CameDomoticAuthError):
            await auth_instance_not_logged_in.async_login()


@patch.object(Auth, "validate_session", return_value=True)
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_async_keep_alive_valid_session_successful_keep_alive(
    mock_send_command, mock_validate_session, auth_instance
):
    await auth_instance.async_keep_alive()
    mock_validate_session.assert_called_once()
    mock_send_command.assert_called_once_with(
        {"sl_client_id": auth_instance.client_id, "sl_cmd": "sl_keep_alive_req"}
    )


@patch.object(Auth, "validate_session", return_value=True)
@patch.object(
    Auth,
    "async_send_command",
    new_callable=AsyncMock,
    side_effect=CameDomoticServerError,
)
async def test_async_keep_alive_valid_session_unsuccessful_keep_alive(
    mock_send_command, mock_validate_session, auth_instance
):
    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_keep_alive()
    mock_validate_session.assert_called_once()
    mock_send_command.assert_called_once_with(
        {"sl_client_id": auth_instance.client_id, "sl_cmd": "sl_keep_alive_req"}
    )


@patch.object(Auth, "validate_session", return_value=False)
@patch.object(Auth, "async_login", new_callable=AsyncMock)
async def test_async_keep_alive_invalid_session_successful_login(
    mock_login, mock_validate_session, auth_instance
):
    await auth_instance.async_keep_alive()
    mock_validate_session.assert_called_once()
    mock_login.assert_called_once()


@patch.object(Auth, "validate_session", return_value=False)
@patch.object(
    Auth, "async_login", new_callable=AsyncMock, side_effect=CameDomoticAuthError
)
async def test_async_keep_alive_invalid_session_unsuccessful_login(
    mock_login, mock_validate_session, auth_instance
):
    with pytest.raises(CameDomoticAuthError):
        await auth_instance.async_keep_alive()
    mock_validate_session.assert_called_once()
    mock_login.assert_called_once()


@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_async_logout_valid_session(mock_send_command, auth_instance: Auth):
    valid_client_id = auth_instance.client_id

    await auth_instance.async_logout()
    mock_send_command.assert_called_once_with(
        {
            "sl_client_id": valid_client_id,
            "sl_cmd": "sl_logout_req",
        }
    )
    assert auth_instance.client_id == ""
    assert auth_instance.session_expiration_timestamp <= time.monotonic()


@patch.object(Auth, "validate_session", return_value=False)
@patch.object(Auth, "async_send_command", new_callable=AsyncMock)
async def test_async_logout_invalid_session(
    mock_send_command, mock_validate_session, auth_instance
):
    await auth_instance.async_logout()
    mock_validate_session.assert_called_once()
    mock_send_command.assert_not_called()


@patch.object(Auth, "validate_session", return_value=True)
@patch.object(
    Auth,
    "async_send_command",
    new_callable=AsyncMock,
    side_effect=CameDomoticServerError,
)
async def test_async_logout_send_command_failure(
    mock_send_command, mock_validate_session, auth_instance
):
    with pytest.raises(CameDomoticServerError):
        await auth_instance.async_logout()
    mock_validate_session.assert_called_once()
    mock_send_command.assert_called_once()


@patch.object(ClientSession, "close", new_callable=AsyncMock)
@patch.object(Auth, "validate_session", return_value=True)
@patch.object(Auth, "async_logout", new_callable=AsyncMock)
async def test_async_dispose_valid_session_successful_logout(
    mock_logout, mock_validate_session, mock_close, auth_instance
):
    await auth_instance.async_dispose()
    mock_validate_session.assert_called_once()
    mock_logout.assert_called_once()
    mock_close.assert_called_once()


@patch.object(ClientSession, "close", new_callable=AsyncMock)
@patch.object(Auth, "validate_session", return_value=True)
@patch.object(
    Auth, "async_logout", new_callable=AsyncMock, side_effect=CameDomoticServerError
)
async def test_async_dispose_valid_session_unsuccessful_logout(
    mock_logout, mock_validate_session, mock_close, auth_instance
):
    await auth_instance.async_dispose()
    mock_validate_session.assert_called_once()
    mock_logout.assert_called_once()
    mock_close.assert_called_once()


@patch.object(ClientSession, "close", new_callable=AsyncMock)
@patch.object(Auth, "validate_session", return_value=False)
@patch.object(Auth, "async_logout", new_callable=AsyncMock)
async def test_async_dispose_invalid_session(
    mock_logout, mock_validate_session, mock_close, auth_instance
):
    await auth_instance.async_dispose()
    mock_validate_session.assert_called_once()
    mock_logout.assert_not_called()
    mock_close.assert_called_once()


@patch.object(ClientSession, "close", new_callable=AsyncMock)
async def test_async_dispose_no_websession_close(mock_close, auth_instance):
    auth_instance.close_websession_on_disposal = False
    await auth_instance.async_dispose()
    mock_close.assert_not_called()


@freezegun.freeze_time("2022-01-01 12:00:00")
def test_validate_session_valid(auth_instance):
    # Set the session expiration timestamp to a future date
    auth_instance.session_expiration_timestamp = time.monotonic() + 900
    auth_instance.client_id = "test_client_id"
    assert auth_instance.validate_session() is True


@freezegun.freeze_time("2022-01-01 12:00:00")
def test_validate_session_expired(auth_instance):
    # Set the session expiration timestamp to a past date
    auth_instance.session_expiration_timestamp = time.monotonic() - 3600
    assert auth_instance.validate_session() is False


async def test_concurrent_logins(auth_instance):
    with patch.object(
        Auth, "async_send_command", new_callable=AsyncMock
    ) as mock_send_command:  # pylint: disable=unused-variable  # noqa: F841
        # Mock validate_session to initially return False, indicating session is invalid
        auth_instance.validate_session = Mock(side_effect=[False] * 10)

        # Mock the async_login so it actually changes the validate_session to return
        # True afterwards
        async def login_side_effect():
            auth_instance.validate_session = Mock(return_value=True)

        auth_instance.async_login = AsyncMock(side_effect=login_side_effect)

        # Simulate concurrent login attempts
        await asyncio.gather(*(auth_instance.async_keep_alive() for _ in range(10)))

        # Check that login was initiated and is now valid
        assert (
            auth_instance.validate_session()
        ), "Session should be valid after concurrent logins"
        assert (
            auth_instance.async_login.call_count == 1
        ), "Login should be called exactly once"


@pytest.mark.asyncio
async def test_no_deadlocks_under_load(auth_instance):
    auth_instance.validate_session = AsyncMock(return_value=True)
    auth_instance.async_login = AsyncMock()
    auth_instance.async_send_command = AsyncMock()

    # Semaphore to simulate load and a small delay in each operation
    async with asyncio.Semaphore(10):  # Limit concurrency to 10
        tasks = [
            asyncio.create_task(auth_instance.async_keep_alive()) for _ in range(100)
        ]  # 100 concurrent requests
        await asyncio.gather(*tasks)  # Wait for all tasks to complete

    # Check if all tasks completed successfully without deadlocking
    assert all(task.done() for task in tasks), "All tasks should complete successfully"
