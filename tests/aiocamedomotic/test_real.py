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

from aiocamedomotic import CAME_MAC_PREFIXES, CameDomoticAPI
from aiocamedomotic.errors import CameDomoticError
from aiocamedomotic.models import (
    DigitalInputUpdate,
    LightStatus,
    LightUpdate,
    OpeningUpdate,
    PlantTopology,
    PlantUpdate,
    ScenarioUpdate,
    ThermoZoneFanSpeed,
    ThermoZoneMode,
    ThermoZoneSeason,
    ThermoZoneUpdate,
    User,
)
from aiocamedomotic.models.opening import OpeningStatus

RUN_TESTS_ON_REAL_SERVER = False

# Skip all tests in this module by default
pytestmark = pytest.mark.skipif(
    not RUN_TESTS_ON_REAL_SERVER,
    reason="All tests in this module are disabled by default.",
)


async def test_async_get_topology(api_instance_real: CameDomoticAPI):
    """Tests fetching the complete plant topology."""
    print("\nFetching plant topology...")
    topology = await api_instance_real.async_get_topology()

    assert topology is not None, "Failed to get topology"
    assert isinstance(topology, PlantTopology)

    print(f"Found {len(topology.floors)} floor(s):")
    if topology.floors:
        for floor in topology.floors:
            print(f"\n  Floor ID: {floor.id}, Name: {floor.name}")
            print(f"    Rooms ({len(floor.rooms)}):")
            for room in floor.rooms:
                print(f"      Room ID: {room.id}, Name: {room.name}")


async def test_async_get_floors_and_rooms(api_instance_real: CameDomoticAPI):
    """Tests fetching all floors and rooms from the server."""
    print("\nFetching all floors...")
    floors = await api_instance_real.async_get_floors()
    floors_by_id = {f.id: f.name for f in floors}

    print(f"Found {len(floors)} floor(s):")
    for floor in floors:
        print(f"  Floor ID: {floor.id}, Name: {floor.name}")

    print("\nFetching all rooms...")
    rooms = await api_instance_real.async_get_rooms()

    print(f"Found {len(rooms)} room(s):")
    for room in rooms:
        floor_name = floors_by_id.get(room.floor_id, "Unknown")
        print(
            f"  Room ID: {room.id}, Name: {room.name}, "
            f"Floor: {floor_name} (ID: {room.floor_id})"
        )

    assert floors is not None, "Failed to get floors"
    assert rooms is not None, "Failed to get rooms"


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
        print(
            f"ID: {light.act_id}, Name: {light.name}, Status: {light.status}, "
            f"Floor: {light.floor_ind}, Room: {light.room_ind}"
        )


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


async def test_async_get_digital_inputs(api_instance_real: CameDomoticAPI):
    """Tests fetching all digital inputs from the server."""
    print("\nFetching all digital inputs...")
    digital_inputs = await api_instance_real.async_get_digital_inputs()
    if not digital_inputs:
        print("No digital inputs found on the server.")
        return

    print(f"Found {len(digital_inputs)} digital input(s):")
    for di in digital_inputs:
        print(
            f"  ID: {di.act_id}"
            f" - Name: {di.name}"
            f" - Status: {di.status.name}"
            f" - Type: {di.type.name}"
            f" - Address: {di.addr}"
            f" - UTC time: {di.utc_time}"
        )
    assert digital_inputs is not None, "Failed to get digital inputs"


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


