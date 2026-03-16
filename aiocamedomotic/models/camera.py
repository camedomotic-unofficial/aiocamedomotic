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
CAME Domotic TVCC camera entity models.

This module implements the classes for working with TVCC (closed-circuit
television) cameras in a CAME Domotic system. Cameras are read-only entities
that provide access to IP camera stream URIs but do not support control
commands.

.. note::
    This module is based on reverse-engineered API documentation from the
    CAME JS client and has not been verified against a real CAME Domotic
    server. Behaviour may differ across firmware versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..auth import Auth
from ..utils import EntityValidator
from .base import CameEntity


@dataclass
class Camera(CameEntity):
    """
    TVCC camera entity in the CameDomotic API.

    Cameras are read-only devices that provide streaming video and still-image
    URIs for IP cameras connected to the CAME Domotic system. They cannot be
    controlled remotely — this is purely a viewing/monitoring feature.

    .. warning::
        The ``uri`` and ``uri_still`` fields point directly to camera HTTP
        endpoints on the local network. These URIs may contain embedded
        authentication credentials (e.g. ``http://user:pass@camera/stream``).
        Avoid logging or displaying these values without sanitisation.

    Raises:
        ValueError: If ``name`` or ``id`` keys are missing from the input
            data or the auth argument is not an instance of the expected
            ``Auth`` class.
    """

    raw_data: dict[str, Any]
    auth: Auth

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "id"],
            typed_keys={"id": int},
        )
        # Basic type-safety on the auth argument
        if not isinstance(self.auth, Auth):
            raise ValueError(
                f"'auth' must be an instance of Auth, got {type(self.auth).__name__}"
            )

    @property
    def id(self) -> int:
        """Unique camera identifier.

        Unlike other device models which use ``act_id``, cameras use a plain
        ``id`` field as their primary key (JS field: ``id``, ``idProperty``).
        """
        return self.raw_data["id"]

    @property
    def name(self) -> str:
        """Camera display name (JS field: ``name``)."""
        return self.raw_data["name"]

    @property
    def uri(self) -> str:
        """Primary streaming video URI.

        Points directly to the camera's stream endpoint on the LAN.
        The actual protocol/format is opaque — the JS client loads it
        in an iframe (JS field: ``uri``).
        """
        return self.raw_data.get("uri", "")

    @property
    def uri_still(self) -> str:
        """Snapshot/still-image URI.

        Returns a single JPEG frame from the camera. Useful for thumbnails
        or as a fallback when the primary stream format is not supported.
        Append ``?t=<timestamp>`` for cache busting on repeated fetches
        (JS field: ``uri_still``).
        """
        return self.raw_data.get("uri_still", "")

    @property
    def stream_type(self) -> str:
        """Raw stream format string as returned by the server.

        The only known value with special semantics is ``"swf"`` (Flash).
        All other values are treated identically by the JS client
        (JS field: ``stream_type``).
        """
        return self.raw_data.get("stream_type", "")

    @property
    def is_flash(self) -> bool:
        """Whether this camera uses a Flash (SWF) stream.

        Flash streams are obsolete — consumers should fall back to
        :attr:`uri_still` for cameras where this is ``True``.

        Derived from: ``stream_type == "swf"`` (same check as JS client,
        line 5493).
        """
        return self.stream_type == "swf"
