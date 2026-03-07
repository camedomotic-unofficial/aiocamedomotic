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

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import freezegun
import pytest
from aiohttp import ClientSession, ClientTimeout
from cryptography.fernet import Fernet

from aiocamedomotic import Auth
from aiocamedomotic.errors import (
    CameDomoticAuthError,
    CameDomoticServerError,
    CameDomoticServerNotFoundError,
)


class TestAuthInit:
    """Tests for Auth constructor, async_create, and host validation."""

    @pytest.mark.parametrize(
        "host",
        [
            "192.168.1.100",
            "192.168.1.100:8080",
            "10.0.0.1",
            "my-server",
            "came.local",
            "came.example.com",
            "came.local:443",
            "[::1]",
            "[2001:db8::1]",
            "[::1]:8080",
            "[fe80::1%25eth0]",
        ],
    )
    def test_valid_hosts(self, host):
        session = Mock()
        auth = Auth(session, host, "user", "password")
        assert auth.host == host

    @pytest.mark.parametrize(
        "host",
        [
            "",
            "example.com/../../admin",
            "example.com?q=1",
            "example.com#frag",
            "user:pass@example.com",
            "@evil.com",
            "example.com/@evil",
        ],
    )
    def test_invalid_hosts(self, host):
        session = Mock()
        with pytest.raises(ValueError, match="Invalid host"):
            Auth(session, host, "user", "password")

    @freezegun.freeze_time(
        "2022-01-01 12:00:00"
    )  # To ensure that the session expiration timestamp is in the past
    async def test_init(self):
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
    async def test_async_create(self, mock_validate_host):
        session = ClientSession()
        auth_create = await Auth.async_create(
            session, "192.168.x.x", "user", "password"
        )
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
            auth_create._lock,
            asyncio.Lock,  # pylint: disable=protected-access
        )
        assert isinstance(auth_create.cipher_suite, Fernet)

        mock_validate_host.assert_called_once()

    @patch.object(
        Auth, "async_validate_host", side_effect=CameDomoticServerNotFoundError
    )
    async def test_create_invalid_host(self, mock_validate_host):
        session = ClientSession()
        with pytest.raises(CameDomoticServerNotFoundError):
            await Auth.async_create(session, "192.168.x.x", "user", "password")
        mock_validate_host.assert_called_once()

    async def test_get_endpoint_url(self, auth_instance):
        assert auth_instance.get_endpoint_url() == "http://192.168.x.x/domo/"


class TestAuthSession:
    """Tests for session validation and client ID retrieval."""

    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(Auth, "async_login", new_callable=AsyncMock)
    async def test_get_valid_client_id_valid_session(
        self, mock_login, mock_is_session_valid, auth_instance
    ):
        auth_instance.client_id = "test_client_id"
        client_id = await auth_instance.async_get_valid_client_id()
        assert client_id == "test_client_id"
        mock_is_session_valid.assert_called_once()
        mock_login.assert_not_called()

    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(Auth, "_async_perform_login", new_callable=AsyncMock)
    async def test_get_valid_client_id_invalid_session_successful_login(
        self, mock_login, mock_is_session_valid, auth_instance
    ):
        auth_instance.client_id = "test_client_id"
        client_id = await auth_instance.async_get_valid_client_id()
        assert client_id == "test_client_id"
        mock_is_session_valid.assert_called_once()
        mock_login.assert_called_once()

    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(
        Auth,
        "_async_perform_login",
        new_callable=AsyncMock,
        side_effect=CameDomoticAuthError,
    )
    async def test_get_valid_client_id_invalid_session_unsuccessful_login(
        self, mock_login, mock_is_session_valid, auth_instance
    ):
        with pytest.raises(CameDomoticAuthError):
            await auth_instance.async_get_valid_client_id()
        mock_is_session_valid.assert_called_once()
        mock_login.assert_called_once()

    @freezegun.freeze_time("2022-01-01 12:00:00")
    def test_session_valid(self, auth_instance):
        auth_instance.session_expiration_timestamp = time.monotonic() + 900
        auth_instance.client_id = "test_client_id"
        assert auth_instance.is_session_valid() is True

    @freezegun.freeze_time("2022-01-01 12:00:00")
    def test_session_expired(self, auth_instance):
        auth_instance.session_expiration_timestamp = time.monotonic() - 3600
        assert auth_instance.is_session_valid() is False


