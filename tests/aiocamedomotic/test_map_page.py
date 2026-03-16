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

# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import pytest

from aiocamedomotic.models import MapPage


class TestMapPage:
    def test_init_valid_data(self, map_page_data):
        page = MapPage(map_page_data)

        assert page.page_id == 0
        assert page.page_label == "Piano Terra"
        assert page.page_scale == 1024
        assert page.background == "maps/maps_pianta piano terra.png"
        assert len(page.elements) == 2

    def test_init_empty_page(self, map_page_data_empty):
        page = MapPage(map_page_data_empty)

        assert page.page_id == 2
        assert page.page_label == "Empty Floor"
        assert page.elements == []

    def test_missing_page_id_raises(self):
        data = {"page_label": "Test"}
        with pytest.raises(ValueError, match="Data is missing required keys: page_id"):
            MapPage(data)

    def test_missing_page_label_raises(self):
        data = {"page_id": 0}
        with pytest.raises(
            ValueError, match="Data is missing required keys: page_label"
        ):
            MapPage(data)

    def test_missing_multiple_keys_raises(self):
        data = {}
        with pytest.raises(
            ValueError, match="Data is missing required keys: page_id, page_label"
        ):
            MapPage(data)

    def test_invalid_page_id_type_raises(self):
        data = {"page_id": "not_an_int", "page_label": "Test"}
        with pytest.raises(ValueError, match="page_id"):
            MapPage(data)

    def test_non_dict_data_raises(self):
        with pytest.raises(ValueError, match="Provided data must be a dictionary"):
            MapPage("not a dict")

    def test_page_scale_default(self):
        data = {"page_id": 0, "page_label": "Test"}
        page = MapPage(data)
        assert page.page_scale == 1024

    def test_background_default(self):
        data = {"page_id": 0, "page_label": "Test"}
        page = MapPage(data)
        assert page.background == ""

    def test_background_with_spaces(self, map_page_data):
        page = MapPage(map_page_data)
        assert " " in page.background

    def test_elements_missing_array_key(self):
        data = {"page_id": 0, "page_label": "Test"}
        page = MapPage(data)
        assert page.elements == []

    def test_elements_none_array(self):
        data = {"page_id": 0, "page_label": "Test", "array": None}
        page = MapPage(data)
        assert page.elements == []

    def test_elements_returns_raw_dicts(self, map_page_data):
        page = MapPage(map_page_data)
        elements = page.elements

        assert isinstance(elements, list)
        assert all(isinstance(elem, dict) for elem in elements)

        # Verify page link element (type 3) has expected keys
        page_link = elements[0]
        assert page_link["type"] == 3
        assert page_link["label"] == "Bagno"
        assert page_link["page"] == 1

        # Verify light element (type 0) has expected keys
        light = elements[1]
        assert light["type"] == 0
        assert light["label"] == "Specchio Bagno"
        assert light["act_id"] == 4
        assert light["status"] == 0

    def test_raw_data_preserved(self, map_page_data):
        page = MapPage(map_page_data)
        assert page.raw_data is map_page_data
