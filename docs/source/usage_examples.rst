.. SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
.. SPDX-License-Identifier: Apache-2.0

Usage examples
==============

This page walks you through the typical workflow for integrating with a
CAME Domotic server: connecting, discovering what the server offers, fetching
and controlling devices, and monitoring real-time changes. For a minimal
"hello world" example, see :doc:`getting_started`.

.. note::
    The examples below assume the library is installed (``pip install
    aiocamedomotic``). Unless otherwise noted, all code runs inside an
    ``async with`` block:

    .. code-block:: python

        import asyncio

        from aiocamedomotic import CameDomoticAPI
        from aiocamedomotic.models import (
            AnalogSensorType, DeviceType, DigitalInputStatus, LightStatus,
            LightType, LoadsCtrlProfile, OpeningStatus, ProfileDay,
            RelayStatus, ScenarioStatus,
            ServerFeature, ThermoProfile, ThermoZoneFanSpeed,
            ThermoZoneMode, ThermoZoneSeason, ThermoZoneStatus,
            Timer, TimerTimeSlot, TimerUpdate,
            DeviceUpdate, LightUpdate, OpeningUpdate, RelayUpdate,
            ThermoZoneUpdate, ScenarioUpdate, DigitalInputUpdate,
            AnalogInUpdate, EnergyMeterUpdate, LoadsCtrlMeterUpdate,
            LoadsCtrlRelayUpdate, PlantUpdate, WEEKDAYS,
        )
        from aiocamedomotic.errors import (
            CameDomoticError,
            CameDomoticServerNotFoundError,
            CameDomoticAuthError,
            CameDomoticServerTimeoutError,
            CameDomoticServerError,
        )

        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:
            ...


Connecting to the server
------------------------

Creating the API client
^^^^^^^^^^^^^^^^^^^^^^^

Create a ``CameDomoticAPI`` instance with the async factory method. The
``async with`` statement ensures resources are cleaned up automatically:

.. code-block:: python

    import asyncio
    from aiocamedomotic import CameDomoticAPI

    async def main():
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:
            server_info = await api.async_get_server_info()
            print(f"Connected to server: {server_info.keycode}")

    asyncio.run(main())

.. note::
    The session is **not** authenticated at creation time. The library
    authenticates lazily on the first real API call, like ``async_get_server_info()``.
    If the credentials are invalid, a ``CameDomoticAuthError`` will be raised at that
    point.

Using an existing HTTP session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you already have an ``aiohttp.ClientSession`` (e.g. in Home Assistant),
pass it via the ``websession`` parameter:

.. code-block:: python

    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password",
        websession=my_existing_session
    ) as api:
        ...

Handling connection errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

The library raises specific exceptions for different failure scenarios:

.. code-block:: python

    from aiocamedomotic import CameDomoticAPI
    from aiocamedomotic.errors import (
        CameDomoticServerNotFoundError,
        CameDomoticAuthError,
        CameDomoticServerTimeoutError,
        CameDomoticServerError,
    )

    async def main():
        try:
            async with await CameDomoticAPI.async_create(
                "192.168.x.x", "username", "password"
            ) as api:
                lights = await api.async_get_lights()
        except CameDomoticServerNotFoundError:
            print("Server not reachable. Check the IP address.")
        except CameDomoticAuthError:
            print("Authentication failed. Check your credentials.")
        except CameDomoticServerTimeoutError:
            print("Request timed out. The server may be busy, retry later.")
        except CameDomoticServerError as err:
            print(f"Server error: {err}")

The exception hierarchy is:

- ``CameDomoticError`` — base class
    - ``CameDomoticServerNotFoundError`` — host unreachable (transient)
    - ``CameDomoticAuthError`` — bad credentials or too many sessions
    - ``CameDomoticServerError`` — other server errors
        - ``CameDomoticServerTimeoutError`` — request timeout (transient, retryable)


Server configuration
--------------------

Server information
^^^^^^^^^^^^^^^^^^

Retrieve the server properties with ``async_get_server_info()``. The
``keycode`` property serves as a unique identifier for the server:

.. code-block:: python

    server_info = await api.async_get_server_info()

    print(f"Keycode: {server_info.keycode}")
    print(f"Software version: {server_info.swver}")
    print(f"Server type: {server_info.type}")
    print(f"Board type: {server_info.board}")
    print(f"Serial number: {server_info.serial}")

Example output:

.. code-block:: text

    Keycode: 0000FFFF9999AAAA
    Software version: 1.2.3
    Server type: 0
    Board type: 3
    Serial number: 0011ffee

Connectivity check
^^^^^^^^^^^^^^^^^^

Use ``async_ping()`` to verify the server is reachable and measure
round-trip latency:

.. code-block:: python

    try:
        latency_ms = await api.async_ping()
        print(f"Server responded in {latency_ms:.1f} ms")
    except CameDomoticServerNotFoundError:
        print("Server is unreachable")
    except CameDomoticServerTimeoutError:
        print("Server timed out")

Available features
^^^^^^^^^^^^^^^^^^

The ``features`` property on ``ServerInfo`` lists the capabilities configured
on the server. These are the functional blocks you would see in the official
CAME Domotic mobile app (lights, openings, scenarios, etc.):

.. code-block:: python

    server_info = await api.async_get_server_info()

    for feature in server_info.features:
        print(f"Feature: {feature}")

Example output:

.. code-block:: text

    Feature: lights
    Feature: openings
    Feature: thermoregulation
    Feature: scenarios
    Feature: digitalin
    Feature: analogin
    Feature: energy
    Feature: loadsctrl

The ``features`` property returns plain strings whose known values are
defined in :class:`~aiocamedomotic.models.ServerFeature`. You can compare
entries against enum members to decide which device APIs to call:

.. code-block:: python

    from aiocamedomotic.models import ServerFeature

    if ServerFeature.LIGHTS in server_info.features:
        lights = await api.async_get_lights()

    if ServerFeature.OPENINGS in server_info.features:
        openings = await api.async_get_openings()

    if ServerFeature.RELAYS in server_info.features:
        relays = await api.async_get_relays()

    if ServerFeature.THERMOREGULATION in server_info.features:
        zones = await api.async_get_thermo_zones()
        sensors = await api.async_get_analog_sensors()

    if ServerFeature.SCENARIOS in server_info.features:
        scenarios = await api.async_get_scenarios()

    if ServerFeature.DIGITALIN in server_info.features:
        digital_inputs = await api.async_get_digital_inputs()

    if ServerFeature.ANALOGIN in server_info.features:
        analog_inputs = await api.async_get_analog_inputs()

    if ServerFeature.TIMERS in server_info.features:
        timers = await api.async_get_timers()

    if ServerFeature.ENERGY in server_info.features:
        meters = await api.async_get_energy_meters()

    if ServerFeature.LOADSCTRL in server_info.features:
        controllers = await api.async_get_loadsctrl_meters()

Floors and rooms
^^^^^^^^^^^^^^^^

Retrieve the building topology to understand how devices are organized.
``async_get_topology()`` merges data from multiple server endpoints and
nested device list commands, ensuring that floors and rooms are discovered
even on servers where some endpoints return empty:

.. code-block:: python

    topology = await api.async_get_topology()

    for floor in topology.floors:
        print(f"Floor {floor.id}: {floor.name}")
        for room in floor.rooms:
            print(f"  Room {room.id}: {room.name}")

Example output:

.. code-block:: text

    Floor 0: Ground Floor
      Room 1: Living Room
      Room 2: Kitchen
    Floor 1: First Floor
      Room 3: Bedroom
      Room 4: Bathroom

Working with devices
--------------------

All device types follow the same pattern: fetch the list, find a specific
device, and control it. Lights are shown in full detail below; the other
device types use the same approach with their own properties and methods.

Lights
^^^^^^

**Fetching and inspecting lights:**

.. code-block:: python

    lights = await api.async_get_lights()

    for light in lights:
        print(
            f"ID: {light.act_id}, Name: {light.name}, "
            f"Status: {light.status}, Type: {light.type}"
        )

