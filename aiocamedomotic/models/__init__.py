# SPDX-FileCopyrightText: 2024 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the Python representation of each of the entity types used by the
CAME Domotic API.
"""

from __future__ import annotations

from ..const import DeviceType, ServerFeature, UpdateIndicator  # noqa: F401
from .analog_in import AnalogIn  # noqa: F401
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
from .energy_meter import EnergyMeter, EnergyMeterType  # noqa: F401
from .light import Light, LightStatus, LightType  # noqa: F401
from .loads_ctrl import (  # noqa: F401
    LoadsCtrlMeter,
    LoadsCtrlRelay,
    LoadsCtrlRelayStatus,
)
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
from .timer import Timer, TimerTimeSlot  # noqa: F401
from .update import (  # noqa: F401
    AnalogInUpdate,
    DeviceUpdate,
    DigitalInputUpdate,
    EnergyMeterUpdate,
    LightUpdate,
    LoadsCtrlMeterUpdate,
    LoadsCtrlRelayUpdate,
    OpeningUpdate,
    PlantUpdate,
    RelayUpdate,
    ScenarioUpdate,
    ThermoZoneUpdate,
    TimerUpdate,
    UpdateList,
    get_update_device_type,
    parse_update,
)

__all__ = [
    "AnalogIn",
    "AnalogInUpdate",
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
    "EnergyMeter",
    "EnergyMeterType",
    "EnergyMeterUpdate",
    "Floor",
    "Light",
    "LightStatus",
    "LightType",
    "LightUpdate",
    "LoadsCtrlMeter",
    "LoadsCtrlMeterUpdate",
    "LoadsCtrlRelay",
    "LoadsCtrlRelayStatus",
    "LoadsCtrlRelayUpdate",
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
    "ServerFeature",
    "ServerInfo",
    "TerminalGroup",
    "ThermoZone",
    "ThermoZoneFanSpeed",
    "ThermoZoneMode",
    "ThermoZoneSeason",
    "ThermoZoneStatus",
    "ThermoZoneUpdate",
    "Timer",
    "TimerTimeSlot",
    "TimerUpdate",
    "TopologyFloor",
    "TopologyRoom",
    "UpdateIndicator",
    "UpdateList",
    "User",
    "get_update_device_type",
    "parse_update",
]
