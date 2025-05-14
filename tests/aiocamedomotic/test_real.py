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

"""
Test module for real server connections.

These tests are designed to be run against a real CAME Domotic server.
They are skipped by default, but can be enabled by setting the SKIP_TESTS_ON_REAL_SERVER
variable to False.

To configure the connection to a real server, set the following environment variables:
- CAMEDOMOTIC_HOST: The IP address of the CAME Domotic server
- CAMEDOMOTIC_USERNAME: The username for authentication
- CAMEDOMOTIC_PASSWORD: The password for authentication

Example:
    $ export CAMEDOMOTIC_HOST="192.168.x.y"
    $ export CAMEDOMOTIC_USERNAME="my_username"
    $ export CAMEDOMOTIC_PASSWORD="my_password"
    $ pytest tests/aiocamedomotic/test_real.py -v
"""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

# flake8: noqa: F811

import asyncio
import os
import pytest

from aiocamedomotic import CameDomoticAPI
from aiocamedomotic.models import LightStatus
from aiocamedomotic.models.opening import Opening, OpeningStatus, OpeningType

from tests.aiocamedomotic.const import (
    api_instance_real as api,
)  # pylint: disable=unused-import  # noqa: F401


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


async def test_async_get_openings(api: CameDomoticAPI):
    """Tests fetching all openings from the server."""
    print("\nFetching all openings...")
    openings = await api.async_get_openings()
    if not openings:
        print("No openings found on the server.")
        return

    print(f"Found {len(openings)} opening(s):")
    for opening in openings:
        print(
            f"Open/Close IDs: {opening.open_act_id}/{opening.close_act_id}"
            f" - Name: {opening.name}, "
            f" - Status: {opening.status.name}, "
            f" - Type: {opening.type.name}"
        )
    assert openings is not None, "Failed to get openings"


async def test_async_control_specific_shutter(api: CameDomoticAPI):
    """Tests shutter control: CLOSE -> STOPPED -> OPEN sequence."""
    shutter_name = "Tapparella Camera matrimoniale"
    wait_time_sec = 3

    print(f"\nLooking for shutter: '{shutter_name}'...")
    openings = await api.async_get_openings()
    if not openings:
        pytest.skip("No openings found on server")
        return

    target_shutter = next((o for o in openings if o.name == shutter_name), None)
    if target_shutter is None:
        pytest.skip(f"Shutter '{shutter_name}' not found")
        return

    print(f"Found '{target_shutter.name}' (Open ID: {target_shutter.open_act_id})")
    print("Starting control sequence...")

    try:
        # Close
        print(f"  Setting to CLOSING")
        await target_shutter.async_set_status(OpeningStatus.CLOSING)
        print(f"  Status: {target_shutter.status.name}")
        await asyncio.sleep(wait_time_sec)

        # Stop
        print(f"  Setting to STOPPED")
        await target_shutter.async_set_status(OpeningStatus.STOPPED)
        print(f"  Status: {target_shutter.status.name}")
        await asyncio.sleep(wait_time_sec)

        # Open
        print(f"  Setting to OPENING")
        await target_shutter.async_set_status(OpeningStatus.OPENING)
        print(f"  Status: {target_shutter.status.name}")

        print("Control sequence completed")

    except Exception as e:
        pytest.fail(f"Error controlling shutter: {e}")

    assert target_shutter.status == OpeningStatus.OPENING


async def test_async_usage_example():
    host = os.environ.get("CAMEDOMOTIC_HOST")
    username = os.environ.get("CAMEDOMOTIC_USERNAME")
    password = os.environ.get("CAMEDOMOTIC_PASSWORD")

    async with await CameDomoticAPI.async_create(host, username, password) as api:
        # Get the list of all the lights configured on the CAME server
        lights = await api.async_get_lights()

        # Get a specific light by ID
        bedroom_dimmable_lamp = next(
            (light for light in lights if light.act_id == 13), None
        )

        # Get a specific light by name
        bedroom_lamp = next(
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
            await bedroom_dimmable_lamp.async_set_status(LightStatus.ON, brightness=50)

            # Turn the light off
            await bedroom_dimmable_lamp.async_set_status(LightStatus.OFF)

            # Turn the light on, leaving the brightness unchanged
            await bedroom_dimmable_lamp.async_set_status(LightStatus.ON)

        # Ensure the light is found
        if bedroom_lamp:
            # Turn the light on
            await bedroom_lamp.async_set_status(LightStatus.ON)

            # Turn the light off
            await bedroom_lamp.async_set_status(LightStatus.OFF)
