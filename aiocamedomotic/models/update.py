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
CAME Domotic status update handling.

This module provides classes for processing and representing status updates
from the CAME Domotic system. It implements a specialized list-based data
structure to track chronological updates and state changes received from
the CAME Domotic API, facilitating the consumption of system state changes.
"""

from __future__ import annotations

from collections import UserList
from dataclasses import dataclass
from typing import Any

from ..const import _UPDATE_CMD_TO_DEVICE_TYPE, DeviceType
from ..utils import LOGGER
from .base import CameEntity


def get_update_device_type(update: dict[str, Any]) -> DeviceType | None:
    """Return the device type for a status update dict, or None if unknown.

    Args:
        update: A single update dict from the ``status_update_resp`` result
            array. Must contain a ``cmd_name`` key.

    Returns:
        The corresponding :class:`~aiocamedomotic.const.DeviceType`, or
        ``None`` if the ``cmd_name`` is not recognized.
    """
    cmd_name: str | None = update.get("cmd_name")
    if cmd_name is None:
        return None
    return _UPDATE_CMD_TO_DEVICE_TYPE.get(cmd_name)


@dataclass
class UpdateList(UserList[dict[str, Any]], CameEntity):
    """Chronological list of status updates from the CameDomotic API."""

    def __init__(self, updates: UserList[dict[str, Any]] | None = None):
        try:
            super().__init__(updates)
        except TypeError as exc:
            LOGGER.warning("Caught exception in the UpdateList method", exc_info=exc)
            super().__init__()
