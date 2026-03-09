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

This section provides **practical examples** to help you get started with the
CAME Domotic Unofficial library.

.. note::
    The examples assume you have already installed the library (``pip
    install aiocamedomotic``) and are familiar with the basics of Python
    programming.

Essential imports for working with this library
-----------------------------------------------

To interact with and control your CAME Domotic environment using this
library, you need the following imports at the beginning of your file.

Basic imports
^^^^^^^^^^^^^

To communicate with the CAME Domotic server using this asynchronous library,
you need to import the following:

.. code-block:: python

    import asyncio

    from aiocamedomotic import CameDomoticAPI

Working with entities
^^^^^^^^^^^^^^^^^^^^^

To work with CAME devices, you may need one or more of the following imports:

.. code-block:: python

    from aiocamedomotic.models import (
        DeviceType, LightStatus, OpeningStatus, ScenarioStatus,
        ThermoZoneMode, ThermoZoneSeason, ThermoZoneStatus,
    )

Working with real-time updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To receive and process real-time status updates from the CAME Domotic server,
you will also need the following typed update classes:

.. code-block:: python

    from aiocamedomotic.models import (
        DeviceType,
        DeviceUpdate,
        LightUpdate,
        OpeningUpdate,
        ThermoZoneUpdate,
        ScenarioUpdate,
        DigitalInputUpdate,
        PlantUpdate,
    )


Handling Exceptions
^^^^^^^^^^^^^^^^^^^

To properly handle potential errors, you can add these imports:

.. code-block:: python

    from aiocamedomotic.errors import (
        CameDomoticError, # Base error raised by the library
        CameDomoticServerNotFoundError, # Server not reachable (wrong IP/hostname?)
        CameDomoticAuthError, # Authentication failure (wrong credentials?)
        CameDomoticServerError, # Server-side error
    )

Device autodiscovery
--------------------

The library exposes known MAC address OUI (Organizationally Unique Identifier)
prefixes for CAME Domotic devices via the ``CAME_MAC_PREFIXES`` constant. This
can be used as a first step to identify potential CAME ETI/Domo servers on the
local network.

Checking the MAC address prefix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``CAME_MAC_PREFIXES`` to quickly filter network devices that may be CAME
Domotic servers:

.. code-block:: python

    from aiocamedomotic import CAME_MAC_PREFIXES

    def is_came_mac(mac_address: str) -> bool:
        """Check if a MAC address belongs to a known CAME/BPT manufacturer."""
        mac_upper = mac_address.upper()
        return any(mac_upper.startswith(prefix) for prefix in CAME_MAC_PREFIXES)

    # Example: filter discovered devices on the network
    discovered_mac = "00:1C:B2:71:1B:82"
    if is_came_mac(discovered_mac):
        print(f"{discovered_mac} looks like a CAME device")

Verifying the CAME API endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A matching MAC prefix alone does not guarantee the device is a CAME Domotic
server. To confirm, use :func:`~aiocamedomotic.utils.async_is_came_endpoint`
to check whether the host exposes the CAME API endpoint. This check does
**not** require credentials, making it suitable for autodiscovery:

.. code-block:: python

    from aiocamedomotic import CAME_MAC_PREFIXES, async_is_came_endpoint

    async def async_discover_came_server(host: str, mac_address: str) -> bool:
        """Check if a network device is a CAME Domotic server.

        No credentials are needed: the function only verifies that the
        MAC address belongs to a known CAME/BPT manufacturer and that
        the host exposes the expected API endpoint.
        """
        # Step 1: Quick MAC prefix check
        mac_upper = mac_address.upper()
        if not any(mac_upper.startswith(prefix) for prefix in CAME_MAC_PREFIXES):
            return False

        # Step 2: Verify the device exposes a valid CAME API endpoint
        return await async_is_came_endpoint(host)


Initializing the API client
---------------------------

Initialize a ``CameDomoticAPI`` instance to connect to your CAME Domotic server. This
step verifies that the server is **reachable** but **does not** immediately **validate
credentials** or **establish a session**, since sessions are **created on demand**,
which optimizes resource usage and security.

.. code-block:: python

    import asyncio
    from aiohttp import ClientSession

    from aiocamedomotic import Auth, CameDomoticAPI

    async def async_my_usage_example():
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:

.. note::
    If you want to reuse an existing ``aiohttp.ClientSession`` instead of letting the
    library create and manage one for you, you can pass it as the value of the
    ``websession`` parameter of the ``CameDomoticAPI.async_create`` method. The
    HTTP requests will then be made using that session.

    .. code-block:: python

        async def async_my_usage_example():
            async with await CameDomoticAPI.async_create(
                "192.168.x.x",
                "username",
                "password",
                websession=my_existing_session,
            ) as api:

Server information
------------------

You can access the CAME Domotic server properties using the ``async_get_server_info()``
method. Should you need a **unique ID** for the server, you can use the ``keycode``
property, a CAME proprietary unique identifier for the server.

.. code-block:: python

    server_info = await api.async_get_server_info()

    print(f"Keycode: {server_info.keycode}")
    print(f"Software version: {server_info.software_version}")
    print(f"Server type: {server_info.server_type}")
    print(f"Board type: {server_info.board}")
    print(f"Serial number: {server_info.serial_number}")

On success, the output looks like this:

.. code-block:: text

    Keycode: 0000FFFF9999AAAA
    Software version: 1.2.3
    Server type: 0
    Board type: 3
    Serial number: 0011ffee

Server features
---------------

To find out which capabilities your CAME Domotic system offers, you can fetch
a list of all the features configured on the server using the
``async_get_features()`` method. These features represent the functional blocks you
would see in the official CAME Domotic mobile app's homepage, such as lights, openings,
or scenarios.

.. code-block:: python

    features = await api.async_get_features()

    for feature in features:
        print(f"Feature: {feature.name}")

Below is example output showing the server's available features. Note that each
server installation is unique and may support a different set of features.

.. code-block:: text

    Feature: lights
    Feature: openings
    Feature: thermoregulation
    Feature: scenarios
    Feature: digitalin
    Feature: energy
    Feature: loadsctrl


Server users
------------

To list the users configured on the CAME Domotic server, just run the
``async_get_users()`` method:

.. code-block:: python

    users = await api.async_get_users()

    for user in users:
        print(f"Username: {user.name}")

The output will look similar to this:

.. code-block:: text

    Username: alex
    Username: sam
    Username: jordan


Lights
------

List of available lights
^^^^^^^^^^^^^^^^^^^^^^^^

You can get the list of all the available lights with the ``async_get_lights()``
method:

.. code-block:: python

    lights = await api.async_get_lights()

    for light in lights:
        print(f"ID: {light.act_id}, Name: {light.name}, Status: {light.status}")

Example output for lights:

.. code-block:: text

    ID: 1, Name: Living Room Chandelier, Status: LightStatus.ON
    ID: 2, Name: Hallway Night Light, Status: LightStatus.OFF

Change light status
^^^^^^^^^^^^^^^^^^^

You can turn a light on or off with the ``async_set_status`` method. For dimmable
lights, the method also supports setting the brightness level (this setting is ignored
for non-dimmable lights).

The following example shows different ways to interact with a light device:

.. code-block:: python

    # Get the list of all the lights configured on the CAME server
    lights = await api.async_get_lights()

    # Get a specific light by ID
    living_room_chandelier = next((l for l in lights if l.act_id == 1), None)

    # Get a specific light by name
    hallway_night_light = next(
        (l for l in lights if l.name == "Hallway Night Light"), None
    )

    # Control a dimmable light if found
    if living_room_chandelier:
        # Turn the light on, setting the brightness to 50%
        await living_room_chandelier.async_set_status(LightStatus.ON, brightness=50)

        # Turn the light off
        await living_room_chandelier.async_set_status(LightStatus.OFF)

        # Turn the light on, leaving the brightness unchanged
        await living_room_chandelier.async_set_status(LightStatus.ON)

    # Control a non-dimmable light if found
    if hallway_night_light:
        # Turn the light on
        await hallway_night_light.async_set_status(LightStatus.ON)

        # Turn the light off
        await hallway_night_light.async_set_status(LightStatus.OFF)


Openings
--------

List of available openings
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get the list of all the available openings with the ``async_get_openings()``
method:

.. code-block:: python

    openings = await api.async_get_openings()

    for opening in openings:
        print(f"ID: {opening.id}, Name: {opening.name}, Status: {opening.status}, Type: {opening.type}")

Example output for openings:

.. code-block:: text

    ID: 10, Name: Living Room Shutter, Status: OpeningStatus.STOPPED, Type: OpeningType.SHUTTER
    ID: 20, Name: Patio Awning, Status: OpeningStatus.OPENING, Type: OpeningType.SHUTTER

Change opening status
^^^^^^^^^^^^^^^^^^^^^

You can control an opening with the ``async_set_status`` method, allowing you to open, close,
or stop an opening.

The following example shows different ways to interact with opening devices:

.. code-block:: python

    # Get the list of all the openings configured on the CAME server
    openings = await api.async_get_openings()

    # Get a specific opening by ID
    living_room_shutter = next((o for o in openings if o.open_act_id == 10), None)

    # Get a specific opening by name
    patio_awning = next(
        (o for o in openings if o.name == "Patio Awning"), None
    )

    # Control the shutter if found
    if living_room_shutter:
        # Open the shutter
        await living_room_shutter.async_set_status(OpeningStatus.OPENING)

        # Stop the shutter movement
        await living_room_shutter.async_set_status(OpeningStatus.STOPPED)

        # Close the shutter
        await living_room_shutter.async_set_status(OpeningStatus.CLOSING)

    # Control the awning if found
    if patio_awning:
        # Open the awning
        await patio_awning.async_set_status(OpeningStatus.OPENING)

        # Close the awning
        await patio_awning.async_set_status(OpeningStatus.CLOSING)


Scenarios
---------

List of available scenarios
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get the list of all the available scenarios with the ``async_get_scenarios()``
method:

.. code-block:: python

    scenarios = await api.async_get_scenarios()

    for scenario in scenarios:
        print(f"ID: {scenario.id}, Name: {scenario.name}, Status: {scenario.scenario_status}")

Example output for scenarios:

.. code-block:: text

    ID: 1, Name: Good Morning, Status: ScenarioStatus.OFF
    ID: 2, Name: Good Night, Status: ScenarioStatus.OFF

Activate a scenario
^^^^^^^^^^^^^^^^^^^

You can activate a scenario with the ``async_activate`` method. Scenarios represent
pre-configured automation sequences that control multiple devices at once.

The following example shows how to activate a scenario:

.. code-block:: python

    # Get the list of all the scenarios configured on the CAME server
    scenarios = await api.async_get_scenarios()

    # Get a specific scenario by ID
    good_morning = next((s for s in scenarios if s.id == 1), None)

    # Get a specific scenario by name
    good_night = next(
        (s for s in scenarios if s.name == "Good Night"), None
    )

    # Activate the scenario if found
    if good_morning:
        await good_morning.async_activate()

    if good_night:
        await good_night.async_activate()


Thermoregulation zones
----------------------

List of available thermoregulation zones
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get the list of all the available thermoregulation zones with the
``async_get_thermo_zones()`` method:

.. code-block:: python

    zones = await api.async_get_thermo_zones()

    for zone in zones:
        print(
            f"ID: {zone.act_id}, Name: {zone.name}, "
            f"Temperature: {zone.temperature}°C, "
            f"Setpoint: {zone.set_point}°C, "
            f"Mode: {zone.mode}, Season: {zone.season}"
        )

Example output for thermoregulation zones:

.. code-block:: text

    ID: 1, Name: Living Room, Temperature: 20.0°C, Setpoint: 21.5°C, Mode: ThermoZoneMode.AUTO, Season: ThermoZoneSeason.WINTER
    ID: 52, Name: Bedroom, Temperature: 19.5°C, Setpoint: 20.0°C, Mode: ThermoZoneMode.MANUAL, Season: ThermoZoneSeason.WINTER

.. note::
    Temperature values are returned as float values in degrees Celsius.
    The API internally stores them as integers multiplied by 10
    (e.g., 215 = 21.5°C), but this conversion is handled automatically.

Analog sensors
--------------

List of available analog sensors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analog sensors provide top-level temperature, humidity, and pressure readings
from the thermoregulation system. You can retrieve them with the
``async_get_analog_sensors()`` method:

.. code-block:: python

    sensors = await api.async_get_analog_sensors()

    for sensor in sensors:
        print(f"Name: {sensor.name}, Value: {sensor.value}, Unit: {sensor.unit}")

Example output for analog sensors:

.. code-block:: text

    Name: Outdoor Temperature, Value: 21.5, Unit: °C
    Name: Indoor Humidity, Value: 55, Unit: %
    Name: Barometric Pressure, Value: 1013, Unit: hPa


Real-time updates
-----------------

The CAME Domotic server supports **long polling** for real-time status updates.
When you call ``async_get_updates()``, the request **blocks on the server**
until one or more device state changes are detected, then returns an
:class:`~aiocamedomotic.models.update.UpdateList` containing all pending
updates. This is the recommended mechanism for monitoring devices in real time
without repeatedly fetching full device lists.

Basic polling loop
^^^^^^^^^^^^^^^^^^

A typical polling loop continuously calls ``async_get_updates()`` and processes
each batch of updates as it arrives:

.. code-block:: python

    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password"
    ) as api:
        while True:
            updates = await api.async_get_updates()

            for update in updates.get_typed_updates():
                print(f"[{update.device_type}] {update.name} (ID: {update.device_id})")

.. note::
    Because ``async_get_updates()`` blocks until the server has new updates,
    you do **not** need to add ``asyncio.sleep()`` between calls. If you need
    to run the polling loop alongside other logic, wrap it in
    ``asyncio.create_task()``.