Example output:

.. code-block:: text

    ID: 1, Name: Living Room Chandelier, Status: LightStatus.ON, Type: LightType.STEP_STEP
    ID: 2, Name: Hallway Night Light, Status: LightStatus.OFF, Type: LightType.DIMMER
    ID: 3, Name: RGB Strip, Status: LightStatus.ON, Type: LightType.RGB

**Finding a specific light:**

.. code-block:: python

    # By ID
    chandelier = next((l for l in lights if l.act_id == 1), None)

    # By name
    hallway = next((l for l in lights if l.name == "Hallway Night Light"), None)

**Controlling lights:**

.. code-block:: python

    from aiocamedomotic.models import LightStatus

    # Simple on/off (STEP_STEP lights)
    if chandelier:
        await chandelier.async_set_status(LightStatus.ON)
        await chandelier.async_set_status(LightStatus.OFF)

    # Dimmable lights: set brightness (0-100)
    if hallway:
        await hallway.async_set_status(LightStatus.ON, brightness=50)
        await hallway.async_set_status(LightStatus.ON, brightness=100)

    # RGB lights: set color as [R, G, B] (each 0-255)
    rgb_strip = next((l for l in lights if l.type == LightType.RGB), None)
    if rgb_strip:
        await rgb_strip.async_set_status(LightStatus.ON, rgb=[255, 0, 0])
        await rgb_strip.async_set_status(LightStatus.ON, brightness=75, rgb=[0, 128, 255])

.. note::
    The ``brightness`` parameter is silently ignored for non-dimmable
    (STEP_STEP) lights. The ``rgb`` parameter is silently ignored for
    non-RGB lights. Dimmer hardware may quantize the requested brightness
    to its own steps, so the server can report back a slightly different
    value (e.g. requesting ``50`` may result in ``52``).

Openings
^^^^^^^^

Openings represent shutters, awnings, and similar motorized covers. They
support opening, closing, stopping, and slat tilting (open/close) for
covers with adjustable slats (e.g., venetian blinds).

.. code-block:: python

    import asyncio
    from aiocamedomotic.models import OpeningStatus

    openings = await api.async_get_openings()

    for opening in openings:
        print(f"ID: {opening.open_act_id}, Name: {opening.name}, Status: {opening.status}")

    # Control an opening
    shutter = next((o for o in openings if o.open_act_id == 10), None)
    if shutter:
        await shutter.async_set_status(OpeningStatus.OPENING)
        await asyncio.sleep(5)
        await shutter.async_set_status(OpeningStatus.STOPPED)
        await asyncio.sleep(5)
        await shutter.async_set_status(OpeningStatus.CLOSING)

        # Tilt slats (for covers with adjustable slats)
        await asyncio.sleep(5)
        await shutter.async_set_status(OpeningStatus.SLAT_OPEN)
        await asyncio.sleep(5)
        await shutter.async_set_status(OpeningStatus.SLAT_CLOSE)

Scenarios
^^^^^^^^^

Scenarios are pre-configured automation sequences. They can only be
activated (fire-and-forget); there is no bidirectional status control.

.. code-block:: python

    scenarios = await api.async_get_scenarios()

    for scenario in scenarios:
        print(f"ID: {scenario.id}, Name: {scenario.name}, Status: {scenario.scenario_status}")

    # Activate a scenario
    good_morning = next((s for s in scenarios if s.name == "Good morning"), None)
    if good_morning:
        await good_morning.async_activate()

**Recording a new custom scenario:**

Custom (user-defined) scenarios are created by *recording* them: you put
the server in recording mode, perform the actions you want the scenario
to replay (e.g. switching lights on/off), and then finalize the
recording. This mirrors the recording feature of the official CAME app.

.. code-block:: python

    # 1. Start recording a new scenario
    await api.async_start_scenario_recording("Movie night")

    # 2. Perform the actions to be captured, e.g. by pressing physical
    #    switches on the plant, or via API commands:
    lights = await api.async_get_lights()
    living_room = next(l for l in lights if l.name == "Living room")
    await living_room.async_set_status(LightStatus.OFF)

    # 3. Finalize the recording: the server saves the new scenario and
    #    the method returns it as a Scenario object
    movie_night = await api.async_stop_scenario_recording()
    print(f"Created scenario '{movie_night.name}' (ID: {movie_night.id})")

    # The new scenario can now be activated like any other one
    await movie_night.async_activate()

.. note::
    Recording has been verified against a real plant with actions
    performed via **physical switches**. Actions sent through the API
    while recording are expected to be captured as well — the official
    CAME app records its own commands this way — but this has not been
    verified yet.

:meth:`~aiocamedomotic.CameDomoticAPI.async_stop_scenario_recording`
identifies the new scenario by the name passed to
:meth:`~aiocamedomotic.CameDomoticAPI.async_start_scenario_recording`
and returns ``None`` if it cannot be found (e.g. when finalizing a
recording started by another client).

**Renaming and deleting custom scenarios:**

User-defined scenarios (``user_defined == 1``) can be renamed and
deleted. System-defined scenarios are not meant to be modified: the
command is sent anyway, but a warning is logged and the server behaviour
is unverified.

.. code-block:: python

    scenarios = await api.async_get_scenarios()
    movie_night = next(
        (s for s in scenarios if s.name == "Movie night" and s.user_defined),
        None,
    )

    if movie_night:
        # Rename the scenario (the local object is updated too)
        await movie_night.async_rename("Cinema mode")

        # Delete the scenario (irreversible!)
        await movie_night.async_delete()

Thermoregulation zones
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    zones = await api.async_get_thermo_zones()

    for zone in zones:
        print(
            f"ID: {zone.act_id}, Name: {zone.name}, "
            f"Temperature: {zone.temperature}°C, "
            f"Setpoint: {zone.set_point}°C, "
            f"Mode: {zone.mode}, Season: {zone.season}"
        )

Example output:

.. code-block:: text

    ID: 1, Name: Living Room, Temperature: 20.0°C, Setpoint: 21.5°C, Mode: ThermoZoneMode.AUTO, Season: ThermoZoneSeason.WINTER
    ID: 52, Name: Bedroom, Temperature: 19.5°C, Setpoint: 20.0°C, Mode: ThermoZoneMode.MANUAL, Season: ThermoZoneSeason.WINTER

**Controlling thermoregulation zones:**

.. code-block:: python

    from aiocamedomotic.models import ThermoZoneFanSpeed, ThermoZoneMode, ThermoZoneSeason

    # Set target temperature (keeps current mode).
    # Only effective when the zone is in MANUAL mode; in AUTO or other modes
    # the server silently discards the new setpoint without returning an error.
    zone = zones[0]
    await zone.async_set_temperature(22.0)

    # To guarantee a setpoint change regardless of the current mode, switch to
    # MANUAL and set the temperature in a single call:
    await zone.async_set_config(mode=ThermoZoneMode.MANUAL, set_point=22.0)

    # Change operating mode (keeps current temperature)
    await zone.async_set_mode(ThermoZoneMode.MANUAL)

    # Full configuration with fan speed
    await zone.async_set_config(
        mode=ThermoZoneMode.MANUAL,
        set_point=21.5,
        fan_speed=ThermoZoneFanSpeed.MEDIUM,
    )

    # Set fan speed (keeps current mode and temperature)
    await zone.async_set_fan_speed(ThermoZoneFanSpeed.SLOW)

    # Change global season for all zones (plant-level command — season cannot
    # be changed per zone)
    await api.async_set_thermo_season(ThermoZoneSeason.WINTER)

.. warning::
    **Setting the season to** ``PLANT_OFF`` **forces all zones to** ``OFF``.

    When the season is set to ``PLANT_OFF``, the CAME server automatically
    switches every thermoregulation zone to ``ThermoZoneMode.OFF``. Reverting
    the season back to ``WINTER`` or ``SUMMER`` does **not** restore the
    previous zone modes — each zone stays ``OFF`` until its mode is changed
    manually (e.g. via ``async_set_mode()`` or ``async_set_config()``).

    If your application needs to restore zone operation after re-enabling a
    season, you must track each zone's previous mode yourself and re-apply it
    after changing the season.

