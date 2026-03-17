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
CAME Domotic analog input entity models.

This module implements the class for working with standalone analog input
sensors in a CAME Domotic system. Analog inputs represent read-only analog
sensors such as hygrometers, thermometers, and barometers exposed via the
``analogin`` feature. They provide sensor readings but do not support
control commands.

These sensors are independent of the thermoregulation system's
:class:`~aiocamedomotic.models.thermo_zone.AnalogSensor`, which is retrieved
from the ``thermo_list_resp`` endpoint. The same physical sensor may appear
in both endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..utils import EntityValidator
from .base import CameEntity


@dataclass
class AnalogIn(CameEntity):
    """Standalone analog input sensor from the ``analogin_list_resp`` endpoint.

    Represents a read-only analog sensor (e.g. hygrometer, thermometer,
    barometer) exposed via the ``analogin`` feature.

    Args:
        raw_data: Dictionary containing the sensor data from the API.

    Raises:
        ValueError: If ``name`` or ``act_id`` keys are missing from
            the input data.

    Note:
        Temperature values (``unit == "C"``) are stored as integers multiplied
        by 10 (e.g. 215 = 21.5 °C). The :attr:`value` property applies the
        conversion automatically.
    """

    raw_data: dict[str, Any]

    def __post_init__(self) -> None:
        EntityValidator.validate_data(
            self.raw_data,
            required_keys=["name", "act_id"],
            typed_keys={"act_id": int},
        )

    @property
    def act_id(self) -> int:
        """Unique actuator/sensor identifier."""
        return self.raw_data["act_id"]

    @property
    def name(self) -> str:
        """Display name of the sensor."""
        return self.raw_data["name"]

    @property
    def value(self) -> float:
        """Sensor reading in the unit reported by :attr:`unit`.

        Temperature readings (``unit == "C"``) are divided by 10 to convert
        from the API's integer encoding to degrees Celsius. All other units
        are returned as-is.
        """
        raw = self.raw_data.get("value", 0)
        if self.unit == "C":
            return raw / 10.0
        return float(raw)

    @property
    def unit(self) -> str:
        """Unit of measurement (e.g. ``'C'``, ``'%'``, ``'hPa'``)."""
        return self.raw_data.get("unit", "")
