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

from unittest.mock import AsyncMock, Mock, patch

import aiohttp

from aiocamedomotic.utils import async_is_came_endpoint


class TestAsyncIsCameEndpoint:
    """Tests for the async_is_came_endpoint helper."""

    async def test_returns_true_on_http_200(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is True
                mock_get.assert_called_once_with(
                    "http://192.168.1.100/domo/",
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_returns_false_on_http_404(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 404
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is False

    async def test_returns_false_on_http_500(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 500
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is False

    async def test_returns_false_on_timeout(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get", side_effect=TimeoutError()):
                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is False

    async def test_returns_false_on_client_error(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get", side_effect=aiohttp.ClientError()):
                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is False

    async def test_returns_false_on_os_error(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(
                session, "get", side_effect=OSError("Network unreachable")
            ):
                result = await async_is_came_endpoint(
                    "192.168.1.100", websession=session
                )

                assert result is False

    async def test_creates_and_closes_own_session(self):
        mock_response = Mock()
        mock_response.status = 200

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("aiocamedomotic.utils.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            result = await async_is_came_endpoint("192.168.1.100")

            assert result is True
            mock_cls.assert_called_once()
            mock_session.close.assert_awaited_once()

    async def test_does_not_close_provided_session(self):
        mock_response = Mock()
        mock_response.status = 200

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await async_is_came_endpoint("192.168.1.100", websession=mock_session)

        assert result is True
        mock_session.close.assert_not_awaited()

    async def test_custom_timeout(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                await async_is_came_endpoint(
                    "192.168.1.100", websession=session, timeout=5
                )

                mock_get.assert_called_once_with(
                    "http://192.168.1.100/domo/",
                    timeout=aiohttp.ClientTimeout(total=5),
                )

    async def test_url_construction(self):
        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                await async_is_came_endpoint("came-server.local", websession=session)

                mock_get.assert_called_once_with(
                    "http://came-server.local/domo/",
                    timeout=aiohttp.ClientTimeout(total=10),
                )

    async def test_closes_own_session_on_error(self):
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get.side_effect = aiohttp.ClientError()

        with patch("aiocamedomotic.utils.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            result = await async_is_came_endpoint("192.168.1.100")

            assert result is False
            mock_session.close.assert_awaited_once()

    async def test_importable_from_package(self):
        from aiocamedomotic import (  # pylint: disable=import-outside-toplevel
            async_is_came_endpoint as imported_func,
        )

        assert callable(imported_func)