.. note::
    Temperature values are returned as floats in degrees Celsius.

    The ``fan_speed`` parameter in ``async_set_config`` is optional; when
    provided, the ``extended_infos`` flag is set automatically.

    Season can only be changed at the plant level via ``async_set_thermo_season()``.

Weekly setpoint profile
"""""""""""""""""""""""

Each thermo zone carries a weekly schedule that selects, hour by hour, which
of the **five setpoint levels** shown in the official CAME app is active.
The ``profile`` property exposes it as a typed
:class:`~aiocamedomotic.models.ThermoProfile` object with **8 rows**:
Monday through Sunday, plus the special **JOLLY** profile (the schedule used
while the zone is in ``ThermoZoneMode.JOLLY``) as the 8th row.

Rows are addressed with :class:`~aiocamedomotic.models.ProfileDay`, whose
``MONDAY``..``SUNDAY`` values (0-6) match ``datetime.date.weekday()``, so
``ProfileDay(some_date.weekday())`` always picks the right row.

**Reading the profile:**

.. code-block:: python

    from datetime import datetime, time
    from aiocamedomotic.models import ProfileDay

    zones = await api.async_get_thermo_zones()
    zone = next((z for z in zones if z.name == "Office"), None)
    profile = zone.profile

    # Level active on a given day at a given moment
    print(profile.level_at(ProfileDay.MONDAY, 8))            # int hour (0-23)
    print(profile.level_at(ProfileDay.MONDAY, time(6, 30)))  # any time of day

    # Level active right now
    now = datetime.now()
    print(profile.level_at(ProfileDay(now.weekday()), now))

    # The JOLLY row is addressed like a day
    print(profile.level_at(ProfileDay.JOLLY, 12))

**Viewing a day as time spans:**

``spans()`` returns a day's schedule as runs of consecutive equal levels —
handy for displaying the schedule the way the official app draws it:

.. code-block:: python

    for span in profile.spans(ProfileDay.MONDAY):
        print(f"{span.start} - {span.end}: level {span.level}")

Example output:

.. code-block:: text

    00:00:00 - 08:00:00: level 1
    08:00:00 - 09:00:00: level 4
    09:00:00 - 15:00:00: level 3
    15:00:00 - 00:00:00: level 1

Each span is a half-open ``[start, end)`` range; the last span's ``end`` of
``00:00`` means "through midnight".

The ``profile_data`` property exposes the same schedule in raw wire format:
8 strings of 96 characters (one per quarter hour of day), each character a
digit ``1``-``5``. The official app edits profiles per hour, so the four
quarters within an hour normally share the same level; the typed API speaks
in hours only.

.. note::
    Thermo profiles are currently **read-only**: the command the official
    app uses to write them has not been mapped yet, so the library cannot
    send an edited thermo profile back to the server. The editing methods
    described in :ref:`loadsctrl-weekly-profile` work on ``ThermoProfile``
    objects too (with one extra option: pass
    ``days=aiocamedomotic.models.WEEKDAYS`` to target Monday..Sunday while
    leaving the JOLLY row untouched, since ``days=None`` targets all 8
    rows), but the result can only be used locally.

    Zone objects returned by ``async_get_thermo_zones()`` always carry the
    profile; ``ThermoZoneUpdate`` push updates do **not** include it, so
    read profiles from the zone list, not from updates.

Analog sensors
^^^^^^^^^^^^^^

Analog sensors provide top-level readings (temperature, humidity, pressure)
from the thermoregulation system. Each sensor carries an ``AnalogSensorType``
that identifies the kind of measurement it represents.

**Fetching and inspecting sensors:**

.. code-block:: python

    from aiocamedomotic.models import AnalogSensorType

    sensors = await api.async_get_analog_sensors()

    for sensor in sensors:
        print(
            f"Name: {sensor.name}, Type: {sensor.sensor_type}, "
            f"Value: {sensor.value}, Unit: {sensor.unit}"
        )

Example output:

.. code-block:: text

    Name: Outdoor Temperature, Type: AnalogSensorType.TEMPERATURE, Value: 21.5, Unit: C
    Name: Indoor Humidity, Type: AnalogSensorType.HUMIDITY, Value: 55, Unit: %
    Name: Barometric Pressure, Type: AnalogSensorType.PRESSURE, Value: 1013, Unit: hPa

**Filtering by sensor type:**

.. code-block:: python

    # Get only temperature sensors
    temp_sensors = [
        s for s in sensors if s.sensor_type == AnalogSensorType.TEMPERATURE
    ]
    for s in temp_sensors:
        print(f"{s.name}: {s.value}°{s.unit}")

    # Find a specific sensor by ID
    outdoor = next((s for s in sensors if s.act_id == 100), None)

Digital inputs (binary sensors)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Digital inputs are read-only binary sensors such as physical buttons or
contact sensors. They report their state (ACTIVE/IDLE) but cannot be
controlled remotely. ``ACTIVE`` means the input is triggered (e.g. a button
is being pressed); ``IDLE`` means the input is in its normal resting state.

.. code-block:: python

    from aiocamedomotic.models import DigitalInputStatus

    digital_inputs = await api.async_get_digital_inputs()

    for di in digital_inputs:
        print(
            f"ID: {di.act_id}, Name: {di.name}, "
            f"Status: {di.status}, Address: {di.addr}"
        )

Example output:

.. code-block:: text

    ID: 0, Name: digitalin_PvGCT, Status: DigitalInputStatus.UNKNOWN, Address: 200
    ID: 1, Name: digitalin_BuTbB, Status: DigitalInputStatus.IDLE, Address: 201

**Finding a specific digital input:**

.. code-block:: python

    # By ID
    button = next((di for di in digital_inputs if di.act_id == 1), None)

    # By name
    sensor = next((di for di in digital_inputs if di.name == "Front door button"), None)

.. note::
    Some digital inputs do not report a ``status`` until their first state
    change. In that case, ``status`` returns ``DigitalInputStatus.UNKNOWN``.

Analog inputs (standalone sensors)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analog inputs are read-only standalone sensors exposed via the ``analogin`` feature.
They provide a numeric reading and a unit of measurement and cannot be
controlled remotely.

.. note::
    These sensors are independent of the thermoregulation system's
    :class:`~aiocamedomotic.models.AnalogSensor`. The same physical sensor
    may appear in both endpoints.

.. code-block:: python

    if ServerFeature.ANALOGIN in server_info.features:
        analog_inputs = await api.async_get_analog_inputs()

        for ai in analog_inputs:
            print(
                f"ID: {ai.act_id}, Name: {ai.name}, "
                f"Value: {ai.value}, Unit: {ai.unit}"
            )

Example output:

.. code-block:: text

    ID: 89, Name: Hygrometer, Value: 47.0, Unit: %
    ID: 90, Name: Outdoor Thermometer, Value: 21.5, Unit: C
    ID: 91, Name: Barometer, Value: 1013.0, Unit: hPa

**Finding a specific analog input:**

.. code-block:: python

    # By ID
    thermo = next((ai for ai in analog_inputs if ai.act_id == 90), None)

    # By name
    hygro = next((ai for ai in analog_inputs if ai.name == "Hygrometer"), None)

Relays
^^^^^^

Relays are simple on/off switches that can be controlled remotely.

**Fetching and inspecting relays:**

.. code-block:: python

    from aiocamedomotic.models import RelayStatus

    relays = await api.async_get_relays()

    for relay in relays:
        print(f"ID: {relay.act_id}, Name: {relay.name}, Status: {relay.status}")

Example output:

.. code-block:: text

    ID: 31, Name: Garden Pump, Status: RelayStatus.ON
    ID: 32, Name: Gate Motor, Status: RelayStatus.OFF

**Finding a specific relay:**

.. code-block:: python

    # By ID
    pump = next((r for r in relays if r.act_id == 31), None)

    # By name
    gate = next((r for r in relays if r.name == "Gate Motor"), None)

**Controlling relays:**

.. code-block:: python

    if pump:
        await pump.async_set_status(RelayStatus.ON)
        await asyncio.sleep(5)
        await pump.async_set_status(RelayStatus.OFF)

Timers
^^^^^^

Timers are scheduling entities that define time-based activation windows for
associated devices. Each timer has an enabled/disabled state, a day-of-week
schedule, and up to 4 time slots. Timers support remote control: you can
enable/disable them, toggle individual days, and configure the timetable.

**Fetching and inspecting timers:**

.. code-block:: python

    timers = await api.async_get_timers()

    for timer in timers:
        print(
            f"ID: {timer.id}, Name: {timer.name}, "
            f"Enabled: {timer.enabled}, "
            f"Days: {timer.active_days}"
        )

        for slot in timer.timetable:
            print(
                f"  Slot {slot.index}: "
                f"start={slot.start_hour:02d}:{slot.start_min:02d}:{slot.start_sec:02d}"
            )

Example output:

.. code-block:: text

    ID: 163, Name: Test timer, Enabled: True, Days: ['Monday', 'Wednesday', 'Friday']
      Slot 0: start=10:00:00
    ID: 164, Name: Timer 2, Enabled: True, Days: ['Tuesday', 'Thursday', 'Sunday']
      Slot 1: start=12:00:00
      Slot 2: start=11:00:00

**Finding a specific timer:**

.. code-block:: python

    # By ID
    my_timer = next((t for t in timers if t.id == 163), None)

    # By name
    irrigation = next((t for t in timers if t.name == "Irrigation"), None)

Understanding the days bitmask
""""""""""""""""""""""""""""""

The ``days`` property is a 7-bit integer bitmask where each bit represents a
day of the week. Bit 0 is Monday, bit 6 is Sunday:

.. code-block:: text

    Bit:   6    5    4    3    2    1    0
    Day:  Sun  Sat  Fri  Thu  Wed  Tue  Mon

Common values:

- ``1`` — Monday only
- ``15`` — Monday through Thursday (1+2+4+8)
- ``31`` — Monday through Friday (weekdays)
- ``96`` — Saturday and Sunday (weekend)
- ``127`` — every day

The ``active_days`` property returns a human-readable list, and
``is_active_on_day()`` checks a specific day:

.. code-block:: python

    timer = timers[0]

    print(timer.days)                    # 21
    print(timer.active_days)             # ['Monday', 'Wednesday', 'Friday']
    print(timer.is_active_on_day(0))     # True  (Monday)
    print(timer.is_active_on_day(1))     # False (Tuesday)

Understanding the timetable
"""""""""""""""""""""""""""