class TestAuthSendCommand:
    """Tests for async_send_command method."""

    @freezegun.freeze_time("2020-01-01")
    async def test_success(self, auth_instance):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"sl_data_ack_reason": 0}

        auth_instance.keep_alive_timeout_sec = 900

        payload = {"command": "test_command"}

        with patch.object(
            auth_instance.websession, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with patch.object(
                auth_instance, "async_get_valid_client_id", new_callable=AsyncMock
            ) as mock_get_client_id:
                mock_get_client_id.return_value = "test_client_id"

                response = await auth_instance.async_send_command(payload)

                assert response == mock_response.json.return_value
                assert auth_instance.cseq == 1
                assert (
                    auth_instance.session_expiration_timestamp
                    == time.monotonic() + auth_instance.keep_alive_timeout_sec - 30
                )

                expected_appl_msg = {
                    **payload,
                    "cseq": 1,
                    "client": "test_client_id",
                }
                expected_request_payload = {
                    "sl_appl_msg": expected_appl_msg,
                    "sl_client_id": "test_client_id",
                    "sl_cmd": "sl_data_req",
                    "sl_appl_msg_type": "domo",
                }

                mock_post.assert_called_once_with(
                    "http://192.168.x.x/domo/",
                    data={"command": json.dumps(expected_request_payload)},
                    headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    @freezegun.freeze_time("2020-01-01")
    async def test_bad_ack(self, auth_instance):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"sl_data_ack_reason": 1}

        auth_instance.keep_alive_timeout_sec = 900

        payload = {"command": "test_command"}
        previous_session_expiration_timestamp = (
            auth_instance.session_expiration_timestamp
        )

        with patch.object(
            auth_instance.websession, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with patch.object(
                auth_instance, "async_get_valid_client_id", new_callable=AsyncMock
            ) as mock_get_client_id:
                mock_get_client_id.return_value = "test_client_id"

                with pytest.raises(
                    CameDomoticAuthError, match=r"ACK error 1: Invalid user\."
                ):
                    await auth_instance.async_send_command(payload)

                # Session state should NOT be refreshed on ACK error
                assert auth_instance.cseq == 0
                assert (
                    auth_instance.session_expiration_timestamp
                    == previous_session_expiration_timestamp
                )

                expected_appl_msg = {
                    **payload,
                    "cseq": 1,
                    "client": "test_client_id",
                }
                expected_request_payload = {
                    "sl_appl_msg": expected_appl_msg,
                    "sl_client_id": "test_client_id",
                    "sl_cmd": "sl_data_req",
                    "sl_appl_msg_type": "domo",
                }

                mock_post.assert_called_once_with(
                    "http://192.168.x.x/domo/",
                    data={"command": json.dumps(expected_request_payload)},
                    headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_failure(self, auth_instance):
        payload = {"command": "test_command"}

        with patch.object(
            auth_instance.websession, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = Exception()

            with patch.object(
                auth_instance, "async_get_valid_client_id", new_callable=AsyncMock
            ) as mock_get_client_id:
                mock_get_client_id.return_value = "test_client_id"

                with pytest.raises(CameDomoticServerError):
                    await auth_instance.async_send_command(payload)

                expected_appl_msg = {
                    **payload,
                    "cseq": 1,
                    "client": "test_client_id",
                }
                expected_request_payload = {
                    "sl_appl_msg": expected_appl_msg,
                    "sl_client_id": "test_client_id",
                    "sl_cmd": "sl_data_req",
                    "sl_appl_msg_type": "domo",
                }

                mock_post.assert_called_once_with(
                    "http://192.168.x.x/domo/",
                    data={"command": json.dumps(expected_request_payload)},
                    headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_timeout(self, auth_instance):
        payload = {"command": "test_command"}

        with patch.object(
            auth_instance.websession, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = ClientTimeout()

            with patch.object(
                auth_instance, "async_get_valid_client_id", new_callable=AsyncMock
            ) as mock_get_client_id:
                mock_get_client_id.return_value = "test_client_id"

                with pytest.raises(CameDomoticServerError):
                    await auth_instance.async_send_command(payload)

                expected_appl_msg = {
                    **payload,
                    "cseq": 1,
                    "client": "test_client_id",
                }
                expected_request_payload = {
                    "sl_appl_msg": expected_appl_msg,
                    "sl_client_id": "test_client_id",
                    "sl_cmd": "sl_data_req",
                    "sl_appl_msg_type": "domo",
                }

                mock_post.assert_called_once_with(
                    "http://192.168.x.x/domo/",
                    data={"command": json.dumps(expected_request_payload)},
                    headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    @patch.object(
        Auth,
        "async_raise_for_status_and_ack",
        new_callable=AsyncMock,
        side_effect=CameDomoticServerError,
    )
    @patch.object(Auth, "async_get_valid_client_id", new_callable=AsyncMock)
    async def test_non_2xx_status(
        self, mock_get_client_id, mock_raise_for_status_and_ack, auth_instance: Auth
    ):
        mock_response = Mock()
        mock_response.status = 500
        mock_get_client_id.return_value = "my_client_id"
        payload = {"command": "test_command"}

        previous_session_expiration_timestamp = (
            auth_instance.session_expiration_timestamp
        )

        with patch.object(
            auth_instance.websession, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(CameDomoticServerError):
                await auth_instance.async_send_command(payload)

            expected_appl_msg = {
                **payload,
                "cseq": 1,
                "client": "my_client_id",
            }
            full_payload = {
                "sl_appl_msg": expected_appl_msg,
                "sl_client_id": "my_client_id",
                "sl_cmd": "sl_data_req",
                "sl_appl_msg_type": "domo",
            }

            mock_post.assert_called_once_with(
                "http://192.168.x.x/domo/",
                data={"command": json.dumps(full_payload)},
                headers=Auth._DEFAULT_HTTP_HEADERS,  # pylint: disable=protected-access
                timeout=aiohttp.ClientTimeout(total=10),
            )
            mock_raise_for_status_and_ack.assert_called_once()
            assert auth_instance.cseq == 0
            assert (
                auth_instance.session_expiration_timestamp
                == previous_session_expiration_timestamp
            )

    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="test_client_id",
    )
    @patch.object(ClientSession, "post", new_callable=AsyncMock)
    @freezegun.freeze_time("2020-01-01")
    async def test_server_ack_errors(
        self, mock_post, mock_get_client_id, auth_instance
    ):
        """Test that server ACK error codes (4-11) raise CameDomoticServerError."""
        auth_instance.keep_alive_timeout_sec = 900
        payload = {"command": "test_command"}

        server_error_codes = [4, 5, 6, 7, 8, 9, 10, 11]
        error_messages = [
            "Error occurred in JSON Syntax.",
            "No session layer command tag.",
            "Unrecognized session layer command.",
            "No client ID in request.",
            "Wrong client ID in request.",
            "Wrong application command.",
            "No reply to application command, maybe service down.",
            "Wrong application data.",
        ]

        for ack_code, expected_message in zip(
            server_error_codes, error_messages, strict=False
        ):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = {"sl_data_ack_reason": ack_code}
            mock_post.return_value = mock_response

            with pytest.raises(
                CameDomoticServerError,
                match=rf"ACK error {ack_code}: {expected_message.replace('.', r'\.')}",
            ):
                await auth_instance.async_send_command(payload)

    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="test_client_id",
    )
    @patch.object(ClientSession, "post", new_callable=AsyncMock)
    @freezegun.freeze_time("2020-01-01")
    @pytest.mark.parametrize("ack_code", [7, 8])
    async def test_session_invalidated_on_session_ack_errors(
        self, mock_post, mock_get_client_id, auth_instance, ack_code
    ):
        """Test that ACK errors 7/8 invalidate the session for re-login."""
        auth_instance.keep_alive_timeout_sec = 900
        auth_instance.client_id = "test_client_id"
        auth_instance.session_expiration_timestamp = time.monotonic() + 3600
        payload = {"command": "test_command"}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"sl_data_ack_reason": ack_code}
        mock_post.return_value = mock_response

        with pytest.raises(CameDomoticServerError):
            await auth_instance.async_send_command(payload)

        assert auth_instance.client_id == ""
        assert auth_instance.session_expiration_timestamp < time.monotonic()

    @patch.object(
        Auth,
        "async_get_valid_client_id",
        new_callable=AsyncMock,
        return_value="test_client_id",
    )
    @patch.object(ClientSession, "post", new_callable=AsyncMock)
    @freezegun.freeze_time("2020-01-01")
    async def test_auth_ack_errors(self, mock_post, mock_get_client_id, auth_instance):
        """Test that ACK error codes (1, 3) raise CameDomoticAuthError."""
        auth_instance.keep_alive_timeout_sec = 900
        payload = {"command": "test_command"}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"sl_data_ack_reason": 3}
        mock_post.return_value = mock_response

        with pytest.raises(
            CameDomoticAuthError, match=r"ACK error 3: Too many sessions during login\."
        ):
            await auth_instance.async_send_command(payload)

    async def test_raise_for_status_and_ack_http_error(self):
        """Test handling of HTTP errors in async_raise_for_status_and_ack."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.raise_for_status = Mock(
            side_effect=aiohttp.ClientResponseError(
                request_info=Mock(),
                history=[],
                status=500,
                message="Any message",
                headers=Mock(),
            )
        )

        with pytest.raises(CameDomoticServerError):
            await Auth.async_raise_for_status_and_ack(mock_response)

    async def test_raise_for_status_and_ack_json_error(self):
        """Test handling of JSON decode errors in async_raise_for_status_and_ack."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with pytest.raises(CameDomoticServerError):
            await Auth.async_raise_for_status_and_ack(mock_response)


class TestAuthValidateHost:
    """Tests for host validation."""

    async def test_success(self):
        async with aiohttp.ClientSession() as session:
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                async with await Auth.async_create(
                    session, "192.168.x.x", "username", "password"
                ) as auth:
                    auth.client_id = "test_client_id"
                    auth.keep_alive_timeout_sec = 900
                    auth.session_expiration_timestamp = time.monotonic() + 3600

                    previous_calls = mock_get.call_count

                    await auth.async_validate_host()
                    assert mock_get.call_count == previous_calls + 1
                    mock_get.assert_called_with(
                        auth.get_endpoint_url(), timeout=aiohttp.ClientTimeout(total=10)
                    )

    async def test_failure_status_code(self):
        async with aiohttp.ClientSession() as session:
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                async with await Auth.async_create(
                    session, "192.168.x.x", "username", "password"
                ) as auth:
                    auth.client_id = "test_client_id"
                    auth.keep_alive_timeout_sec = 900
                    auth.session_expiration_timestamp = time.monotonic() + 3600

                mock_response.status = 404

                with pytest.raises(CameDomoticServerNotFoundError):
                    await auth.async_validate_host()

                mock_get.assert_called_with(
                    auth.get_endpoint_url(),
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_failure_exception(self):
        async with aiohttp.ClientSession() as session:
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                async with await Auth.async_create(
                    session, "192.168.x.x", "username", "password"
                ) as auth:
                    auth.client_id = "test_client_id"
                    auth.keep_alive_timeout_sec = 900
                    auth.session_expiration_timestamp = time.monotonic() + 3600

                mock_get.side_effect = aiohttp.ClientError()

                with pytest.raises(CameDomoticServerNotFoundError):
                    await auth.async_validate_host()

                mock_get.assert_called_with(
                    auth.get_endpoint_url(),
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_failure_timeout_error(self):
        async with aiohttp.ClientSession() as session:
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                async with await Auth.async_create(
                    session, "192.168.x.x", "username", "password"
                ) as auth:
                    auth.client_id = "test_client_id"
                    auth.keep_alive_timeout_sec = 900
                    auth.session_expiration_timestamp = time.monotonic() + 3600

                mock_get.side_effect = TimeoutError()

                with pytest.raises(CameDomoticServerNotFoundError):
                    await auth.async_validate_host()

                mock_get.assert_called_with(
                    auth.get_endpoint_url(),
                    timeout=aiohttp.ClientTimeout(total=10),
                )


class TestAuthLogin:
    """Tests for async_login method."""

    @freezegun.freeze_time("2020-01-01")
    async def test_success(self, auth_instance_not_logged_in: Auth):
        with (
            patch.object(Auth, "async_send_command") as mock_send_command,
            patch.object(
                Auth, "is_session_valid", return_value=False
            ) as mock_is_session_valid,
        ):
            mock_send_command.return_value = {
                "sl_data_ack_reason": 0,
                "sl_client_id": "test_client_id",
                "sl_keep_alive_timeout_sec": 900,
            }

            await auth_instance_not_logged_in.async_login()

            mock_is_session_valid.assert_called_once()
            mock_send_command.assert_called_once_with(
                {},
                command_type="sl_registration_req",
                additional_payload={
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
    async def test_already_authenticated(self, auth_instance: Auth):
        with (
            patch.object(
                Auth, "is_session_valid", return_value=True
            ) as mock_is_session_valid,
            patch.object(
                Auth, "_async_perform_login", new_callable=AsyncMock
            ) as mock_login,
            patch.object(
                Auth, "_async_perform_keep_alive", new_callable=AsyncMock
            ) as mock_keep_alive,
        ):
            await auth_instance.async_login()
            mock_is_session_valid.assert_called_once()
            mock_keep_alive.assert_called_once()
            mock_login.assert_not_called()

    async def test_send_command_failure(self, auth_instance_not_logged_in: Auth):
        with patch.object(
            Auth,
            "async_send_command",
            new_callable=AsyncMock,
        ) as mock_send_command:
            mock_send_command.side_effect = Exception()

            with pytest.raises(CameDomoticAuthError):
                await auth_instance_not_logged_in.async_login()

    async def test_bad_ack(self, auth_instance_not_logged_in: Auth):
        with (
            patch.object(
                ClientSession, "post", new_callable=AsyncMock
            ) as mock_send_command,
            patch.object(
                Auth, "is_session_valid", return_value=None
            ) as mock_is_session_valid,
        ):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "sl_data_ack_reason": 1,
                "sl_client_id": "bad_client_id",
                "sl_keep_alive_timeout_sec": 900,
            }
            mock_send_command.return_value = mock_response

            mock_is_session_valid.assert_not_called()
            with pytest.raises(
                CameDomoticAuthError, match=r"ACK error 1: Invalid user\."
            ):
                await auth_instance_not_logged_in.async_login()

    async def test_json_decode_error(self, auth_instance_not_logged_in: Auth):
        with patch.object(
            ClientSession, "post", new_callable=AsyncMock
        ) as mock_send_command:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = json.JSONDecodeError("Error", "", 0)
            mock_send_command.return_value = mock_response

            with pytest.raises(CameDomoticAuthError):
                await auth_instance_not_logged_in.async_login()

    async def test_too_many_sessions_ack(self, auth_instance_not_logged_in: Auth):
        """Test login with ACK error code 3 (too many sessions)."""
        with (
            patch.object(
                ClientSession, "post", new_callable=AsyncMock
            ) as mock_send_command,
            patch.object(
                Auth, "is_session_valid", return_value=None
            ) as mock_is_session_valid,
        ):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "sl_data_ack_reason": 3,
                "sl_client_id": "client_id",
                "sl_keep_alive_timeout_sec": 900,
            }
            mock_send_command.return_value = mock_response

            mock_is_session_valid.assert_not_called()
            with pytest.raises(
                CameDomoticAuthError,
                match=r"ACK error 3: Too many sessions during login\.",
            ):
                await auth_instance_not_logged_in.async_login()

    async def test_server_error_ack(self, auth_instance_not_logged_in: Auth):
        """Test login with server ACK error code (non-authentication)."""
        with (
            patch.object(
                ClientSession, "post", new_callable=AsyncMock
            ) as mock_send_command,
            patch.object(
                Auth, "is_session_valid", return_value=None
            ) as mock_is_session_valid,
        ):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "sl_data_ack_reason": 4,  # "Error occurred in JSON Syntax."
                "sl_client_id": "client_id",
                "sl_keep_alive_timeout_sec": 900,
            }
            mock_send_command.return_value = mock_response

            mock_is_session_valid.assert_not_called()
            with pytest.raises(
                CameDomoticAuthError,
                match=r"ACK error 4: Error occurred in JSON Syntax\.",
            ):
                await auth_instance_not_logged_in.async_login()


class TestAuthKeepAlive:
    """Tests for async_keep_alive method."""

    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_valid_session_successful(
        self, mock_send_command, mock_is_session_valid, auth_instance
    ):
        await auth_instance.async_keep_alive()
        mock_is_session_valid.assert_called_once()
        mock_send_command.assert_called_once_with({}, command_type="sl_keep_alive_req")

    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(
        Auth,
        "async_send_command",
        new_callable=AsyncMock,
        side_effect=CameDomoticServerError,
    )
    async def test_valid_session_unsuccessful(
        self, mock_send_command, mock_is_session_valid, auth_instance
    ):
        with pytest.raises(CameDomoticServerError):
            await auth_instance.async_keep_alive()
        mock_is_session_valid.assert_called_once()
        mock_send_command.assert_called_once_with({}, command_type="sl_keep_alive_req")

    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(Auth, "_async_perform_login", new_callable=AsyncMock)
    async def test_invalid_session_successful_login(
        self, mock_login, mock_is_session_valid, auth_instance
    ):
        await auth_instance.async_keep_alive()
        mock_is_session_valid.assert_called_once()
        mock_login.assert_called_once()

    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(
        Auth,
        "_async_perform_login",
        new_callable=AsyncMock,
        side_effect=CameDomoticAuthError,
    )
    async def test_invalid_session_unsuccessful_login(
        self, mock_login, mock_is_session_valid, auth_instance
    ):
        with pytest.raises(CameDomoticAuthError):
            await auth_instance.async_keep_alive()
        mock_is_session_valid.assert_called_once()
        mock_login.assert_called_once()


class TestAuthLogout:
    """Tests for async_logout method."""

    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_valid_session(self, mock_send_command, auth_instance: Auth):
        await auth_instance.async_logout()
        mock_send_command.assert_called_once_with({}, command_type="sl_logout_req")
        assert auth_instance.client_id == ""
        assert auth_instance.session_expiration_timestamp <= time.monotonic()

    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(Auth, "async_send_command", new_callable=AsyncMock)
    async def test_invalid_session(
        self, mock_send_command, mock_is_session_valid, auth_instance
    ):
        await auth_instance.async_logout()
        mock_is_session_valid.assert_called_once()
        mock_send_command.assert_not_called()

    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(
        Auth,
        "async_send_command",
        new_callable=AsyncMock,
        side_effect=CameDomoticServerError,
    )
    async def test_send_command_failure(
        self, mock_send_command, mock_is_session_valid, auth_instance
    ):
        with pytest.raises(CameDomoticServerError):
            await auth_instance.async_logout()
        mock_is_session_valid.assert_called_once()
        mock_send_command.assert_called_once()


class TestAuthDispose:
    """Tests for async_dispose method."""

    @patch.object(ClientSession, "close", new_callable=AsyncMock)
    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(Auth, "async_logout", new_callable=AsyncMock)
    async def test_valid_session_successful_logout(
        self, mock_logout, mock_is_session_valid, mock_close, auth_instance
    ):
        await auth_instance.async_dispose()
        mock_is_session_valid.assert_called_once()
        mock_logout.assert_called_once()
        mock_close.assert_called_once()

    @patch.object(ClientSession, "close", new_callable=AsyncMock)
    @patch.object(Auth, "is_session_valid", return_value=True)
    @patch.object(
        Auth, "async_logout", new_callable=AsyncMock, side_effect=CameDomoticServerError
    )
    async def test_valid_session_unsuccessful_logout(
        self, mock_logout, mock_is_session_valid, mock_close, auth_instance
    ):
        await auth_instance.async_dispose()
        mock_is_session_valid.assert_called_once()
        mock_logout.assert_called_once()
        mock_close.assert_called_once()

    @patch.object(ClientSession, "close", new_callable=AsyncMock)
    @patch.object(Auth, "is_session_valid", return_value=False)
    @patch.object(Auth, "async_logout", new_callable=AsyncMock)
    async def test_invalid_session(
        self, mock_logout, mock_is_session_valid, mock_close, auth_instance
    ):
        await auth_instance.async_dispose()
        mock_is_session_valid.assert_called_once()
        mock_logout.assert_not_called()
        mock_close.assert_called_once()

    @patch.object(ClientSession, "close", new_callable=AsyncMock)
    async def test_no_websession_close(self, mock_close, auth_instance):
        auth_instance.close_websession_on_disposal = False
        await auth_instance.async_dispose()
        mock_close.assert_not_called()


class TestAuthCredentials:
    """Tests for credential management methods."""

    async def test_update_credentials(self, auth_instance):
        """Test the update_auth_credentials method."""
        original_username = auth_instance.username
        original_password = auth_instance.password

        auth_instance.update_auth_credentials("new_user", "new_password")

        assert auth_instance.username != original_username
        assert auth_instance.password != original_password
        assert auth_instance.session_expiration_timestamp < time.monotonic()
        assert auth_instance.client_id == ""

        assert (
            auth_instance.cipher_suite.decrypt(auth_instance.username).decode()
            == "new_user"
        )
        assert (
            auth_instance.cipher_suite.decrypt(auth_instance.password).decode()
            == "new_password"
        )

    def test_backup_restore(self):
        """Test Auth backup and restore credentials methods."""
        mock_session = AsyncMock()
        auth = Auth(mock_session, "192.168.1.100", "user", "password")

        auth.client_id = "test_client_123"
        auth.session_expiration_timestamp = 1234567890
        auth.keep_alive_timeout_sec = 300
        auth.cseq = 42

        backup = auth.backup_auth_credentials()
        assert isinstance(backup, tuple)
        assert len(backup) == 6
        assert backup[2] == "test_client_123"
        assert backup[3] == 1234567890
        assert backup[4] == 300
        assert backup[5] == 42

        auth.client_id = "modified_client"
        auth.session_expiration_timestamp = 9876543210
        auth.keep_alive_timeout_sec = 600
        auth.cseq = 99

        auth.restore_auth_credentials(backup)
        assert auth.client_id == "test_client_123"
        assert auth.session_expiration_timestamp == 1234567890
        assert auth.keep_alive_timeout_sec == 300
        assert auth.cseq == 42


class TestAuthConcurrency:
    """Tests for concurrent access and deadlock prevention."""

    async def test_concurrent_logins(self, auth_instance):
        with patch.object(
            Auth, "async_send_command", new_callable=AsyncMock
        ) as mock_send_command:  # pylint: disable=unused-variable  # noqa: F841
            auth_instance.is_session_valid = Mock(side_effect=[False] * 10)

            async def login_side_effect():
                auth_instance.is_session_valid = Mock(return_value=True)

            auth_instance._async_perform_login = AsyncMock(
                side_effect=login_side_effect
            )

            await asyncio.gather(*(auth_instance.async_keep_alive() for _ in range(10)))

            assert auth_instance.is_session_valid(), (
                "Session should be valid after concurrent logins"
            )
            assert auth_instance._async_perform_login.call_count == 1, (
                "Login should be called exactly once"
            )

    @pytest.mark.asyncio
    async def test_no_deadlocks_under_load(self, auth_instance):
        auth_instance.is_session_valid = Mock(return_value=True)
        auth_instance.async_login = AsyncMock()
        auth_instance.async_send_command = AsyncMock()

        async with asyncio.Semaphore(10):
            tasks = [
                asyncio.create_task(auth_instance.async_keep_alive())
                for _ in range(100)
            ]
            await asyncio.gather(*tasks)

        assert all(task.done() for task in tasks), (
            "All tasks should complete successfully"
        )
