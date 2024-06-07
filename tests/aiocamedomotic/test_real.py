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
import pytest

from aiocamedomotic import CameDomoticAPI
from aiocamedomotic.models import LightStatus

from tests.aiocamedomotic.const import (
    api_instance_real as api,  # pylint: disable=unused-import  # noqa: F401
)


SKIP_TESTS_ON_REAL_SERVER = True

# Skip all tests in this module by default
pytestmark = pytest.mark.skipif(
    SKIP_TESTS_ON_REAL_SERVER,
    reason="All tests in this module are disabled by default.",
)


async def test_async_get_users(api: CameDomoticAPI):
    users = await api.async_get_users()
    # Print the username of each user in a human readable format
    for user in users:
        print(f"Username: {user.name}")


async def test_async_get_users_new(api: CameDomoticAPI):
    users = await api.async_get_users()
    # Print the username of each user in a human readable format
    for user in users:
        print(f"Username: {user.name}")


# Test for async_get_server_info method
async def test_async_get_server_info(api: CameDomoticAPI):
    server_info = await api.async_get_server_info()
    # Print the server_info attributes in a human readable format
    print(f"Server Info - Keycode: {server_info.keycode}")
    print(f"Server Info - Swver: {server_info.swver}")
    print(f"Server Info - Serial: {server_info.serial}")
    print(f"Server Info - Board: {server_info.board}")
    print(f"Server Info - Type: {server_info.type}")
    for feature in server_info.list:
        print(f"Feature Name: {feature}")


# Test for async_get_lights method
async def test_async_get_lights(api: CameDomoticAPI):
    lights = await api.async_get_lights()
    # Print the id, name and status of each light in a human readable format
    for light in lights:
        print(f"ID: {light.act_id}, Name: {light.name}, Status: {light.status}")


async def test_async_change_light_status(api: CameDomoticAPI):
    lights = await api.async_get_lights()

    light = next(
        (lig for lig in lights if lig.name == "Lampada cabina armadio camera m"), None
    )
    if light:
        await light.async_set_status(
            LightStatus.OFF if light.status == LightStatus.ON else LightStatus.ON
        )
        # wait 1 second
        await asyncio.sleep(3)
        await light.async_set_status(
            LightStatus.OFF if light.status == LightStatus.ON else LightStatus.ON
        )


async def test_async_usage_example():
    async with await CameDomoticAPI.async_create(
        "192.168.1.3", "admin", "admin"
    ) as api:

        # Get the list of all the lights configured on the CAME server
        lights = await api.async_get_lights()

        # Get a specific light by ID
        bedroom_dimmable_lamp = next(
            (light for light in lights if light.act_id == 13), None
        )

        # Get a specific light by name
        kitchen_lamp = next(
            (
                light
                for light in lights
                if light.name == "Lampada cabina armadio camera m"
            ),
            None,
        )

        # Ensure the light is found (dimmable)
        if bedroom_dimmable_lamp:
            # Turn the light on, setting the brightness to 50%
            await bedroom_dimmable_lamp.async_set_status(LightStatus.ON, brightness=14)

            # Turn the light off
            await bedroom_dimmable_lamp.async_set_status(LightStatus.OFF)

            # Turn the light on, leaving the brightness unchanged
            await bedroom_dimmable_lamp.async_set_status(LightStatus.ON)

        # Ensure the light is found
        if kitchen_lamp:
            # Turn the light on
            await kitchen_lamp.async_set_status(LightStatus.ON)

            # Turn the light off
            await kitchen_lamp.async_set_status(LightStatus.OFF)
