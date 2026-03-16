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

from ..const import DeviceType, UpdateIndicator  # noqa: F401
from .base import (  # noqa: F401
    CameEntity,
    Floor,
    PlantTopology,
    Room,
    ServerInfo,
    TerminalGroup,
    TopologyFloor,
    TopologyRoom,
    User,
)
from .camera import Camera  # noqa: F401
from .digital_input import (  # noqa: F401
    DigitalInput,
    DigitalInputStatus,
    DigitalInputType,
)
from .light import Light, LightStatus, LightType  # noqa: F401
from .map_page import MapPage  # noqa: F401
from .opening import Opening, OpeningStatus, OpeningType  # noqa: F401
from .relay import Relay, RelayStatus  # noqa: F401
from .scenario import Scenario, ScenarioStatus  # noqa: F401
from .thermo_zone import (  # noqa: F401
    AnalogSensor,
    AnalogSensorType,
    ThermoZone,
    ThermoZoneFanSpeed,
    ThermoZoneMode,
    ThermoZoneSeason,
    ThermoZoneStatus,
)
from .update import (  # noqa: F401
    DeviceUpdate,
    DigitalInputUpdate,
    LightUpdate,
    OpeningUpdate,
    PlantUpdate,
    RelayUpdate,
    ScenarioUpdate,
    ThermoZoneUpdate,
    UpdateList,
    get_update_device_type,
    parse_update,
)

__all__ = [
    "AnalogSensor",
    "AnalogSensorType",
    "Camera",
    "CameEntity",
    "DeviceType",
    "DeviceUpdate",
    "DigitalInput",
    "DigitalInputStatus",
    "DigitalInputType",
    "DigitalInputUpdate",
    "Floor",
    "Light",
    "LightStatus",
    "LightType",
    "LightUpdate",
    "MapPage",
    "Opening",
    "OpeningStatus",
    "OpeningType",
    "OpeningUpdate",
    "PlantTopology",
    "PlantUpdate",
    "Relay",
    "RelayStatus",
    "RelayUpdate",
    "Room",
    "Scenario",
    "ScenarioStatus",
    "ScenarioUpdate",
    "ServerInfo",
    "TerminalGroup",
    "TopologyFloor",
    "TopologyRoom",
    "ThermoZone",
    "ThermoZoneFanSpeed",
    "ThermoZoneMode",
    "ThermoZoneSeason",
    "ThermoZoneStatus",
    "ThermoZoneUpdate",
    "UpdateIndicator",
    "UpdateList",
    "User",
    "get_update_device_type",
    "parse_update",
]
