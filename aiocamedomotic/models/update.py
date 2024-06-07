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

# This module contains the classes for the CAME Domotic status updates.

from dataclasses import dataclass

from typing import Any
from collections import UserList

from .base import CameEntity


@dataclass
class CameUpdateList(UserList[dict[str, Any]], CameEntity):
    """Chronological list of status updates from the CameDomotic API."""

    _raw_data: dict[str, Any] | None

    def __init__(self, raw_data: dict[str, Any] | None = None):
        self._raw_data = raw_data
        if isinstance(raw_data, dict):
            super().__init__(raw_data.get("result", []))
        else:
            super().__init__()