@pytest.mark.timeout(90)
async def test_listen_for_updates(api_instance_real: CameDomoticAPI):
    """Listens for 10 API calls and prints typed information for all updates."""
    max_api_calls = 20
    print(
        f"\nListening for real-time updates (waiting for {max_api_calls} API calls)..."
    )

    total_updates = 0
    batch_num = 0

    for batch_num in range(1, max_api_calls + 1):
        print(f"\n--- Waiting for batch {batch_num}/{max_api_calls}... ---")
        updates = await api_instance_real.async_get_updates()

        batch_count = len(updates)
        print(f"Batch {batch_num}: received {batch_count} update(s)")

        if updates.has_plant_update:
            print(
                "  *** Plant configuration changed — cached devices "
                "should be refreshed ***"
            )

        for update in updates.get_typed_updates():
            total_updates += 1
            print(f"\n  Update #{total_updates}:")

            if isinstance(update, LightUpdate):
                print(
                    f"    [Light] '{update.name}' (act_id={update.act_id})\n"
                    f"      Status: {update.status.name}, "
                    f"Type: {update.light_type.name}, "
                    f"Brightness: {update.perc}%"
                )
                if update.rgb is not None:
                    print(f"      RGB: {update.rgb}")

            elif isinstance(update, OpeningUpdate):
                print(
                    f"    [Opening] '{update.name}' "
                    f"(open_id={update.open_act_id}, "
                    f"close_id={update.close_act_id})\n"
                    f"      Status: {update.status.name}"
                )

            elif isinstance(update, ThermoZoneUpdate):
                print(
                    f"    [ThermoZone] '{update.name}' "
                    f"(act_id={update.act_id})\n"
                    f"      Temp: {update.temperature}\u00b0C, "
                    f"Setpoint: {update.set_point}\u00b0C\n"
                    f"      Mode: {update.mode.name}, "
                    f"Season: {update.season.name}, "
                    f"Status: {update.status.name}"
                )

            elif isinstance(update, ScenarioUpdate):
                print(
                    f"    [Scenario] '{update.name}' (id={update.id})\n"
                    f"      Status: {update.scenario_status.name}"
                )

            elif isinstance(update, DigitalInputUpdate):
                print(
                    f"    [DigitalInput] '{update.name}' "
                    f"(act_id={update.act_id})\n"
                    f"      Status: {update.status}, "
                    f"Addr: {update.addr}, "
                    f"UTC time: {update.utc_time}"
                )

            elif isinstance(update, PlantUpdate):
                print(
                    "    [Plant] Configuration change detected — "
                    "full device cache invalidation needed"
                )

            else:
                print(
                    f"    [Unknown] cmd_name='{update.cmd_name}', "
                    f"device_type={update.device_type}, "
                    f"device_id={update.device_id}, "
                    f"name='{update.name}'"
                )

    print(
        f"\nDone — collected {total_updates} update(s) "
        f"across {max_api_calls} API call(s)."
    )


def _get_thermo_zone_name(real_server_config) -> str:
    """Return the thermo zone name from config or a default."""
    if (
        real_server_config
        and "test_devices" in real_server_config
        and "thermo_zone_name" in real_server_config["test_devices"]
    ):
        return real_server_config["test_devices"]["thermo_zone_name"]
    return "Zona giorno"


async def test_thermo_zone_extended_properties(api_instance_real: CameDomoticAPI):
    """Reads all thermo zones and prints new extended properties."""
    print("\nFetching all thermoregulation zones with extended properties...")
    zones = await api_instance_real.async_get_thermo_zones()
    if not zones:
        pytest.skip("No thermoregulation zones found on the server.")
        return

    print(f"Found {len(zones)} zone(s):\n")
    for zone in zones:
        print(
            f"  Zone '{zone.name}' (ID: {zone.act_id})\n"
            f"    Temp: {zone.temperature}°C, Setpoint: {zone.set_point}°C\n"
            f"    Mode: {zone.mode.name}, Season: {zone.season.name}, "
            f"Status: {zone.status.name}\n"
            f"    Fan speed: {zone.fan_speed.name}\n"
            f"    Dehumidifier enabled: {zone.dehumidifier_enabled}, "
            f"setpoint: {zone.dehumidifier_setpoint}\n"
            f"    T1: {zone.t1}, T2: {zone.t2}, T3: {zone.t3}"
        )

        # Verify types are correct
        assert isinstance(zone.fan_speed, ThermoZoneFanSpeed)
        assert isinstance(zone.dehumidifier_enabled, bool)
        assert zone.dehumidifier_setpoint is None or isinstance(
            zone.dehumidifier_setpoint, float
        )
        assert zone.t1 is None or isinstance(zone.t1, float)
        assert zone.t2 is None or isinstance(zone.t2, float)
        assert zone.t3 is None or isinstance(zone.t3, float)


