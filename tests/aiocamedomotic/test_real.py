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
They are skipped by default, but can be enabled by setting the RUN_TESTS_ON_REAL_SERVER
variable to True.
"""

# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import asyncio

import pytest

from aiocamedomotic import CameDomoticAPI
from aiocamedomotic.models import LightStatus
from aiocamedomotic.models.opening import OpeningStatus

RUN_TESTS_ON_REAL_SERVER = False

# Skip all tests in this module by default
pytestmark = pytest.mark.skipif(
    not RUN_TESTS_ON_REAL_SERVER,
    reason="All tests in this module are disabled by default.",
)


async def test_async_get_users(api_instance_real: CameDomoticAPI):
    users = await api_instance_real.async_get_users()
    # Print the username of each user in a human readable format
    for user in users:
        print(f"Username: {user.name}")


# Test for async_get_server_info method
async def test_async_get_server_info(api_instance_real: CameDomoticAPI):
    server_info = await api_instance_real.async_get_server_info()
    # Print the server_info attributes in a human readable format
    print(f"Server Info - Keycode: {server_info.keycode}")
    print(f"Server Info - Swver: {server_info.swver}")
    print(f"Server Info - Serial: {server_info.serial}")
    print(f"Server Info - Board: {server_info.board}")
    print(f"Server Info - Type: {server_info.type}")
    for feature in server_info.features:
        print(f"Feature Name: {feature}")


# Test for async_get_lights method
async def test_async_get_lights(api_instance_real: CameDomoticAPI):
    lights = await api_instance_real.async_get_lights()
    # Print the id, name and status of each light in a human readable format
    for light in lights:
        print(f"ID: {light.act_id}, Name: {light.name}, Status: {light.status}")


async def test_async_change_light_status(api_instance_real: CameDomoticAPI):
    light_name = "Lampadario sala pranzo"
    lights = await api_instance_real.async_get_lights()

    light = next((lig for lig in lights if lig.name == light_name), None)
    if light is None:
        pytest.skip(f"Light '{light_name}' not found on server")
        return

    initial_status = light.status
    print(f"Light '{light_name}' initial status: {initial_status.name}")

    toggled_status = (
        LightStatus.OFF if initial_status == LightStatus.ON else LightStatus.ON
    )
    await light.async_set_status(toggled_status)
    print(f"Light '{light_name}' changed to: {toggled_status.name}")

    await asyncio.sleep(5)

    await light.async_set_status(initial_status)
    print(f"Light '{light_name}' reverted to: {initial_status.name}")


async def test_async_get_openings(api_instance_real: CameDomoticAPI):
    """Tests fetching all openings from the server."""
    print("\nFetching all openings...")
    openings = await api_instance_real.async_get_openings()
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


async def test_async_control_specific_shutter(
    api_instance_real: CameDomoticAPI, real_server_config
):
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
            "Warning: 'shutter_name' not found in "
            f"test_config.ini, using default: {shutter_name}"
        )

    print(f"\nLooking for shutter: '{shutter_name}'...")
    openings = await api_instance_real.async_get_openings()
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
        print("  Setting to CLOSING")
        await target_shutter.async_set_status(OpeningStatus.CLOSING)
        print(f"  Status: {target_shutter.status.name}")
        await asyncio.sleep(wait_time_sec)

        # Stop
        print("  Setting to STOPPED")
        await target_shutter.async_set_status(OpeningStatus.STOPPED)
        print(f"  Status: {target_shutter.status.name}")
        await asyncio.sleep(wait_time_sec)

        # Open
        print("  Setting to OPENING")
        await target_shutter.async_set_status(OpeningStatus.OPENING)
        print(f"  Status: {target_shutter.status.name}")

        print("Control sequence completed")

    except Exception as e:
        pytest.fail(f"Error controlling shutter: {e}")

    assert target_shutter.status == OpeningStatus.OPENING


async def test_async_get_scenarios(api_instance_real: CameDomoticAPI):
    """Tests fetching all scenarios from the server."""
    print("\nFetching all scenarios...")
    scenarios = await api_instance_real.async_get_scenarios()
    if not scenarios:
        print("No scenarios found on the server.")
        return

    print(f"Found {len(scenarios)} scenario(s):")
    for scenario in scenarios:
        print(
            f"  ID: {scenario.id}"
            f" - Name: {scenario.name}"
            f" - Status: {scenario.scenario_status.name}"
            f" - Icon: {scenario.icon_id}"
            f" - User-defined: {scenario.user_defined}"
        )
    assert scenarios is not None, "Failed to get scenarios"


@pytest.mark.timeout(130)
async def test_scenario_activation_openings_down_and_up(
    api_instance_real: CameDomoticAPI,
):
    """Tests scenario activation: close all shutters, wait 1 minute, then open them."""
    scenarios = await api_instance_real.async_get_scenarios()
    if not scenarios:
        pytest.skip("No scenarios found on the server.")
        return

    scenario_down = next((s for s in scenarios if s.id == 8), None)
    scenario_up = next((s for s in scenarios if s.id == 5), None)

    if scenario_down is None:
        pytest.skip("Scenario 8 not found on the server.")
        return

    if scenario_up is None:
        pytest.skip("Scenario 5 not found on the server.")
        return

    print(f"\nActivating scenario '{scenario_down.name}' (ID: {scenario_down.id})...")
    await scenario_down.async_activate()

    print("Waiting 60 seconds...")
    await asyncio.sleep(30)

    print(f"Activating scenario '{scenario_up.name}' (ID: {scenario_up.id})...")
    await scenario_up.async_activate()
    print("Done.")


async def test_async_get_thermo_zones(api_instance_real: CameDomoticAPI):
    """Tests fetching all thermoregulation zones from the server."""
    print("\nFetching all thermoregulation zones...")
    zones = await api_instance_real.async_get_thermo_zones()
    if not zones:
        print("No thermoregulation zones found on the server.")
        return

    print(f"Found {len(zones)} zone(s):")
    for zone in zones:
        print(
            f"  ID: {zone.act_id}"
            f" - Name: {zone.name}"
            f" - Temp: {zone.temperature}\u00b0C"
            f" - Setpoint: {zone.set_point}\u00b0C"
            f" - Mode: {zone.mode.name}"
            f" - Season: {zone.season.name}"
            f" - Status: {zone.status.name}"
        )
    assert zones is not None, "Failed to get thermo zones"


async def test_async_get_analog_sensors(api_instance_real: CameDomoticAPI):
    """Tests fetching analog sensors from the server."""
    print("\nFetching analog sensors...")
    sensors = await api_instance_real.async_get_analog_sensors()
    if not sensors:
        print("No analog sensors found on the server.")
        return

    print(f"Found {len(sensors)} sensor(s):")
    for sensor in sensors:
        print(
            f"  ID: {sensor.act_id}"
            f" - Name: {sensor.name}"
            f" - Value: {sensor.value}"
            f" - Unit: {sensor.unit}"
        )
    assert sensors is not None, "Failed to get analog sensors"


async def test_async_dimmable_light(api_instance_real: CameDomoticAPI):
    light_name = "Led porta finestra sala"
    lights = await api_instance_real.async_get_lights()

    light = next((lig for lig in lights if lig.name == light_name), None)
    if light is None:
        pytest.skip(f"Light '{light_name}' not found on server")
        return

    initial_status = light.status
    initial_brightness = light.perc
    print(
        f"Light '{light_name}' initial state: "
        f"status={initial_status.name}, brightness={initial_brightness}%"
    )

    try:
        # If the light is off, switch it on first
        if initial_status == LightStatus.OFF:
            await light.async_set_status(LightStatus.ON)
            print(f"Light '{light_name}' switched ON")
            await asyncio.sleep(2)

        # Dim to 100%
        await light.async_set_status(LightStatus.ON, brightness=100)
        print(f"Light '{light_name}' dimmed to 100%")
        await asyncio.sleep(2)

        # Dim to 40%
        await light.async_set_status(LightStatus.ON, brightness=40)
        print(f"Light '{light_name}' dimmed to 40%")
        await asyncio.sleep(2)

        # Switch off
        await light.async_set_status(LightStatus.OFF)
        print(f"Light '{light_name}' switched OFF")
        await asyncio.sleep(2)

    finally:
        # Revert to original configuration
        await light.async_set_status(initial_status, brightness=initial_brightness)
        print(
            f"Light '{light_name}' reverted to: "
            f"status={initial_status.name}, brightness={initial_brightness}%"
        )
