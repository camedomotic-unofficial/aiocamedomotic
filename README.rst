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

Welcome!
========

.. image:: https://img.shields.io/badge/License-Apache%202.0-D22128.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache 2.0

.. image:: https://img.shields.io/badge/python-3.12-417fb0.svg
    :target: https://www.python.org
    :alt: Python 3.12

.. image:: https://sonarcloud.io/api/project_badges/measure?project=camedomotic-unofficial_came_domotic_unofficial&metric=security_rating
   :target: https://sonarcloud.io/project/overview?id=camedomotic-unofficial_came_domotic_unofficial
   :alt: SonarCloud - Security Rating

.. image:: https://sonarcloud.io/api/project_badges/measure?project=camedomotic-unofficial_came_domotic_unofficial&metric=vulnerabilities
   :target: https://sonarcloud.io/project/overview?id=camedomotic-unofficial_came_domotic_unofficial
   :alt: SonarCloud - Vulnerabilities

.. image:: https://sonarcloud.io/api/project_badges/measure?project=camedomotic-unofficial_came_domotic_unofficial&metric=bugs
   :target: https://sonarcloud.io/project/overview?id=camedomotic-unofficial_came_domotic_unofficial
   :alt: SonarCloud - Bugs

.. image:: https://readthedocs.org/projects/came-domotic-unofficial/badge/?version=latest
   :target: https://came-domotic-unofficial.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation status


The **CAME Domotic Unofficial Library** provides a streamlined Python interface for
interacting with CAME Domotic plants, much like the official
`CAME Domotic app <https://www.came.com/global/itex/installers/solutions/domotica-e-termoregolazione/prodotti-compatibili-domotica/app-domotic-30>`_.
This library is designed to simplify the management of domotic devices by abstracting
the complexities of the CAME Domotic API.

Although primarily developed for use with
`Home Assistant <https://www.home-assistant.io/>`_, the library is freely available
under the `Apache license 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_ for anyone
interested in experimenting with a CAME Domotic plant.


.. warning::
    This library is currently in **beta development status**.
    It is not yet stable and should be used only for studying purposes.
    Please be aware that you cannot rely on it for any production use.
    Use at your own risk.

.. note::
    This library is independently developed and is not affiliated with, endorsed by,
    or supported by `CAME <https://www.came.com/>`_. It may not be compatible with all
    CAME Domotic systems. Use at your own risk.

.. danger::

    This library is not intended for use in critical systems, such as security or
    life-support systems. Always use official and supported tools for such applications.


Key Features
------------
- **Simplicity**: Easy interaction with domotic entities.
- **Automatic session management**: No need for manual login or session handling.
- **First of its kind**: Unique in providing integration with CAME Domotic systems.
- **Open source**: Freely available under the Apache 2.0 license, inviting
  contributions and adaptations.


Quick Start
-----------

Have a look at the following guides to learn how to install and use the library:

- `Getting started <https://came-domotic-unofficial.readthedocs.io/en/latest/getting_started.html>`_
- `Usage examples <https://came-domotic-unofficial.readthedocs.io/en/latest/usage_examples.html>`_

Once you are a bit more familiar with the library, you may want to explore the following
resources too:

- `API reference <https://came-domotic-unofficial.readthedocs.io/en/latest/api_reference.html>`_
- `What's new (releases) <https://github.com/camedomotic-unofficial/came_domotic_unofficial/releases>`_
- `Development roadmap <https://github.com/camedomotic-unofficial/came_domotic_unofficial/blob/main/ROADMAP.md#development-roadmap>`_
- `Security Policy <https://github.com/camedomotic-unofficial/came_domotic_unofficial/blob/main/SECURITY.md#security-policy>`_
- `Contributing to Our Project <https://github.com/camedomotic-unofficial/came_domotic_unofficial/blob/main/CONTRIBUTING.md#contributing-to-our-project>`_


Acknowledgments
---------------
Special thanks to Andrea Michielan for his foundational work with the
`eti_domo <https://github.com/andrea-michielan/eti_domo>`_ library, which greatly
facilitated the development of this library. We also found great inspiration in the Home
Assistant document
`Building a Python library for an API <https://developers.home-assistant.io/docs/api_lib_index>`_.


License
=======
This project is licensed under the Apache License 2.0. For more details, see the
`LICENSE file <https://github.com/camedomotic-unofficial/came_domotic_unofficial/blob/main/LICENSE>`_
on GitHub.
