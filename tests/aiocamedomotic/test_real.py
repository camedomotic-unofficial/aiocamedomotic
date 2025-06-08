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
    real_server_config,
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
    for feature in server_info.features:
        print(f"Feature Name: {feature}")


# Test for async_get_lights method
async def test_async_get_lights(api: CameDomoticAPI):
    lights = await api.async_get_lights()
    # Print the id, name and status of each light in a human readable format
    for light in lights:
        print(f"ID: {light.act_id}, Name: {light.name}, Status: {light.status}")


async def test_async_change_light_status(api: CameDomoticAPI, real_server_config):
    lights = await api.async_get_lights()

    # Get device name from config, provide a default if not found or section is missing
    light_name_to_test = "Lampada cabina armadio camera m"  # Default
    if (
        real_server_config
        and "test_devices" in real_server_config
        and "on_off_light_name" in real_server_config["test_devices"]
    ):
        light_name_to_test = real_server_config["test_devices"]["on_off_light_name"]
    else:
        print(
            f"Warning: 'on_off_light_name' not found in test_config.ini, using default: {light_name_to_test}"
        )

    light = next((lig for lig in lights if lig.name == light_name_to_test), None)
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


async def test_async_control_specific_shutter(api: CameDomoticAPI, real_server_config):
    """Tests shutter control: CLOSE -> STOPPED -> OPEN sequence."""
    wait_time_sec = 3
    shutter_name = "Tapparella Camera matrimoniale"
    if (
        real_server_config
        and "test_devices" in real_server_config
        and "shutter_name" in real_server_config["test_devices"]
    ):
        shutter_name = real_server_config["test_devices"]["shutter_name"]
    else:
        print(
            f"Warning: 'shutter_name' not found in test_config.ini, using default: {shutter_name}"
        )

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


async def test_async_usage_example(api: CameDomoticAPI, real_server_config):
    # Get the list of all the lights configured on the CAME server
    lights = await api.async_get_lights()

    dimmable_light_id_to_test = 13  # Default
    if (
        real_server_config
        and "test_devices" in real_server_config
        and "dimmable_light_id" in real_server_config["test_devices"]
    ):
        try:
            dimmable_light_id_to_test = int(
                real_server_config["test_devices"]["dimmable_light_id"]
            )
        except ValueError:
            print(
                f"Warning: 'dimmable_light_id' in config is not an int, using default: {dimmable_light_id_to_test}"
            )
    else:
        print(
            f"Warning: 'dimmable_light_id' not found in test_config.ini, using default: {dimmable_light_id_to_test}"
        )

    on_off_light_name_to_test = (
        "Lampada cabina armadio camera m"  # Default (example, adjust)
    )
    if (
        real_server_config
        and "test_devices" in real_server_config
        and "on_off_light_name" in real_server_config["test_devices"]
    ):
        on_off_light_name_to_test = real_server_config["test_devices"][
            "on_off_light_name"
        ]
    else:
        print(
            f"Warning: 'on_off_light_name' not found in test_config.ini, using default: {on_off_light_name_to_test}"
        )

    # Get a specific light by ID
    bedroom_dimmable_lamp = next(
        (light for light in lights if light.act_id == dimmable_light_id_to_test), None
    )

    # Get a specific light by name
    bedroom_lamp = next(
        (light for light in lights if light.name == on_off_light_name_to_test),
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