@pytest.mark.timeout(60)
async def test_thermo_zone_set_temperature(
    api_instance_real: CameDomoticAPI, real_server_config
):
    """Changes zone setpoint, waits for visual check, then reverts."""
    zone_name = _get_thermo_zone_name(real_server_config)
    print(f"\nLooking for zone: '{zone_name}'...")

    zones = await api_instance_real.async_get_thermo_zones()
    zone = next((z for z in zones if z.name == zone_name), None)
    if zone is None:
        pytest.skip(f"Zone '{zone_name}' not found on server")
        return

    initial_set_point = zone.set_point
    initial_mode = zone.mode
    new_set_point = initial_set_point + 1.0

    print(
        f"Zone '{zone.name}' initial state: "
        f"mode={initial_mode.name}, set_point={initial_set_point}°C"
    )

    try:
        print(f"  Setting temperature to {new_set_point}°C...")
        await zone.async_set_temperature(new_set_point)
        assert zone.set_point == new_set_point
        print(f"  Local state: set_point={zone.set_point}°C — check your app now")

        print("  Re-fetching all zones from server to verify server-side value...")
        zones_after = await api_instance_real.async_get_thermo_zones()
        zone_after = next((z for z in zones_after if z.name == zone_name), None)
        if zone_after is not None:
            print(
                f"  Server state after change: "
                f"mode={zone_after.mode.name}, set_point={zone_after.set_point}°C"
                f" (expected {new_set_point}°C)"
            )
        await asyncio.sleep(10)

        print(f"  Reverting temperature to {initial_set_point}°C...")
        await zone.async_set_temperature(initial_set_point)
        assert zone.set_point == initial_set_point
        print(f"  Local state: set_point={zone.set_point}°C — check your app now")
        await asyncio.sleep(5)
    finally:
        # Safety net: always try to restore
        if zone.set_point != initial_set_point:
            await zone.async_set_temperature(initial_set_point)
            print(f"  (safety revert to {initial_set_point}°C)")


@pytest.mark.timeout(80)
async def test_thermo_zone_mode_cycle(
    api_instance_real: CameDomoticAPI, real_server_config
):
    """Cycles through MANUAL -> AUTO -> JOLLY -> OFF, then restores."""
    zone_name = _get_thermo_zone_name(real_server_config)
    print(f"\nLooking for zone: '{zone_name}'...")

    zones = await api_instance_real.async_get_thermo_zones()
    zone = next((z for z in zones if z.name == zone_name), None)
    if zone is None:
        pytest.skip(f"Zone '{zone_name}' not found on server")
        return

    initial_mode = zone.mode
    initial_set_point = zone.set_point
    print(
        f"Zone '{zone.name}' initial state: "
        f"mode={initial_mode.name}, set_point={initial_set_point}°C"
    )

    modes_to_test = [
        ThermoZoneMode.MANUAL,
        ThermoZoneMode.AUTO,
        ThermoZoneMode.JOLLY,
        ThermoZoneMode.OFF,
    ]

    try:
        for mode in modes_to_test:
            print(f"  Setting mode to {mode.name}...")
            await zone.async_set_mode(mode)
            assert zone.mode == mode
            print(f"  Local state: mode={zone.mode.name} — check your app now")
            await asyncio.sleep(8)

        print(f"  Restoring mode to {initial_mode.name}...")
        await zone.async_set_mode(initial_mode)
        assert zone.mode == initial_mode
        print(f"  Local state: mode={zone.mode.name}")
    finally:
        if zone.mode != initial_mode:
            await zone.async_set_config(mode=initial_mode, set_point=initial_set_point)
            print(f"  (safety revert to mode={initial_mode.name})")