Each timer has up to **4 time slots** (indices 0--3). The ``timetable``
property returns a list of :class:`~aiocamedomotic.models.timer.TimerTimeSlot`
objects for the slots that are currently configured. Empty slots are simply
absent from the list.

Each ``TimerTimeSlot`` exposes:

- ``index`` — the slot position (0--3)
- ``start_hour``, ``start_min``, ``start_sec`` — the activation start time
- ``stop_hour``, ``stop_min``, ``stop_sec`` — the stop time (``None`` on
  some firmware versions)
- ``active`` — whether the slot is individually active (``None`` on some
  firmware versions)

.. code-block:: python

    for slot in timer.timetable:
        start = f"{slot.start_hour:02d}:{slot.start_min:02d}:{slot.start_sec:02d}"
        if slot.stop_hour is not None:
            stop = f"{slot.stop_hour:02d}:{slot.stop_min:02d}:{slot.stop_sec:02d}"
        else:
            stop = "N/A"
        print(f"  Slot {slot.index}: {start} → {stop}")

Example output:

.. code-block:: text

      Slot 0: 10:00:00 → 18:30:00
      Slot 2: 22:00:00 → N/A

.. note::
    The ``stop`` and ``active`` fields may not be
    present in the server response. The corresponding properties return
    ``None`` in that case. Your code should handle both cases.

Enabling and disabling timers
"""""""""""""""""""""""""""""

Toggle a timer's global enabled state:

.. code-block:: python

    timer = timers[0]

    # Disable the timer
    await timer.async_disable()
    print(timer.enabled)  # False

    # Re-enable the timer
    await timer.async_enable()
    print(timer.enabled)  # True

Toggling days of the week
"""""""""""""""""""""""""

Add or remove individual days from the timer's schedule. The ``day``
parameter is a zero-based index: 0 = Monday, 6 = Sunday.

.. code-block:: python

    # Enable Sunday (day index 6)
    await timer.async_enable_day(6)
    print(timer.active_days)  # [..., 'Sunday']

    # Disable Friday (day index 4)
    await timer.async_disable_day(4)
    print(timer.is_active_on_day(4))  # False

Setting the timetable
"""""""""""""""""""""

Use ``async_set_timetable()`` to configure all 4 time slots at once. Pass a
list of exactly 4 entries — each is either a ``(hour, minute, second)`` tuple
for an active slot, or ``None`` for an empty slot:

.. code-block:: python

    # Set slot 0 to 06:30:00, slot 2 to 22:00:00, leave slots 1 and 3 empty
    await timer.async_set_timetable([
        (6, 30, 0),     # slot 0
        None,           # slot 1 (empty)
        (22, 0, 0),     # slot 2
        None,           # slot 3 (empty)
    ])

    # Verify
    for slot in timer.timetable:
        print(f"  Slot {slot.index}: {slot.start_hour:02d}:{slot.start_min:02d}")

    # Clear all slots
    await timer.async_set_timetable([None, None, None, None])

.. important::
    ``async_set_timetable()`` always sends **all 4 slots** to the server.
    To keep existing slots unchanged, read the current timetable first and
    merge your changes:

    .. code-block:: python

        # Read current slots into a 4-element list
        current: list[tuple[int, int, int] | None] = [None, None, None, None]
        for slot in timer.timetable:
            current[slot.index] = (slot.start_hour, slot.start_min, slot.start_sec)

        # Modify only slot 3
        current[3] = (14, 30, 0)

        # Send the merged timetable
        await timer.async_set_timetable(current)

