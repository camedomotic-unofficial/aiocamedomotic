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

"""Utilities for the CAME Domotic API."""

import logging

LOGGER = logging.getLogger(__package__)


class EntityValidator:
    """Mixin class to validate the CAME entities."""

    @staticmethod
    def validate_data(data, required_keys) -> None:
        """
        Validates the necessary data fields in the provided dictionary.

        Args:
            data (dict): The data dictionary to validate.
            required_keys (list): A list of keys that must be present in the data.

        Raises:
            ValueError: If any required key is missing from the data.
        """
        if not isinstance(data, dict):
            raise ValueError("Provided data must be a dictionary.")

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(
                f"Data is missing required keys: {', '.join(missing_keys)}"
            )
