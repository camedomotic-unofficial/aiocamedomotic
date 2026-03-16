.. Copyright 2024 - GitHub user: fredericks1982

.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at

..     http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

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
            LightType, OpeningStatus, RelayStatus, ScenarioStatus,
            ThermoZoneFanSpeed,
            ThermoZoneMode, ThermoZoneSeason, ThermoZoneStatus,
            DeviceUpdate, LightUpdate, OpeningUpdate, RelayUpdate,
            ThermoZoneUpdate, ScenarioUpdate, DigitalInputUpdate, PlantUpdate,
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
        websession=my_existing_session,
        close_websession_on_disposal=False,
    ) as api:
        ...

.. important:: **Session ownership — read this carefully if you pass a** ``websession``.

    The ``close_websession_on_disposal`` parameter controls whether the HTTP session is
    closed when the ``CameDomoticAPI`` object is disposed (i.e. on exit from the
    ``async with`` block).

    - ``False`` **(default — use this when passing a shared session)**: the session is
      preserved on disposal. This is almost always what you want in Home Assistant and
      similar frameworks, where a single long-lived ``aiohttp.ClientSession`` is shared
      across many integrations. Closing it here would silently break every other
      component that depends on it.
    - ``True``: the session is closed on disposal. Only use this if you explicitly
      want this object to take ownership of the provided session.

    When **no** ``websession`` is provided, this flag is irrelevant: the internally
    created session is always closed on disposal.

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
    Feature: energy
    Feature: loadsctrl

You can use the features list to decide which device APIs to call:

.. code-block:: python

    if "lights" in server_info.features:
        lights = await api.async_get_lights()

    if "openings" in server_info.features:
        openings = await api.async_get_openings()

    if "relays" in server_info.features:
        relays = await api.async_get_relays()

    if "thermoregulation" in server_info.features:
        zones = await api.async_get_thermo_zones()
        sensors = await api.async_get_analog_sensors()

    if "scenarios" in server_info.features:
        scenarios = await api.async_get_scenarios()

    if "digitalin" in server_info.features:
        digital_inputs = await api.async_get_digital_inputs()

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

.. note::
    ``async_get_topology()`` issues all requests concurrently and produces a
    :class:`~aiocamedomotic.models.base.PlantTopology` object with floors
    and rooms already nested, so you don't need to cross-reference floor IDs
    manually.

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
    non-RGB lights.

Openings
^^^^^^^^

Openings represent shutters, awnings, and similar motorized covers. They use
a three-state control model: opening, closing, or stopped.

.. code-block:: python

    from aiocamedomotic.models import OpeningStatus

    openings = await api.async_get_openings()

    for opening in openings:
        print(f"ID: {opening.open_act_id}, Name: {opening.name}, Status: {opening.status}")

    # Control an opening
    shutter = next((o for o in openings if o.open_act_id == 10), None)
    if shutter:
        await shutter.async_set_status(OpeningStatus.OPENING)
        await shutter.async_set_status(OpeningStatus.STOPPED)
        await shutter.async_set_status(OpeningStatus.CLOSING)

Scenarios
^^^^^^^^^

Scenarios are pre-configured automation sequences. They can only be
activated (fire-and-forget); there is no bidirectional status control.

.. code-block:: python

    scenarios = await api.async_get_scenarios()

    for scenario in scenarios:
        print(f"ID: {scenario.id}, Name: {scenario.name}, Status: {scenario.scenario_status}")

    # Activate a scenario
    good_morning = next((s for s in scenarios if s.name == "Good Morning"), None)
    if good_morning:
        await good_morning.async_activate()

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
        mode=ThermoZoneMode.AUTO,
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
    Temperature values are returned as floats in degrees Celsius (the internal
    integer-times-10 representation is converted automatically). The
    ``fan_speed`` parameter in ``async_set_config`` is optional; when
    provided, the ``extended_infos`` flag is set automatically. Season can
    only be changed at the plant level via ``async_set_thermo_season()``.

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

.. note::
    Temperature sensor values are automatically scaled from the raw
    integer-times-10 representation (e.g. ``215`` becomes ``21.5``).
    Humidity and pressure values are returned as-is. The ``sensor_type``
    property (an ``AnalogSensorType`` enum) determines the scaling behavior.

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
    sensor = next((di for di in digital_inputs if di.name == "Front Door"), None)

.. note::
    Some digital inputs do not report a ``status`` until their first state
    change. In that case, ``status`` returns ``DigitalInputStatus.UNKNOWN``.

Relays
^^^^^^

Relays are simple on/off switches that can be controlled remotely. Unlike
lights, they have no brightness or color capabilities.

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
        await pump.async_set_status(RelayStatus.OFF)

.. note::
    The relay API commands are documented in the CAME API specification but
    have not been verified against a real server. If you encounter unexpected
    behaviour, please report it to the library developers.


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
                print(f"[{update.device_type}] {update.name} (ID: {update.device_id})")

            # Brief pause to avoid tight looping on rapid server responses
            await asyncio.sleep(1)

.. note::
    The ``asyncio.sleep(1)`` acts as a safety throttle in case the server
    returns immediately (e.g. errors or rapid update bursts). If you need to
    run the polling loop alongside other logic, wrap it in
    ``asyncio.create_task()``.

Configuring timeouts
^^^^^^^^^^^^^^^^^^^^

All commands use a default timeout of **30 seconds**, configurable via
``command_timeout`` when creating the API instance:

.. code-block:: python

    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password", command_timeout=15
    ) as api:
        lights = await api.async_get_lights()  # uses 15s timeout

For ``async_get_updates()``, a longer timeout is **strongly recommended**
since the server holds the connection open until updates are available:

.. code-block:: python

    updates = await api.async_get_updates(timeout=120)

.. note::
    If no ``timeout`` is passed to ``async_get_updates()``, the instance-level
    ``command_timeout`` is used (default: 30s). For most real-time monitoring
    use cases, a timeout of **60--120 seconds** is recommended.

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

        elif isinstance(update, RelayUpdate):
            print(f"Relay '{update.name}': {update.status.name}")

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
        thermo_zones = await api.async_get_thermo_zones()
        sensors = await api.async_get_analog_sensors()
        digital_inputs = await api.async_get_digital_inputs()

.. note::
    Plant updates are relatively rare. They typically occur when an installer
    modifies the system configuration. Failing to handle them may result in
    stale device data or missing newly added devices.


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
