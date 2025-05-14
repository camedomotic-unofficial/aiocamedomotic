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

To effectively interact with and control your CAME Domotic environment using this
library, certain import directives are necessary at the beginning of your file.

Basic imports
^^^^^^^^^^^^^

To initiate communication with the CAME Domotic server using this asynchronous library
you must import the following:

.. code-block:: python

    import asyncio

    from aiocamedomotic import CameDomoticAPI

Working with entities
^^^^^^^^^^^^^^^^^^^^^

To work with the CAME devices you may need one or more of the following imports:

.. code-block:: python

    from aiocamedomotic.models import LightStatus, OpeningStatus


Handling Exceptions
^^^^^^^^^^^^^^^^^^^

To properly manage potential errors you can add these imports:

.. code-block:: python

    from aiocamedomotic.errors import (
        CameDomoticError, # Generic error raised by the library
        CameDomoticServerNotFoundError, # Raised by the constructor (bad IP/hostname?)
        CameDomoticAuthError, # Authentication failure (bad credentials?)
        CameDomoticServerError, # Error raised by the server
    )

Initializing the API client
---------------------------

Initialize a ``CameDomoticAPI`` instance to connect to your CAME Domotic server. This
step verifies the server's **reachability** but **does not** immediately **validate
credentials** or **establish a session**, since sessions are **initiated on-demand**,
optimizing resource use and security.

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
    library create and manage one for you, you can pass it as value of the
    ``websession`` named parameter of the ``CameDomoticAPI.async_create`` method, and
    the HTTP requests will be made using that session.

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
property (i.e. the MAC address of the server).

.. code-block:: python

    server_info = await api.async_get_server_info()

    print(f"Keycode: {server_info.keycode}")
    print(f"Software version: {server_info.software_version}")
    print(f"Server type: {server_info.server_type}")
    print(f"Board type: {server_info.board}")
    print(f"Serial number: {server_info.serial_number}")

Assuming a successful interaction with the server, the output is:

.. code-block:: text

    Keycode: 0000FFFF9999AAAA
    Software version: 1.2.3
    Server type: 0
    Board type: 3
    Serial number: 0011ffee

Server features
---------------

To understand which capabilities your CAME Domotic plant offers, you can fetch
a list of all the features configured on the remote server using the
``async_get_features()`` method. These features represent the functional blocks you
would see in the official CAME Domotic mobile app's homepage, such as lights, openings,
or scenarios.

.. code-block:: python

    features = await api.async_get_features()

    for feature in features:
        print(f"Feature: {feature.name}")

Below is an example output, showcasing the server's available features. Please note that
each server installation is unique and may support a different list of features.

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

The output of this will be similar to this:

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

You can switch on/off a light object with the ``async_set_status`` method. For dimmable
lights, the method supports also setting the brightness level (the setting is ignored
for non dimmable lights).

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

    # Ensure the light is found (dimmable)
    if living_room_chandelier:
        # Turn the light on, setting the brightness to 50%
        await living_room_chandelier.async_set_status(LightStatus.ON, brightness=50)

        # Turn the light off
        await living_room_chandelier.async_set_status(LightStatus.OFF)

        # Turn the light on, leaving the brightness unchanged
        await living_room_chandelier.async_set_status(LightStatus.ON)

    # Ensure the light is found
    if hallway_night_light:
        # Turn the light on
        await hallway_night_light.async_set_status(LightStatus.ON)

        # Turn the light off
        await hallway_night_light.async_set_status(LightStatus.OFF)


Openings
-------

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
^^^^^^^^^^^^^^^^^^^^

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

    # Ensure the opening is found
    if living_room_shutter:
        # Open the shutter
        await living_room_shutter.async_set_status(OpeningStatus.OPENING)

        # Stop the shutter movement
        await living_room_shutter.async_set_status(OpeningStatus.STOPPED)

        # Close the shutter
        await living_room_shutter.async_set_status(OpeningStatus.CLOSING)

    # Ensure the opening is found
    if patio_awning:
        # Open the awning
        await patio_awning.async_set_status(OpeningStatus.OPENING)

        # Close the awning
        await patio_awning.async_set_status(OpeningStatus.CLOSING)


Checking Authentication Status
------------------------------

**Session management** is automatic and **transparent to the user**, anyway, should you
need for some reason to check the server session status, you can use the
``validate_session()`` method on the ``auth`` attribute of the ``CameDomoticAPI``
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
    Please note that, in general, you don't need to check if the session is authenticated,
    as the library will handle this for you, (re)authenticating as needed.

Exploring further
-----------------

To check the technical specifications see the :doc:`api_reference`.