Configuring timeouts
^^^^^^^^^^^^^^^^^^^^

All commands sent to the CAME server use a default timeout of **30 seconds**,
configurable via the ``command_timeout`` parameter when creating the API
instance:

.. code-block:: python

    # Set a custom timeout of 15 seconds for all commands
    async with await CameDomoticAPI.async_create(
        "192.168.x.x", "username", "password", command_timeout=15
    ) as api:
        lights = await api.async_get_lights()  # uses 15s timeout

By default, ``async_get_updates()`` also uses ``command_timeout``. However,
since this method uses **long polling** (the server holds the connection open
until updates are available), a longer timeout is **strongly recommended** to
avoid premature disconnections:

.. code-block:: python

    # Recommended: set a longer timeout for long-polling requests
    updates = await api.async_get_updates(timeout=120)

.. note::
    If no ``timeout`` is passed to ``async_get_updates()``, the instance-level
    ``command_timeout`` is used (default: 30s). For most real-time monitoring
    use cases, a timeout of **60–120 seconds** is recommended.

Getting typed updates
^^^^^^^^^^^^^^^^^^^^^

The ``UpdateList`` returned by ``async_get_updates()`` supports iteration over
raw dicts for backward compatibility. To get **typed** update objects with
convenient properties, use the ``get_typed_updates()`` method:

.. code-block:: python

    updates = await api.async_get_updates()

    for update in updates.get_typed_updates():
        print(
            f"Type: {update.device_type}, "
            f"ID: {update.device_id}, "
            f"Name: {update.name}"
        )

Example output:

.. code-block:: text

    Type: DeviceType.LIGHT, ID: 15, Name: Living Room Spotlights
    Type: DeviceType.THERMOSTAT, ID: 76, Name: Bathroom

Each typed update is an instance of a :class:`~aiocamedomotic.models.update.DeviceUpdate`
subclass (e.g. :class:`~aiocamedomotic.models.update.LightUpdate`,
:class:`~aiocamedomotic.models.update.ThermoZoneUpdate`) and exposes
device-specific properties.

Filtering updates by device type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To process only updates for a specific device type, use
``get_typed_by_device_type()``:

.. code-block:: python

    updates = await api.async_get_updates()

    # Get only light updates, already typed as LightUpdate
    light_updates = updates.get_typed_by_device_type(DeviceType.LIGHT)

    for light in light_updates:
        print(
            f"Light '{light.name}': status={light.status}, "
            f"type={light.light_type}, brightness={light.perc}%"
        )

Example output:

.. code-block:: text

    Light 'Living Room Spotlights': status=LightStatus.ON, type=LightType.STEP_STEP, brightness=100%
    Light 'Bedroom Dimmer': status=LightStatus.ON, type=LightType.DIMMER, brightness=50%

Dispatching by update type
^^^^^^^^^^^^^^^^^^^^^^^^^^

For more granular control, use ``isinstance`` to dispatch each update to
device-specific handling logic:

.. code-block:: python

    updates = await api.async_get_updates()

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

        elif isinstance(update, PlantUpdate):
            print("Plant configuration changed, re-fetching devices...")

Handling plant updates
^^^^^^^^^^^^^^^^^^^^^^

A special ``plant_update_ind`` indication signals that the **device
configuration on the server has changed** (e.g. devices were added, removed, or
reconfigured). When this happens, all locally cached device lists must be
discarded and re-fetched.

You can check for this using the ``has_plant_update`` property:

.. code-block:: python

    updates = await api.async_get_updates()

    if updates.has_plant_update:
        # Device configuration changed: refresh all cached device lists
        lights = await api.async_get_lights()
        openings = await api.async_get_openings()
        scenarios = await api.async_get_scenarios()
        thermo_zones = await api.async_get_thermo_zones()

.. note::
    Plant updates are relatively rare. They typically occur when an installer
    modifies the system configuration. Failing to handle them may result in
    stale device data or missing newly added devices.


Checking Authentication Status
------------------------------

**Session management** is automatic and **transparent to the user**. However, if you
need to check the server session status for any reason, you can use the
``is_session_valid()`` method on the ``auth`` attribute of the ``CameDomoticAPI``
instance.

.. code-block:: python

    async def async_my_usage_example():
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:

            # ...other code above

            if api.auth.is_session_valid():
                print("Server session is authenticated and valid.")
            else:
                print("No valid session, but don't worry: it'll be renewed automatically.")

.. note::
    In general, you don't need to check whether the session is authenticated,
    as the library handles this for you and reauthenticates as needed.

Exploring further
-----------------

For technical details, see the :doc:`api_reference`.