@pytest.mark.timeout(60)
async def test_thermo_zone_set_config_combined(
    api_instance_real: CameDomoticAPI, real_server_config
):
    """Tests async_set_config with mode + set_point + season together."""
    zone_name = _get_thermo_zone_name(real_server_config)
    print(f"\nLooking for zone: '{zone_name}'...")

    zones = await api_instance_real.async_get_thermo_zones()
    zone = next((z for z in zones if z.name == zone_name), None)
    if zone is None:
        pytest.skip(f"Zone '{zone_name}' not found on server")
        return

    initial_mode = zone.mode
    initial_set_point = zone.set_point
    print(
        f"Zone '{zone.name}' initial state: mode={initial_mode.name}, "
        f"set_point={initial_set_point}°C, season={zone.season.name}"
    )

    def _print_server_zones(fetched_zones, label):
        print(f"  Server state ({label}):")
        for z in fetched_zones:
            print(
                f"    '{z.name}': mode={z.mode.name}, "
                f"set_point={z.set_point}°C, season={z.season.name}"
            )

    try:
        print("  Setting: MANUAL, 22.0°C...")
        await zone.async_set_config(mode=ThermoZoneMode.MANUAL, set_point=22.0)
        assert zone.mode == ThermoZoneMode.MANUAL
        assert zone.set_point == 22.0
        print(
            f"  Local state: mode={zone.mode.name}, set_point={zone.set_point}°C, "
            f"season={zone.season.name}"
        )
        _print_server_zones(
            await api_instance_real.async_get_thermo_zones(), "after MANUAL/22.0"
        )
        await asyncio.sleep(10)

        print("  Setting: MANUAL, 18.5°C...")
        await zone.async_set_config(mode=ThermoZoneMode.MANUAL, set_point=18.5)
        assert zone.mode == ThermoZoneMode.MANUAL
        assert zone.set_point == 18.5
        print(
            f"  Local state: mode={zone.mode.name}, set_point={zone.set_point}°C, "
            f"season={zone.season.name}"
        )
        _print_server_zones(
            await api_instance_real.async_get_thermo_zones(), "after MANUAL/18.5"
        )
        await asyncio.sleep(10)

        print(f"  Restoring: {initial_mode.name}, {initial_set_point}°C...")
        await zone.async_set_config(mode=initial_mode, set_point=initial_set_point)
        print(
            f"  Local state: mode={zone.mode.name}, set_point={zone.set_point}°C, "
            f"season={zone.season.name}"
        )
        _print_server_zones(
            await api_instance_real.async_get_thermo_zones(), "after restore"
        )
    finally:
        if zone.mode != initial_mode or zone.set_point != initial_set_point:
            await zone.async_set_config(mode=initial_mode, set_point=initial_set_point)
            print("  (safety revert applied)")


@pytest.mark.timeout(60)
async def test_async_set_thermo_season_global(
    api_instance_real: CameDomoticAPI,
):
    """Tests global season switch at the plant level.

    Sequence: PLANT_OFF -> WINTER -> SUMMER -> restore.
    """
    print("\nFetching zones to determine current season...")
    zones = await api_instance_real.async_get_thermo_zones()
    if not zones:
        pytest.skip("No thermoregulation zones found on the server.")
        return

    def _print_all_seasons(fetched_zones, label):
        print(f"  Server state ({label}):")
        for z in fetched_zones:
            print(f"    '{z.name}': season={z.season.name}")

    initial_season = zones[0].season
    print(f"Current season (from first zone): {initial_season.name}")

    try:
        print("  Setting global season to PLANT_OFF...")
        await api_instance_real.async_set_thermo_season(ThermoZoneSeason.PLANT_OFF)
        _print_all_seasons(
            await api_instance_real.async_get_thermo_zones(), "after PLANT_OFF"
        )
        await asyncio.sleep(8)

        print("  Setting global season to WINTER...")
        await api_instance_real.async_set_thermo_season(ThermoZoneSeason.WINTER)
        _print_all_seasons(
            await api_instance_real.async_get_thermo_zones(), "after WINTER"
        )
        await asyncio.sleep(8)

        print("  Setting global season to SUMMER...")
        await api_instance_real.async_set_thermo_season(ThermoZoneSeason.SUMMER)
        _print_all_seasons(
            await api_instance_real.async_get_thermo_zones(), "after SUMMER"
        )
        await asyncio.sleep(8)

        print(f"  Restoring global season to {initial_season.name}...")
        await api_instance_real.async_set_thermo_season(initial_season)
        _print_all_seasons(
            await api_instance_real.async_get_thermo_zones(), "after restore"
        )
        print("  Done")
    finally:
        if initial_season not in (
            ThermoZoneSeason.UNKNOWN,
            ThermoZoneSeason.PLANT_OFF,
        ):
            await api_instance_real.async_set_thermo_season(initial_season)


