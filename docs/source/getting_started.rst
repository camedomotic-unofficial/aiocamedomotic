Getting started
===============

This guide will walk you through the steps to quickly start using the CAME Domotic
Unofficial library in your projects. Before you begin, ensure you have:

- Python 3.12 or newer installed on your system.
- Access to a CAME Domotic server.

Installation
------------

Use `pip <https://pip.pypa.io/en/stable/>`_ to install the latest version of the CAME
Domotic Unofficial library and its dependencies:

.. code-block:: bash

    pip install came-domotic-unofficial

Basic usage examples
--------------------

Here's a simple example to demonstrate how to use the library to turn on or off a light:

.. code-block:: python

    import asyncio

    from aiocamedomotic import CameDomoticAPI
    from aiocamedomotic.models import LightStatus

    async def main():
        async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:

            # Get the server info
            server_info = await api.async_get_server_info()
            print(f"Keycode (i.e. MAC address): {server_info.keycode}")

            # Get the list of all the lights configured on the CAME Domotic server
            lights = await api.async_get_lights()

            # Get a specific light by ID
            bedroom_dimmable_lamp = next((l for l in lights if l.act_id == 33), None)

            # Get a specific light by name
            kitchen_lamp = next(
                (l for l in lights if l.name == "My beautiful lamp"), None
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
            if kitchen_lamp:
                # Turn the light on
                await kitchen_lamp.async_set_status(LightStatus.ON)

                # Turn the light off
                await kitchen_lamp.async_set_status(LightStatus.OFF)

    # Run the main function
    asyncio.run(main())


Let's go step by step:

#. **Creating a Server Instance**:

   First, import the ``CameDomoticAPI`` classes from the library and create a
   ``CameDomoticAPI`` instance using the async factory method
   ``CameDomoticAPI.async_create``.

   .. code-block:: python

        import asyncio

        from aiocamedomotic import CameDomoticAPI
        from aiocamedomotic.models import LightStatus

        async def main():
            async with await CameDomoticAPI.async_create(
            "192.168.x.x", "username", "password"
        ) as api:

   This command will raise a ``CameDomoticServerNotFoundError`` exception if the server
   is not found (tipically, bad IP/hostname or other network issue). Notice that the
   ``CameDomoticAPI`` class is an asynchronous context manager, so it must be used with
   the ``async with`` statement.

   .. note:: The session is *NOT* authenticated at this point: the library will
       authenticate only when the first actual call to the server is made. In case the
       provided credentials are not valid, a ``CameDomoticAuthError`` exception will be
       raised at that time.

#. **Getting the server info**:

   You can retrieve the server info (keycode, serial number, etc.) by using the
   awaitable method ``api.async_get_server_info()``.

   .. code-block:: python

        # Get the server info
        server_info = await api.async_get_server_info()
        print(f"Keycode (i.e. MAC address): {server_info.keycode}")

#. **Fetching the list of available lights**:

   You can retrieve a list of all the lights configured on the CAME Domotic server
   by using the awaitable method ``api.async_get_lights()``.

   .. code-block:: python

        # Get the list of all the lights configured on the CAME Domotic server
        lights = await api.async_get_lights()

   Since this is the first actual call to the server, the library will now authenticate:
   if the provided credentials are not valid, a ``CameDomoticAuthError`` exception will
   be raised.

#. **Selecting a specific light**:

   You can select a specific light, for example, by ID (``act_id`` attribute) or display
   name (``name`` attribute):

   .. code-block:: python

        # Get a specific light by ID
        bedroom_dimmable_lamp = next((l for l in lights if l.act_id == 33), None)

        # Get a specific light by name
        kitchen_lamp = next(
            (l for l in lights if l.name == "My beautiful lamp"), None
        )

#. **Changing the status of a light**

   Lights are controlled by the method ``async_set_status``. You can turn a light on or
   off by passing respectively the status ``LightStatus.ON`` or  ``LightStatus.OFF`` as
   an argument. You can also set the brightness level of a dimmable light by passing the
   optional ``brightness`` argument (range: 0-100).

   .. code-block:: python

        # Ensure the light is found (dimmable)
        if bedroom_dimmable_lamp:
            # Turn the light on, setting the brightness to 50%
            await bedroom_dimmable_lamp.async_set_status(LightStatus.ON, brightness=50)

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

Congratulations! You've successfully used the CAME Domotic Unofficial library to
interact with your CAME Domotic server.

Exploring further
-----------------

- For more detailed examples see :doc:`usage_examples`.
- To check the technical specifications see the :doc:`api_reference`.

Thank you for choosing the CAME Domotic Unofficial library. Happy automating!