Complete timer example
""""""""""""""""""""""

This example fetches timers, prints their configuration, toggles the enabled
state, adds a day, sets a time slot, and reverts everything:

.. code-block:: python

    import asyncio
    from aiocamedomotic import CameDomoticAPI

    async def main():
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:
            timers = await api.async_get_timers()
            if not timers:
                print("No timers found")
                return

            timer = timers[0]
            print(f"Timer: {timer.name} (ID: {timer.id})")
            print(f"  Enabled: {timer.enabled}")
            print(f"  Days: {timer.active_days}")
            print(f"  Slots: {len(timer.timetable)}")

            # Save original state
            was_enabled = timer.enabled
            had_sunday = timer.is_active_on_day(6)

            # Toggle enabled
            if was_enabled:
                await timer.async_disable()
            else:
                await timer.async_enable()
            print(f"  Enabled toggled to: {timer.enabled}")

            # Toggle Sunday
            if had_sunday:
                await timer.async_disable_day(6)
            else:
                await timer.async_enable_day(6)
            print(f"  Days now: {timer.active_days}")

            # Add a time slot
            current: list[tuple[int, int, int] | None] = [None] * 4
            for slot in timer.timetable:
                current[slot.index] = (
                    slot.start_hour, slot.start_min, slot.start_sec
                )
            current[3] = (14, 30, 0)
            await timer.async_set_timetable(current)
            print(f"  Slots after adding slot 3: {len(timer.timetable)}")

            # Revert everything
            current[3] = None
            await timer.async_set_timetable(current)
            if had_sunday:
                await timer.async_enable_day(6)
            else:
                await timer.async_disable_day(6)
            if was_enabled:
                await timer.async_enable()
            else:
                await timer.async_disable()
            print("  Reverted to original state")

    asyncio.run(main())

Energy meters
^^^^^^^^^^^^^

Energy meters are read-only sensors exposed via the ``energy`` feature. They
report the instantaneous power measured on a line (e.g. the whole-home
consumption) together with energy values. Unlike lights or
openings, energy meters are **plant-level entities keyed by** ``id``: they
have no ``act_id`` and no floor/room placement. The number of meters and
their names are entirely plant-specific — always discover them via the API.

**Fetching and inspecting energy meters:**

.. code-block:: python

    meters = await api.async_get_energy_meters()

    for meter in meters:
        print(f"ID: {meter.id}, Name: {meter.name}, "
              f"Power: {meter.instant_power} {meter.unit}")

Example output:

.. code-block:: text

    ID: 4, Name: Consumed Energy, Power: 595 W
    ID: 3, Name: Line 1 + Line 2, Power: 595 W

**Finding a specific energy meter:**

.. code-block:: python

    # By ID
    main_meter = next((m for m in meters if m.id == 4), None)

    # By name
    consumption = next((m for m in meters if m.name == "Consumed Energy"), None)

**Reading the energy values:**

Each meter also exposes the raw ``last_24h_avg`` and ``last_month_avg``
fields, expressed in ``energy_unit`` (typically ``Wh``):

.. code-block:: python

    if main_meter:
        print(f"last_24h_avg: {main_meter.last_24h_avg} {main_meter.energy_unit}")
        print(f"last_month_avg: {main_meter.last_month_avg} {main_meter.energy_unit}")

Real-time power readings are delivered as push updates — see
:ref:`energy-meter-updates` in the monitoring section below.

**Resetting the energy history:**

The stored energy history can be cleared with a single plant-level
command. The reset applies to **all** energy meters at once (it cannot
target a single meter) and is **irreversible**; instantaneous power
readings are not affected:

.. code-block:: python

    await api.async_reset_energy_counters()

Loads control
^^^^^^^^^^^^^

The ``loadsctrl`` feature implements **load shedding**: a loads
**controller** (:class:`~aiocamedomotic.models.LoadsCtrlMeter`) watches an
energy meter and, when consumption exceeds its ``max_power`` threshold
(with a ``hysteresis`` band around it to avoid flapping), it *detaches*
its **managed loads** (:class:`~aiocamedomotic.models.LoadsCtrlRelay`) —
typically high-consumption appliances — one at a time until consumption
drops below the threshold again.

The order in which loads are shed is defined by each load's ``priority``
value: **the lower the priority value, the earlier the load is detached**.
Keep this direction in mind throughout this section — your most expendable
appliance should have the *lowest* priority value.

.. note::
    The number and names of controllers and loads are **entirely
    plant-specific**: another plant may have any number of loads (including
    zero) with arbitrary user-defined names. Never hard-code load names or
    counts — always discover them via the API, as shown below.

**Fetching the loads controllers:**

.. code-block:: python

    controllers = await api.async_get_loadsctrl_meters()

    for ctrl in controllers:
        print(
            f"ID: {ctrl.id}, Name: {ctrl.name}, "
            f"Max power: {ctrl.max_power} W, "
            f"Hysteresis: {ctrl.hysteresis} W, "
            f"Current power: {ctrl.power} W, "
            f"Energy meter ID: {ctrl.meter_id}"
        )

Example output:

.. code-block:: text

    ID: 196612, Name: Consumed Energy, Max power: 5000 W, Hysteresis: 400 W, Current power: 595 W, Energy meter ID: 4

The controller's ``meter_id`` is the ``id`` of the energy meter it watches
(see the `Energy meters`_ section above); the controller's own ``id`` is a
separate, opaque value.

**Fetching the managed loads:**

The examples below reuse the ``controllers`` list fetched above. Get the
loads managed by a controller with ``async_get_relays()``, and sort them by
``priority`` to display the detach order (first row = first load shed):

.. code-block:: python

    if not controllers:
        print("No loads controller on this plant")
    else:
        ctrl = controllers[0]
        relays = sorted(await ctrl.async_get_relays(), key=lambda r: r.priority)

        for relay in relays:
            print(
                f"Priority: {relay.priority}, Name: {relay.name}, "
                f"Enabled: {relay.enabled}, Detached: {relay.detached}, "
                f"Status: {relay.status}"
            )

Example output:

.. code-block:: text

    Priority: 129, Name: Washing machine, Enabled: False, Detached: False, Status: LoadsCtrlRelayStatus.ON
    Priority: 130, Name: Dishwasher, Enabled: True, Detached: False, Status: LoadsCtrlRelayStatus.ON
    Priority: 131, Name: Air conditioner, Enabled: False, Detached: False, Status: LoadsCtrlRelayStatus.ON
    Priority: 132, Name: Tumble dryer, Enabled: False, Detached: False, Status: LoadsCtrlRelayStatus.OFF

``detached`` tells you whether the controller has currently shed the load,
and ``status`` is the read-only relay output state (there is no loadsctrl
command to switch the relay itself).

**Finding a specific load:**

.. code-block:: python

    # By ID
    washer = next((r for r in relays if r.id == 65600), None)

    # By name
    dryer = next((r for r in relays if r.name == "Tumble dryer"), None)

**Enabling or disabling a load:**

A load participates in load shedding only while it is *enabled* — this is
the per-appliance toggle you see in the official CAME app. Disabling a load
means the controller will never detach it, regardless of priority:

.. code-block:: python

    if washer:
        await washer.async_set_enabled(True)   # controller may shed it
        await washer.async_set_enabled(False)  # controller leaves it alone

**Changing a single load's priority:**

Use ``async_set_priority()`` to move one load within the detach order.
Remember the direction: a *lower* value means the load is shed *earlier*.
The wire command always carries both fields, so the current ``enabled``
flag is re-sent automatically alongside the new priority:

.. code-block:: python

    if washer:
        await washer.async_set_priority(130)

**Reordering the whole detach order:**

To rewrite the full shedding sequence in one call, build the desired order
(first element = first load shed) and pass it to
``async_set_detach_order()``. The method reuses the priority values already
present on the plant, reassigning them in ascending order to your sequence:

.. code-block:: python

    # Current order: washer, dishwasher, air conditioner, dryer.
    # Make the dishwasher the first load to shed, then the washer:
    by_name = {r.name: r for r in relays}
    await ctrl.async_set_detach_order([
        by_name["Dishwasher"],
        by_name["Washing machine"],
        by_name["Air conditioner"],
        by_name["Tumble dryer"],
    ])

.. note::
    ``async_set_detach_order()`` writes **only the relays whose priority
    actually changes** (the official app does the same), so a no-op reorder
    sends no set commands. It raises ``ValueError`` if the sequence is not
    a permutation of the controller's relays (same IDs, no duplicates).
    The method is not atomic (one set command per changed relay), but it
    is **safe to retry**: if a call fails partway through and leaves two
    relays sharing a priority value, calling it again repairs the
    duplicates into a strictly increasing sequence and converges to the
    requested order.

**Updating the controller configuration:**

``async_set_config()`` changes the overload threshold (``max_power``)
and/or the ``hysteresis``. Unspecified values are re-sent unchanged, since
the wire command requires the full configuration on every write:

.. code-block:: python

    await ctrl.async_set_config(max_power=4500)
    await ctrl.async_set_config(max_power=5000, hysteresis=300)

Configuration writes and load changes are echoed back as push updates —
see :ref:`loadsctrl-updates` in the monitoring section below.

.. _loadsctrl-weekly-profile:

Weekly threshold profile
""""""""""""""""""""""""

Besides the fixed ``max_power`` value, each controller carries a weekly
schedule that selects, hour by hour, which of the **five threshold levels**
shown in the official CAME app is active (each level is a fraction of
``max_power``). The ``profile`` property exposes it as a typed
:class:`~aiocamedomotic.models.LoadsCtrlProfile` object with 7 rows
(Monday through Sunday) of 24 hourly slots, each set to a level ``1``-``5``.

**Reading the profile:**

.. code-block:: python

    from aiocamedomotic.models import ProfileDay

    profile = ctrl.profile

    # Level active on Monday at 08:00
    print(profile.level_at(ProfileDay.MONDAY, 8))

    # A day's schedule as runs of consecutive equal levels
    for span in profile.spans(ProfileDay.MONDAY):
        print(f"{span.start} - {span.end}: level {span.level}")

Example output:

.. code-block:: text

    4
    00:00:00 - 00:00:00: level 4

Here the whole day runs at level 4, so there is a single span covering the
full day: spans are half-open ``[start, end)`` ranges, and an ``end`` of
``00:00`` means "through midnight". (The ``profile_data`` property exposes
the same schedule in raw wire format: 7 strings of 24 hourly digits.)

**Editing the profile:**

Profiles are **immutable value objects**: every editing method returns a
*new* profile and leaves the original untouched, so nothing reaches the
server until you explicitly write the result back with
``async_set_config()``. Edits are hour-based (``start`` inclusive, ``end``
exclusive), matching how the official app edits profiles:

.. code-block:: python

    from aiocamedomotic.models import LoadsCtrlProfile, ProfileDay

    # Level 2 on Monday from 08:00 to 12:00
    edited = profile.with_level(2, days=ProfileDay.MONDAY, start=8, end=12)

    # Level 1 every day from 22:00 through midnight
    # (days omitted → all days; end omitted → end of day)
    edited = edited.with_level(1, start=22)

    # Copy Monday's whole schedule onto the weekend
    edited = edited.with_day_copied(
        ProfileDay.MONDAY, to=[ProfileDay.SATURDAY, ProfileDay.SUNDAY]
    )

    # Or start from scratch: every hour of every day at level 5
    flat = LoadsCtrlProfile.constant(5)

Spans that cross midnight must be split into two calls (e.g. 22:00-06:00 is
``with_level(1, start=22)`` on one day plus ``with_level(1, end=6)`` on the
next).

**Writing the profile back:**

Pass the edited profile to ``async_set_config()`` — alone or together with
``max_power``/``hysteresis``. As with the other configuration values, the
accepted state is echoed back as a ``loadsctrl_meter_ind`` push update:

.. code-block:: python

    await ctrl.async_set_config(profile_data=edited)

    # Re-fetch to confirm the server state
    ctrl = (await api.async_get_loadsctrl_meters())[0]
    print(ctrl.profile == edited)  # True

.. note::
    ``profile_data`` accepts a ``LoadsCtrlProfile`` object only (typically
    obtained from ``ctrl.profile`` and edited), not raw digit strings — to
    send a raw server-captured value, parse it first with
    ``LoadsCtrlProfile.from_wire(raw_list)``. Profiles compare by value, so
    two profiles with the same grid are equal regardless of how they were
    built.

Map pages
^^^^^^^^^

Map pages are the floor-plan views configured in the official CAME app: each
page is a background image with positioned device elements (lights, openings,
thermostats, scenarios, links to other pages) laid on top. Maps are
**read-only** — they provide positional information for building a visual UI,
while device control always goes through the standard device APIs shown in
the previous sections.

**Fetching and inspecting map pages:**

.. code-block:: python

    pages = await api.async_get_map_pages()

    for page in pages:
        print(
            f"Page {page.page_id}: {page.page_label} "
            f"(elements: {len(page.elements)}, background: {page.background})"
        )

Example output:

.. code-block:: text

    Page 0: Home (elements: 3, background: maps/maps_home.png)
    Page 1: Ground Floor (elements: 12, background: maps/maps_ground floor.png)
    Page 2: First Floor (elements: 8, background: maps/maps_first floor.png)

Page ``0`` is the root/home page. The ``background`` property is the
relative URL path of the background image on the CAME server (full URL:
``http://<server_host>/<background>``); the path may contain spaces, so
percent-encode it before making HTTP requests.

Elements are raw dictionaries preserving the server response structure, with
common keys such as ``x``, ``y``, ``width``, ``height``, ``type``, and
``label``; additional keys depend on the element type (e.g. ``act_id`` for
devices, ``page`` for page links, ``scenario_id`` for scenarios). The
``x``/``y`` coordinates range from ``0`` to ``page_scale`` (typically
``1024``):

.. code-block:: python

    ground_floor = next((p for p in pages if p.page_label == "Ground Floor"), None)
    if ground_floor:
        for element in ground_floor.elements:
            print(
                f"  {element.get('type')} '{element.get('label')}' "
                f"at ({element.get('x')}, {element.get('y')})"
            )


Monitoring real-time updates
----------------------------

The CAME Domotic server supports **long polling** for real-time status updates.
When you call ``async_get_updates()``, the request **blocks on the server**
until one or more device state changes are detected, then returns an
:class:`~aiocamedomotic.models.update.UpdateList` containing all pending
updates. This is the recommended mechanism for monitoring devices in real time
without repeatedly fetching full device lists.

Basic polling loop
^^^^^^^^^^^^^^^^^^

A typical polling loop continuously calls ``async_get_updates()`` and
processes each batch of updates as it arrives:

.. code-block:: python

    import asyncio
    from aiocamedomotic.errors import CameDomoticServerTimeoutError

    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password"
    ) as api:
        while True:
            try:
                updates = await api.async_get_updates(timeout=120)
            except CameDomoticServerTimeoutError:
                # Long poll timed out with no updates; simply retry
                continue

            for update in updates.get_typed_updates():
                print(f"[{update.device_type.name}] {update.name} (ID: {update.device_id})")

            # Brief pause to avoid tight looping on rapid server responses
            await asyncio.sleep(1)

Example output:

.. code-block:: text

    [LIGHT] Living Room Chandelier (ID: 1)
    [OPENING] Bedroom Shutter (ID: 10)
    [THERMOSTAT] Living Room (ID: 1)

.. note::
    The ``asyncio.sleep(1)`` acts as a safety throttle in case the server
    returns immediately (e.g. errors or rapid update bursts). If you need to
    run the polling loop alongside other logic, wrap it in
    ``asyncio.create_task()``.

Configuring timeouts
^^^^^^^^^^^^^^^^^^^^

All API methods use a default timeout of **30 seconds**, configurable via
the ``command_timeout`` parameter when creating the API instance:

.. code-block:: python

    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password", command_timeout=15
    ) as api:
        lights = await api.async_get_lights()  # uses 15s timeout

``async_get_updates()`` is the only method that accepts its own ``timeout``
parameter, allowing it to use a different timeout than the rest of the API.
This is because ``async_get_updates()`` uses **long polling** — the server
holds the connection open until updates are available, which can take
much longer than a regular command round-trip. A longer timeout
(e.g. 60--120 seconds) is **strongly recommended** to avoid premature
disconnections:

.. code-block:: python

    # Instance-level timeout is 15s for regular commands,
    # but async_get_updates uses its own 120s timeout
    updates = await api.async_get_updates(timeout=120)

.. note::
    If no ``timeout`` is passed to ``async_get_updates()``, it falls back to
    the instance-level ``command_timeout`` (default: 30s). For most real-time
    monitoring use cases, a timeout of **60--120 seconds** is recommended.

Typed updates and filtering
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``UpdateList`` supports iteration over raw dicts for backward
compatibility. For **typed** update objects with convenient properties, use
``get_typed_updates()`` or filter by device type with
``get_typed_by_device_type()``:

.. code-block:: python

    updates = await api.async_get_updates()

    # Filter by device type
    light_updates = updates.get_typed_by_device_type(DeviceType.LIGHT)
    for light in light_updates:
        print(
            f"Light '{light.name}': status={light.status}, "
            f"type={light.light_type}, brightness={light.perc}%"
        )

    # Dispatch by update type using isinstance
    for update in updates.get_typed_updates():
        if isinstance(update, LightUpdate):
            print(f"Light '{update.name}': {update.status.name}, brightness={update.perc}%")

        elif isinstance(update, OpeningUpdate):
            print(f"Opening '{update.name}': {update.status.name}")

        elif isinstance(update, ThermoZoneUpdate):
            print(
                f"Thermo '{update.name}': {update.temperature}°C, "
                f"setpoint={update.set_point}°C, mode={update.mode.name}"
            )

        elif isinstance(update, ScenarioUpdate):
            print(f"Scenario '{update.name}': {update.scenario_status.name}")

        elif isinstance(update, DigitalInputUpdate):
            print(f"Input '{update.name}': status={update.status}, addr={update.addr}")

        elif isinstance(update, AnalogInUpdate):
            print(f"Analog input '{update.name}': {update.value} {update.unit}")

        elif isinstance(update, RelayUpdate):
            print(f"Relay '{update.name}': {update.status.name}")

        elif isinstance(update, TimerUpdate):
            print(
                f"Timer '{update.name}': enabled={update.enabled}, "
                f"days={update.days}, slots={len(update.timetable)}"
            )

        elif isinstance(update, EnergyMeterUpdate):
            print(f"Meter '{update.name}': {update.instant_power} {update.unit}")

        elif isinstance(update, LoadsCtrlRelayUpdate):
            print(
                f"Load '{update.name}': enabled={update.enabled}, "
                f"priority={update.priority}, detached={update.detached}"
            )

        elif isinstance(update, LoadsCtrlMeterUpdate):
            print(
                f"Loads controller '{update.name}': "
                f"max_power={update.max_power} W, hysteresis={update.hysteresis} W"
            )

        elif isinstance(update, PlantUpdate):
            print("Plant configuration changed, re-fetching devices...")

Handling plant updates
^^^^^^^^^^^^^^^^^^^^^^

A ``plant_update_ind`` signals that the **device configuration on the server
has changed** (e.g. devices were added, removed, or reconfigured). When this
happens, all locally cached device lists must be discarded and re-fetched:

.. code-block:: python

    updates = await api.async_get_updates()

    if updates.has_plant_update:
        lights = await api.async_get_lights()
        openings = await api.async_get_openings()
        relays = await api.async_get_relays()
        scenarios = await api.async_get_scenarios()
        timers = await api.async_get_timers()
        thermo_zones = await api.async_get_thermo_zones()
        sensors = await api.async_get_analog_sensors()
        digital_inputs = await api.async_get_digital_inputs()

.. note::
    Plant updates are relatively rare. They typically occur when an installer
    modifies the system configuration. Failing to handle them may result in
    stale device data or missing newly added devices.

Timer status updates
^^^^^^^^^^^^^^^^^^^^

When a timer is modified (enabled/disabled, day toggled, timetable changed),
the server sends a ``timer_info_ind`` status update containing the **full
current state** of the affected timer. This happens regardless of whether the
change was made through this library, the CAME app, or the physical panel.

The update payload mirrors the timer list response — it includes ``name``,
``id``, ``enabled``, ``days``, ``bars`` (the number of timetable slots
reported by the server), and the complete ``timetable`` array. The library parses this into a
:class:`~aiocamedomotic.models.update.TimerUpdate` object.

**Applying timer updates to cached objects:**

If you maintain a local cache of ``Timer`` objects, you can update them when
a ``timer_info_ind`` arrives:

.. code-block:: python

    # Assume `timers_cache` is a dict mapping timer ID → Timer object
    timers_cache = {t.id: t for t in await api.async_get_timers()}

    while True:
        try:
            updates = await api.async_get_updates(timeout=120)
        except CameDomoticServerTimeoutError:
            continue

        for update in updates.get_typed_updates():
            if isinstance(update, TimerUpdate):
                cached = timers_cache.get(update.device_id)
                if cached:
                    # Replace the raw_data with the fresh state from the
                    # server — this updates all properties automatically
                    cached.raw_data.update(update.raw_data)
                    print(
                        f"Timer '{cached.name}' updated: "
                        f"enabled={cached.enabled}, "
                        f"days={cached.active_days}, "
                        f"slots={len(cached.timetable)}"
                    )

        await asyncio.sleep(1)

**Sequence of updates during a typical control session:**

When you run a series of timer commands, the server sends one
``timer_info_ind`` for each change. For example, disabling a timer, then
enabling Sunday, then adding a time slot, produces three consecutive
updates:

.. code-block:: text

    timer_info_ind: enabled=0, days=15, timetable=[{index: 0, start: 10:00:00}]
    timer_info_ind: enabled=1, days=79, timetable=[{index: 0, start: 10:00:00}]
    timer_info_ind: enabled=1, days=79, timetable=[{index: 0, ...}, {index: 3, start: 14:30:00}]

Each update is a **complete snapshot** of the timer's state — not a delta.
You can safely overwrite the cached timer data with the update payload
without needing to merge changes.

.. note::
    The ``timer_info_ind`` indication name was confirmed from real server
    traffic (firmware 3.0.1). A legacy variant ``timer_update_ind`` is also
    handled for firmware compatibility.

.. _energy-meter-updates:

Energy meter updates
^^^^^^^^^^^^^^^^^^^^

When the power measured by an energy meter changes, the server pushes a
``meter_instant_power_ind`` indication — one per meter, each containing a
**complete snapshot** of the meter state (the same fields as the meter list
response), with the energy values refreshed in the same push. The library
parses it into an :class:`~aiocamedomotic.models.update.EnergyMeterUpdate`
object whose ``device_id`` is the meter's ``id``.

This is the recommended way to track power consumption in real time,
instead of repeatedly calling ``async_get_energy_meters()``:

.. code-block:: python

    while True:
        try:
            updates = await api.async_get_updates(timeout=120)
        except CameDomoticServerTimeoutError:
            continue

        for update in updates.get_typed_updates():
            if isinstance(update, EnergyMeterUpdate):
                print(
                    f"Meter '{update.name}' (ID: {update.device_id}): "
                    f"{update.instant_power} {update.unit}, "
                    f"last_24h_avg={update.last_24h_avg} {update.energy_unit}"
                )

        await asyncio.sleep(1)

Example output:

.. code-block:: text

    Meter 'Line 1 + Line 2' (ID: 3): 636 W, last_24h_avg=7788947 Wh
    Meter 'Consumed Energy' (ID: 4): 636 W, last_24h_avg=5813290 Wh

.. _loadsctrl-updates:

Loads control updates
^^^^^^^^^^^^^^^^^^^^^

The server pushes a ``loadsctrl_relay_ind`` after **every accepted**
``loadsctrl_relay_set_req`` (enable/disable or priority change), and a
``loadsctrl_meter_ind`` after a controller configuration write. Both carry
a **complete snapshot** of the affected entity, parsed into
:class:`~aiocamedomotic.models.update.LoadsCtrlRelayUpdate` /
:class:`~aiocamedomotic.models.update.LoadsCtrlMeterUpdate`; for both,
``device_id`` is the loadsctrl ``id`` (not the relay's ``act_id``).

.. note::
    **Your own writes are echoed back to you.** These pushes are sent to
    *all* clients — including the one that issued the set command. A
    consumer polling ``async_get_updates()`` must therefore expect to
    receive updates for changes it made itself, and treat the pushed
    snapshot as the authoritative state (which makes it safe to simply
    overwrite any cached data).

.. code-block:: python

    while True:
        try:
            updates = await api.async_get_updates(timeout=120)
        except CameDomoticServerTimeoutError:
            continue

        for update in updates.get_typed_updates():
            if isinstance(update, LoadsCtrlRelayUpdate):
                print(
                    f"Load '{update.name}' (ID: {update.device_id}): "
                    f"enabled={update.enabled}, priority={update.priority}, "
                    f"detached={update.detached}"
                )
            elif isinstance(update, LoadsCtrlMeterUpdate):
                print(
                    f"Controller '{update.name}' (ID: {update.device_id}): "
                    f"max_power={update.max_power} W, "
                    f"hysteresis={update.hysteresis} W, power={update.power} W"
                )

        await asyncio.sleep(1)

Example output (after enabling a load and swapping two priorities):

.. code-block:: text

    Load 'Washing machine' (ID: 65600): enabled=True, priority=129, detached=False
    Load 'Dishwasher' (ID: 65601): enabled=True, priority=129, detached=False
    Load 'Washing machine' (ID: 65600): enabled=True, priority=130, detached=False


Managing users
--------------

The library exposes the same user administration features available in the
official CAME app: listing the users defined on the server, creating and
deleting users, changing passwords, and switching the session to another
user.

Listing users
^^^^^^^^^^^^^

.. code-block:: python

    users = await api.async_get_users()

    for user in users:
        print(f"User: {user.name}")

Example output:

.. code-block:: text

    User: admin
    User: family
    User: guest

Terminal groups
^^^^^^^^^^^^^^^

Terminal groups define the permission scope assigned to users at creation
time. Fetch them with ``async_get_terminal_groups()`` **before** adding a
user, to discover the group names available on your server:

.. code-block:: python

    groups = await api.async_get_terminal_groups()

    for group in groups:
        print(f"Group {group.id}: {group.name}")

Example output:

.. code-block:: text

    Group 1: ETI/Domo

Adding a user
^^^^^^^^^^^^^

Create a new user with ``async_add_user()``. The ``group`` parameter takes a
group **name** (e.g. ``"ETI/Domo"``) as returned by
``async_get_terminal_groups()`` — not its numeric ID. The special value
``"*"`` (the default) may be used when fine-grained group assignment is not
required:

.. code-block:: python

    new_user = await api.async_add_user("family", "s3cret_pwd")

    # Or with an explicit permission group
    new_user = await api.async_add_user("guest", "s3cret_pwd", group="ETI/Domo")

Changing a password
^^^^^^^^^^^^^^^^^^^

Change a user's password with ``async_change_password()`` on the ``User``
object:

.. code-block:: python

    users = await api.async_get_users()
    guest = next((u for u in users if u.name == "guest"), None)

    if guest:
        await guest.async_change_password("old_pwd", "new_pwd")

.. note::
    Changing the password does not invalidate existing active sessions for
    that user — they remain valid until they expire; the new password is
    required at the next login. If the changed user is the currently
    authenticated one, the stored credentials of the active session are
    updated automatically — no additional action is required.

Deleting a user
^^^^^^^^^^^^^^^

Delete a user from the server with ``async_delete()``:

.. code-block:: python

    if guest:
        await guest.async_delete()

The currently authenticated user cannot delete itself: calling
``async_delete()`` on it raises a ``ValueError``.

Switching the session user
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``async_set_as_current_user()`` to log out the current user and continue
the session as another one:

.. code-block:: python

    users = await api.async_get_users()
    admin = next((u for u in users if u.name == "admin"), None)

    if admin:
        await admin.async_set_as_current_user("admin_pwd")

If the login with the new credentials fails, a ``CameDomoticAuthError`` is
raised and the previous credentials are restored, so the API client remains
connected as the original user.


Advanced topics
---------------

Checking authentication status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Session management is automatic and transparent. If you need to inspect the
session status for any reason, use ``is_session_valid()`` on the ``auth``
attribute:

.. code-block:: python

    if api.auth.is_session_valid():
        print("Session is authenticated and valid.")
    else:
        print("No valid session — it will be renewed automatically on the next call.")

.. note::
    You rarely need to call this. The library handles reauthentication
    automatically whenever the session expires.

Device autodiscovery
^^^^^^^^^^^^^^^^^^^^

The library exposes known MAC address OUI prefixes for CAME Domotic devices
via ``CAME_MAC_PREFIXES``. Combined with ``async_is_came_endpoint()``, this
allows identifying CAME ETI/Domo servers on the local network without
credentials:

.. code-block:: python

    from aiocamedomotic import CAME_MAC_PREFIXES, async_is_came_endpoint

    async def async_discover_came_server(host: str, mac_address: str) -> bool:
        """Check if a network device is a CAME Domotic server.

        Args:
            host: IP address or hostname of the device.
            mac_address: MAC address in colon-separated uppercase hex
                format, e.g. "00:1C:B2:AA:BB:CC".
        """
        # Step 1: Quick MAC prefix check (prefixes use "AA:BB:CC" format)
        mac_upper = mac_address.upper()
        if not any(mac_upper.startswith(prefix) for prefix in CAME_MAC_PREFIXES):
            return False

        # Step 2: Verify the device exposes a valid CAME API endpoint
        return await async_is_came_endpoint(host)

.. note::
    ``CAME_MAC_PREFIXES`` contains prefixes in **colon-separated uppercase hex**
    format (e.g. ``"00:1C:B2"``). Make sure the MAC address you pass uses the
    same format (``"00:1C:B2:AA:BB:CC"``) before comparing. Other common
    representations such as ``001cb2aabbcc``, ``00-1C-B2-AA-BB-CC``, or
    lowercase ``00:1c:b2:aa:bb:cc`` will **not** match directly — normalize
    to uppercase colon-separated format first, as shown in the example above.

Debugging with traffic logging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The library includes a built-in traffic logger that records every HTTP
request and response exchanged with the CAME server. **Sensitive data
(passwords, session tokens, server identifiers) is automatically
anonymized**, so the output is safe to share publicly — for example, when
reporting issues on GitHub.

The traffic logger uses the ``aiocamedomotic.traffic`` logger name (a child
of the main ``aiocamedomotic`` logger). Since it is a child logger, it
inherits the handler and formatter already configured by the library — you
only need to lower its level to ``DEBUG``:

.. code-block:: python

    import logging

    # Enable traffic logging (anonymized request/response payloads)
    logging.getLogger("aiocamedomotic.traffic").setLevel(logging.DEBUG)

That single line is all you need. The traffic log messages will appear
alongside the normal library output, using the same format.

Example output:

.. code-block:: text

    2025-03-15 10:23:01.123 DEBUG (MainThread) [aiocamedomotic.traffic] HTTP POST http://192.168.1.***/domo/ [status=200, 42.5ms]
    --> {"sl_cmd":"sl_registration_req","sl_login":"ad***","sl_pwd":"***"}
    <-- {"sl_client_id":"504***","sl_keep_alive_timeout_sec":900,"sl_data_ack_reason":0}

The following fields are redacted automatically:

- ``sl_pwd``, ``sl_new_pwd`` → fully replaced with ``***``
- ``sl_login`` → first 2 characters preserved (e.g. ``ad***``)
- ``sl_client_id``, ``client`` → first 3 characters preserved (e.g. ``504***``)
- ``keycode`` → first 8 characters preserved (e.g. ``61305E97********``)
- ``serial`` → first 3 characters preserved (e.g. ``037***``)
- Camera URIs (``uri``, ``uri_still``) → embedded credentials redacted
- Host IP in the URL → last octet masked (e.g. ``192.168.1.***``)
- Usernames inside ``sl_users_list`` items → partially masked

.. note::
    The traffic logger level is independent from the main library logger.
    Setting ``aiocamedomotic`` to ``WARNING`` and
    ``aiocamedomotic.traffic`` to ``DEBUG`` is a valid configuration —
    you will see only the HTTP traffic, without the library's internal
    debug messages.

.. tip::
    To write the traffic log to a **file** for later analysis, add a
    dedicated ``FileHandler``. Use ``propagate = False`` if you want the
    traffic to go *only* to the file and not to the console:

    .. code-block:: python

        import logging

        traffic_logger = logging.getLogger("aiocamedomotic.traffic")
        traffic_logger.setLevel(logging.DEBUG)
        traffic_logger.addHandler(logging.FileHandler("came_traffic.log"))
        traffic_logger.propagate = False  # file only, no console output

.. seealso::
    For full API details, see the :doc:`api_reference`.
