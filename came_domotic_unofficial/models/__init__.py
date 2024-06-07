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

from .base import CameEntity, CameServerInfo, CameUser  # noqa: F401
from .light import CameLight, LightType, LightStatus  # noqa: F401
from .update import CameUpdateList  # noqa: F401


# Openings
# Scenarios
# Digital inputs
