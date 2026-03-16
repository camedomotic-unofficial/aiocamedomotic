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

API Reference
=============

.. note::
    This page is dynamically created using the
    `sphinx.ext.autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
    extension.


CAME Domotic API
----------------

.. automodule:: aiocamedomotic.came_domotic_api
   :members:


Entity models
-------------

.. automodule:: aiocamedomotic.models
   :members:
   :noindex:

.. automodule:: aiocamedomotic.models.base
   :members:

.. automodule:: aiocamedomotic.models.camera
   :members:

.. automodule:: aiocamedomotic.models.digital_input
   :members:

.. automodule:: aiocamedomotic.models.light
   :members:

.. automodule:: aiocamedomotic.models.map_page
   :members:

.. automodule:: aiocamedomotic.models.opening
   :members:

.. automodule:: aiocamedomotic.models.relay
   :members:

.. automodule:: aiocamedomotic.models.scenario
   :members:

.. automodule:: aiocamedomotic.models.thermo_zone
   :members:

.. automodule:: aiocamedomotic.models.update
   :members:


Constants
---------

.. automodule:: aiocamedomotic.const
   :members: CAME_MAC_PREFIXES, DeviceType, UpdateIndicator


Utilities
---------

.. autofunction:: aiocamedomotic.utils.async_is_came_endpoint

.. automodule:: aiocamedomotic.anonymizer
   :members: TRAFFIC_LOGGER, anonymize_payload


Errors
------

.. automodule:: aiocamedomotic.errors
   :members:


Auth module
-----------

.. automodule:: aiocamedomotic.auth
   :members:
..    :undoc-members:
..    :show-inheritance:
