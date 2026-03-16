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
CAME Domotic map page entity model.

This module implements the class representing a page (floor plan) in the
CAME Domotic map system. Maps are read-only — they provide positional
information about devices overlaid on background images but do not support
control commands. Device control is performed through the standard device
command APIs (``light_switch_req``, ``opening_move_req``, etc.).

.. note::
    This module is based on reverse-engineered API documentation from the
    CAME JS client and has not been verified against a real CAME Domotic
    server. Behaviour may differ across firmware versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..utils import EntityValidator
from .base import CameEntity


@dataclass
class MapPage(CameEntity):
    """A page (floor plan) in the CAME Domotic map system.

    Each page represents a spatial view containing positioned elements
    (lights, openings, thermostats, page links, scenarios, cameras)
    overlaid on a background image. Elements are returned as raw
    dictionaries preserving the server response structure.

    The ``elements`` list contains dictionaries with at least the following
    common keys: ``x``, ``y``, ``width``, ``height``, ``type``, ``label``,
    ``aspect``, ``icon_id``, ``permission``, ``read_only``, ``address``.
    Additional keys depend on the element type (e.g. ``act_id`` for devices,
    ``page`` for page links, ``scenario_id`` for scenarios).

    Raises:
        ValueError: If ``page_id`` or ``page_label`` keys are missing from
            the input data, or if ``page_id`` is not an integer.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["page_id", "page_label"],
            typed_keys={"page_id": int},
        )

    @property
    def page_id(self) -> int:
        """Unique page identifier.

        ``0`` is the root/home page.
        """
        return self.raw_data["page_id"]

    @property
    def page_label(self) -> str:
        """Human-readable page title."""
        return self.raw_data["page_label"]

    @property
    def page_scale(self) -> int:
        """Coordinate space size for element positioning.

        Element ``x``/``y`` values range from ``0`` to ``page_scale``.
        Typically ``1024``.
        """
        return self.raw_data.get("page_scale", 1024)

    @property
    def background(self) -> str:
        """Relative URL path to the background image on the CAME server.

        The URL may contain spaces (e.g. ``"maps/maps_pianta piano terra.png"``).
        Consumers must percent-encode the path when making HTTP requests.
        The full URL is constructed as ``http://<server_host>/<background>``.
        """
        return self.raw_data.get("background", "")

    @property
    def elements(self) -> list[dict[str, Any]]:
        """Interactive elements placed on this map page.

        Each element is a raw dictionary from the server response. Common
        keys include ``x``, ``y``, ``width``, ``height``, ``type``,
        ``label``, ``aspect``, ``icon_id``, ``permission``, ``read_only``,
        and ``address``. Type-specific keys (``act_id``, ``page``,
        ``scenario_id``, ``status``) are present only for applicable
        element types.
        """
        return self.raw_data.get("array") or []