@pytest.mark.timeout(30)
async def test_thermo_zone_updates_after_setpoint_change(
    api_instance_real: CameDomoticAPI, real_server_config
):
    """Switches zone to MANUAL, changes setpoint, listens for a ThermoZoneUpdate.

    Restores zone state after the test.
    """
    zone_name = _get_thermo_zone_name(real_server_config)
    print(f"\nLooking for zone: '{zone_name}'...")

    zones = await api_instance_real.async_get_thermo_zones()
    zone = next((z for z in zones if z.name == zone_name), None)
    if zone is None:
        pytest.skip(f"Zone '{zone_name}' not found on server")
        return

    initial_mode = zone.mode
    initial_set_point = zone.set_point
    new_set_point = initial_set_point + 0.5
    print(
        f"Zone '{zone.name}' initial state: mode={initial_mode.name}, "
        f"set_point={initial_set_point}°C"
    )

    try:
        print(f"  Switching to MANUAL and setting set_point to {new_set_point}°C...")
        await zone.async_set_config(mode=ThermoZoneMode.MANUAL, set_point=new_set_point)

        print("  Listening for ThermoZoneUpdate...")
        thermo_update_found = False
        while not thermo_update_found:
            updates = await api_instance_real.async_get_updates(timeout=10)
            for update in updates.get_typed_updates():
                if isinstance(update, ThermoZoneUpdate):
                    thermo_update_found = True
                    print(
                        f"\n  Received ThermoZoneUpdate for '{update.name}' "
                        f"(act_id={update.act_id}):\n"
                        f"    Temp: {update.temperature}°C, "
                        f"Setpoint: {update.set_point}°C\n"
                        f"    Mode: {update.mode.name}, "
                        f"Season: {update.season.name}, "
                        f"Status: {update.status.name}\n"
                        f"    Fan speed: {update.fan_speed.name}\n"
                        f"    Dehumidifier enabled: "
                        f"{update.dehumidifier_enabled}, "
                        f"setpoint: {update.dehumidifier_setpoint}\n"
                        f"    T1: {update.t1}, T2: {update.t2}, T3: {update.t3}"
                    )
                    break

        assert thermo_update_found, "No ThermoZoneUpdate received"
    finally:
        await zone.async_set_config(mode=initial_mode, set_point=initial_set_point)
        print(
            f"  Reverted to mode={initial_mode.name}, set_point={initial_set_point}°C"
        )


async def test_user_management_lifecycle(
    api_instance_real: CameDomoticAPI, real_server_config
):
    """Full lifecycle: create user, verify, switch session, change password, delete."""
    admin_username = real_server_config["came_server"]["username"]
    admin_password = real_server_config["came_server"]["password"]

    test_username = real_server_config["test_user"]["username"]
    test_password = real_server_config["test_user"]["password"]
    new_password = real_server_config["test_user"]["new_password"]

    # Step 1: Get users and terminal groups
    print("\n--- Step 1: Get users and terminal groups ---")
    users = await api_instance_real.async_get_users()
    print(f"Users: {[u.name for u in users]}")

    groups = await api_instance_real.async_get_terminal_groups()
    print(f"Groups: {[g.name for g in groups]}")
    assert groups, "No terminal groups found — cannot create a user without a group"
    group_name = groups[0].name
    print(f"Using group: '{group_name}'")

    # Clean up any leftover test user from a previous failed run
    leftover = next((u for u in users if u.name == test_username), None)
    if leftover:
        print(f"Cleaning up pre-existing '{test_username}' from a previous run")
        await leftover.async_delete()

    # Step 2: Create the test user
    print(f"\n--- Step 2: Create user '{test_username}' ---")
    await api_instance_real.async_add_user(test_username, test_password, group_name)
    print(f"User '{test_username}' created in group '{group_name}'")

    # Step 3: Verify the new user is in the users list
    print(f"\n--- Step 3: Verify '{test_username}' appears in users list ---")
    users_after = await api_instance_real.async_get_users()
    print(f"Users after creation: {[u.name for u in users_after]}")
    test_user = next((u for u in users_after if u.name == test_username), None)
    assert test_user is not None, (
        f"User '{test_username}' not found in list after creation"
    )
    print(f"Confirmed: '{test_username}' is present")

    # Step 4: Switch to test user, get server info, then switch back to admin
    print(
        f"\n--- Step 4: Login as '{test_username}', get server info, restore admin ---"
    )
    await test_user.async_set_as_current_user(test_password)
    print(f"Logged in as '{api_instance_real.auth.current_username}'")

    server_info = await api_instance_real.async_get_server_info()
    print(
        f"Server info (as '{test_username}'): "
        f"keycode={server_info.keycode}, swver={server_info.swver}"
    )
    assert server_info.keycode, "Server info keycode should not be empty"

    admin_user = User({"name": admin_username}, api_instance_real.auth)
    await admin_user.async_set_as_current_user(admin_password)
    print(f"Restored session as '{api_instance_real.auth.current_username}'")

    # Step 5: Change the test user's password
    print(f"\n--- Step 5: Change password of '{test_username}' ---")
    users_current = await api_instance_real.async_get_users()
    test_user = next((u for u in users_current if u.name == test_username), None)
    assert test_user is not None, (
        f"User '{test_username}' not found before password change"
    )
    await test_user.async_change_password(test_password, new_password)
    print(f"Password of '{test_username}' changed")

    # Step 6: Login with new password and verify with server info, then restore admin
    print(f"\n--- Step 6: Login as '{test_username}' with new password ---")
    await test_user.async_set_as_current_user(new_password)
    print(f"Logged in as '{api_instance_real.auth.current_username}' with new password")

    server_info = await api_instance_real.async_get_server_info()
    current = api_instance_real.auth.current_username
    print(
        f"Server info (as '{current}' with new password): keycode={server_info.keycode}"
    )
    assert server_info.keycode, "Server info keycode should not be empty"

    await admin_user.async_set_as_current_user(admin_password)
    print(f"Restored session as '{api_instance_real.auth.current_username}'")

    # Step 7: Delete the test user and verify it's gone
    print(f"\n--- Step 7: Delete '{test_username}' and verify ---")
    users_before_delete = await api_instance_real.async_get_users()
    test_user = next((u for u in users_before_delete if u.name == test_username), None)
    assert test_user is not None, f"User '{test_username}' not found before deletion"
    await test_user.async_delete()
    print(f"User '{test_username}' deleted")

    users_after_delete = await api_instance_real.async_get_users()
    print(f"Users after deletion: {[u.name for u in users_after_delete]}")
    assert not any(u.name == test_username for u in users_after_delete), (
        f"User '{test_username}' still present after deletion"
    )
    print(f"Confirmed: '{test_username}' is no longer in the users list")


async def test_async_ping(api_instance_real: CameDomoticAPI):
    """Tests server info retrieval followed by a ping with latency measurement."""
    print("\nFetching server info...")
    server_info = await api_instance_real.async_get_server_info()
    print(
        f"Server Info - Keycode: {server_info.keycode}, "
        f"Swver: {server_info.swver}, Board: {server_info.board}"
    )

    print("Pinging server...")
    latency_ms = await api_instance_real.async_ping()
    print(f"Ping successful — round-trip latency: {latency_ms:.1f} ms")

    assert isinstance(latency_ms, float)
    assert latency_ms >= 0


async def test_async_keep_alive(api_instance_real: CameDomoticAPI):
    """Tests that async_keep_alive succeeds on a live session."""
    print("\nCalling async_keep_alive...")
    await api_instance_real.auth.async_keep_alive()
    print("Keep-alive succeeded — session is still valid")
    assert api_instance_real.auth.is_session_valid()


async def test_autodiscovery(real_server_config):
    """Tests the two-step autodiscovery: MAC prefix check + API verification."""
    mac_address = real_server_config["came_server"].get("mac_address", "")
    if not mac_address:
        pytest.skip(
            "mac_address not configured in test_config.ini, "
            "skipping autodiscovery test."
        )
        return

    host = real_server_config["came_server"]["host"]
    username = real_server_config["came_server"]["username"]
    password = real_server_config["came_server"]["password"]

    # Step 1: Check the MAC prefix
    mac_upper = mac_address.upper()
    mac_matches = any(mac_upper.startswith(prefix) for prefix in CAME_MAC_PREFIXES)
    print(f"\nMAC address: {mac_upper[:8]}:**:**:**")
    print(f"Matches CAME prefix: {mac_matches}")
    assert mac_matches, (
        f"MAC address {mac_upper[:8]}:**:**:** does not match any known CAME prefix "
        f"({', '.join(CAME_MAC_PREFIXES)})"
    )

    # Step 2: Verify the device exposes a valid CAME API endpoint
    try:
        async with await CameDomoticAPI.async_create(host, username, password) as api:
            server_info = await api.async_get_server_info()
            print(
                f"Confirmed CAME server at {host}: "
                f"keycode={server_info.keycode}, "
                f"version={server_info.swver}"
            )
            assert server_info.keycode, "Server keycode should not be empty"
    except CameDomoticError as err:
        pytest.fail(f"CAME API verification failed: {err}")
