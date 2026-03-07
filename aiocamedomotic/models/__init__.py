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
This module defines the Python representation of each of the entity types used by the
CAME Domotic API.
"""

from __future__ import annotations

from ..const import DeviceType  # noqa: F401
from .base import CameEntity, Floor, Room, ServerInfo, User  # noqa: F401
from .light import Light, LightStatus, LightType  # noqa: F401
from .opening import Opening, OpeningStatus, OpeningType  # noqa: F401
from .scenario import Scenario, ScenarioStatus  # noqa: F401
from .thermo_zone import (  # noqa: F401
    AnalogSensor,
    ThermoZone,
    ThermoZoneMode,
    ThermoZoneSeason,
    ThermoZoneStatus,
)
from .update import UpdateList, get_update_device_type  # noqa: F401

__all__ = [
    "AnalogSensor",
    "CameEntity",
    "DeviceType",
    "Floor",
    "Light",
    "LightStatus",
    "LightType",
    "Opening",
    "OpeningStatus",
    "OpeningType",
    "Room",
    "Scenario",
    "ScenarioStatus",
    "ServerInfo",
    "ThermoZone",
    "ThermoZoneMode",
    "ThermoZoneSeason",
    "ThermoZoneStatus",
    "UpdateList",
    "User",
    "get_update_device_type",
]

# Digital inputs
