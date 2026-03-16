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
# pylint: disable=missing-class-docstring

"""Tests for the anonymizer module."""

import logging
from unittest.mock import patch

from aiocamedomotic.anonymizer import (
    TRAFFIC_LOGGER,
    _anonymize_host,
    _anonymize_uri,
    _anonymize_url,
    _anonymize_value,
    _partial_redact,
    anonymize_payload,
    log_traffic,
)

# ---------------------------------------------------------------------------
# _partial_redact
# ---------------------------------------------------------------------------


class TestPartialRedact:
    def test_normal_string(self):
        assert _partial_redact("admin", 2, "***") == "ad***"

    def test_exact_length(self):
        assert _partial_redact("ab", 2, "***") == "ab***"

    def test_short_string_fully_redacted(self):
        assert _partial_redact("a", 2, "***") == "***"

    def test_empty_string_fully_redacted(self):
        assert _partial_redact("", 2, "***") == "***"

    def test_long_keycode(self):
        assert _partial_redact("61305E975DE3F469", 8, "********") == "61305E97********"


# ---------------------------------------------------------------------------
# _anonymize_host
# ---------------------------------------------------------------------------


class TestAnonymizeHost:
    def test_ipv4_address(self):
        assert _anonymize_host("192.168.1.100") == "192.168.1.***"

    def test_ipv4_short_octets(self):
        assert _anonymize_host("10.0.0.1") == "10.0.0.***"

    def test_hostname_with_domain(self):
        assert _anonymize_host("came-server.local") == "came-server.***"

    def test_hostname_with_multiple_segments(self):
        assert _anonymize_host("came.server.example.com") == "came.***"

    def test_single_segment_hostname(self):
        assert _anonymize_host("localhost") == "***"

    def test_empty_string(self):
        assert _anonymize_host("") == "***"


# ---------------------------------------------------------------------------
# _anonymize_url
# ---------------------------------------------------------------------------


class TestAnonymizeUrl:
    def test_http_url_with_ipv4(self):
        result = _anonymize_url("http://192.168.1.100/domo/")
        assert result == "http://192.168.1.***/domo/"

    def test_url_with_port(self):
        result = _anonymize_url("http://192.168.1.100:8080/domo/")
        assert result == "http://192.168.1.***:8080/domo/"

    def test_url_with_hostname(self):
        result = _anonymize_url("http://came-server.local/domo/")
        assert result == "http://came-server.***/domo/"

    def test_empty_url(self):
        assert _anonymize_url("") == ""


# ---------------------------------------------------------------------------
# _anonymize_uri
# ---------------------------------------------------------------------------


class TestAnonymizeUri:
    def test_uri_with_credentials(self):
        result = _anonymize_uri("http://user:pass@192.168.1.100:8080/stream")
        assert result == "http://***:***@192.168.1.100:8080/stream"

    def test_uri_with_user_only(self):
        result = _anonymize_uri("http://user@192.168.1.100/stream")
        assert result == "http://***:***@192.168.1.100/stream"

    def test_uri_without_credentials(self):
        uri = "http://192.168.1.100/stream"
        assert _anonymize_uri(uri) == uri

    def test_empty_uri(self):
        assert _anonymize_uri("") == ""

    def test_uri_with_query_and_fragment(self):
        result = _anonymize_uri("http://user:pass@host/path?t=123#frag")
        assert "***:***@host" in result
        assert "?t=123" in result
        assert "#frag" in result


# ---------------------------------------------------------------------------
# _anonymize_value
# ---------------------------------------------------------------------------


class TestAnonymizeValue:
    # Full redaction
    def test_sl_pwd_fully_redacted(self):
        assert _anonymize_value("sl_pwd", "my_secret") == "***"

    def test_sl_new_pwd_fully_redacted(self):
        assert _anonymize_value("sl_new_pwd", "new_secret") == "***"

    def test_sl_pwd_non_string_unchanged(self):
        assert _anonymize_value("sl_pwd", 12345) == 12345

    # Partial redaction
    def test_sl_login_partial(self):
        assert _anonymize_value("sl_login", "admin") == "ad***"

    def test_sl_login_short(self):
        assert _anonymize_value("sl_login", "a") == "***"

    def test_sl_client_id_partial(self):
        assert _anonymize_value("sl_client_id", "5046b5a9") == "504***"

    def test_client_partial(self):
        assert _anonymize_value("client", "5046b5a9") == "504***"

    def test_keycode_partial(self):
        assert _anonymize_value("keycode", "61305E975DE3F469") == "61305E97********"

    def test_serial_partial(self):
        assert _anonymize_value("serial", "03718b9a") == "037*****"

    def test_partial_non_string_unchanged(self):
        assert _anonymize_value("sl_client_id", 12345) == 12345

    # URI fields
    def test_uri_with_credentials(self):
        result = _anonymize_value("uri", "http://user:pass@host/stream")
        assert "***:***@host" in result

    def test_uri_still_with_credentials(self):
        result = _anonymize_value("uri_still", "http://user:pass@host/snap.jpg")
        assert "***:***@host" in result

    def test_uri_non_string_unchanged(self):
        assert _anonymize_value("uri", None) is None

    # Non-sensitive fields
    def test_non_sensitive_field_unchanged(self):
        assert _anonymize_value("cmd_name", "light_list_req") == "light_list_req"

    def test_device_name_not_redacted(self):
        assert _anonymize_value("name", "Living Room Light") == "Living Room Light"

    # sl_users_list context-aware handling
    def test_sl_users_list_name_redacted(self):
        users = [{"name": "admin"}, {"name": "guest"}]
        result = _anonymize_value("sl_users_list", users)
        assert result[0]["name"] == "ad***"
        assert result[1]["name"] == "gu***"

    def test_sl_users_list_sl_login_redacted(self):
        users = [{"sl_login": "admin"}]
        result = _anonymize_value("sl_users_list", users)
        assert result[0]["sl_login"] == "ad***"

    def test_sl_users_list_non_dict_items_preserved(self):
        users = ["admin", 42]
        result = _anonymize_value("sl_users_list", users)
        assert result == ["admin", 42]

    def test_sl_users_list_does_not_modify_original(self):
        users = [{"name": "admin"}]
        _anonymize_value("sl_users_list", users)
        assert users[0]["name"] == "admin"


# ---------------------------------------------------------------------------
# anonymize_payload
# ---------------------------------------------------------------------------


class TestAnonymizePayload:
    def test_login_request(self):
        payload = {
            "sl_cmd": "sl_registration_req",
            "sl_login": "admin",
            "sl_pwd": "secret123",
        }
        result = anonymize_payload(payload)
        assert result["sl_cmd"] == "sl_registration_req"
        assert result["sl_login"] == "ad***"
        assert result["sl_pwd"] == "***"

    def test_data_request_with_nested_client(self):
        payload = {
            "sl_appl_msg": {
                "cseq": 5,
                "client": "5046b5a9",
                "cmd_name": "light_list_req",
            },
            "sl_client_id": "5046b5a9",
            "sl_cmd": "sl_data_req",
            "sl_appl_msg_type": "domo",
        }
        result = anonymize_payload(payload)
        assert result["sl_client_id"] == "504***"
        assert result["sl_appl_msg"]["client"] == "504***"
        assert result["sl_appl_msg"]["cmd_name"] == "light_list_req"
        assert result["sl_appl_msg"]["cseq"] == 5

    def test_password_change_request(self):
        payload = {
            "sl_cmd": "sl_user_pwd_change_req",
            "sl_login": "admin",
            "sl_pwd": "oldpass",
            "sl_new_pwd": "newpass",
        }
        result = anonymize_payload(payload)
        assert result["sl_login"] == "ad***"
        assert result["sl_pwd"] == "***"
        assert result["sl_new_pwd"] == "***"

    def test_feature_list_response(self):
        payload = {
            "cmd_name": "feature_list_resp",
            "keycode": "0000FFFF9999AAAA",
            "serial": "0011ffee",
            "swver": "1.2.3",
            "sl_data_ack_reason": 0,
        }
        result = anonymize_payload(payload)
        assert result["keycode"] == "0000FFFF********"
        assert result["serial"] == "001*****"
        assert result["swver"] == "1.2.3"

    def test_users_list_response(self):
        payload = {
            "sl_cmd": "sl_users_list_resp",
            "sl_data_ack_reason": 0,
            "sl_client_id": "75c6c33a",
            "sl_users_list": [{"name": "admin"}],
        }
        result = anonymize_payload(payload)
        assert result["sl_client_id"] == "75c***"
        assert result["sl_users_list"][0]["name"] == "ad***"

    def test_camera_response_with_credentials(self):
        payload = {
            "cmd_name": "tvcc_cameras_list_resp",
            "array": [
                {
                    "id": 1,
                    "name": "Front Door Camera",
                    "uri": "http://user:pass@192.168.1.100:8080/stream.swf",
                    "uri_still": "http://user:pass@192.168.1.100:8080/snapshot.jpg",
                }
            ],
        }
        result = anonymize_payload(payload)
        cam = result["array"][0]
        assert "***:***@" in cam["uri"]
        assert "***:***@" in cam["uri_still"]
        assert cam["name"] == "Front Door Camera"  # device name NOT redacted

    def test_deep_copy_no_mutation(self):
        payload = {
            "sl_login": "admin",
            "sl_pwd": "secret",
            "nested": {"sl_client_id": "abc123"},
        }
        anonymize_payload(payload)
        assert payload["sl_login"] == "admin"
        assert payload["sl_pwd"] == "secret"
        assert payload["nested"]["sl_client_id"] == "abc123"

    def test_empty_dict(self):
        assert anonymize_payload({}) == {}

    def test_nested_list_of_dicts(self):
        payload = {
            "result": [
                {"cmd_name": "light_switch_ind", "act_id": 1, "status": 1},
                {"cmd_name": "light_switch_ind", "act_id": 2, "status": 0},
            ]
        }
        result = anonymize_payload(payload)
        assert result["result"][0]["act_id"] == 1
        assert result["result"][1]["status"] == 0

    def test_add_user_request(self):
        payload = {
            "sl_client_id": "abcdef12",
            "sl_cmd": "sl_add_user_req",
            "sl_login": "newuser",
            "sl_pwd": "newpassword",
        }
        result = anonymize_payload(payload)
        assert result["sl_client_id"] == "abc***"
        assert result["sl_login"] == "ne***"
        assert result["sl_pwd"] == "***"


# ---------------------------------------------------------------------------
# log_traffic
# ---------------------------------------------------------------------------


class TestLogTraffic:
    def test_post_with_request_and_response(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aiocamedomotic.traffic"):
            log_traffic(
                "POST",
                "http://192.168.1.100/domo/",
                {"sl_cmd": "sl_registration_req", "sl_login": "admin", "sl_pwd": "x"},
                {"sl_client_id": "5046b5a9", "sl_data_ack_reason": 0},
                200,
                42.5,
            )

        assert len(caplog.records) == 1
        text = caplog.records[0].message
        assert "HTTP POST" in text
        assert "192.168.1.***" in text
        assert "status=200" in text
        assert "42.5ms" in text
        assert '"sl_login":"ad***"' in text
        assert '"sl_pwd":"***"' in text
        assert '"sl_client_id":"504***"' in text

    def test_get_with_none_payloads(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aiocamedomotic.traffic"):
            log_traffic("GET", "http://192.168.1.100/domo/", None, None, None, 10.0)

        assert len(caplog.records) == 1
        text = caplog.records[0].message
        assert "HTTP GET" in text
        assert "-->" not in text
        assert "<--" not in text

    def test_elapsed_time_in_output(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aiocamedomotic.traffic"):
            log_traffic("POST", "http://host/domo/", {}, {}, 200, 123.456)

        text = caplog.records[0].message
        assert "123.5ms" in text

    def test_exception_in_anonymization_swallowed(self, caplog):
        with (
            patch(
                "aiocamedomotic.anonymizer.anonymize_payload",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.WARNING, logger="aiocamedomotic.traffic"),
        ):
            log_traffic("POST", "http://host/", {"sl_pwd": "x"}, None, 200, 1.0)

        assert any("Traffic logging failed" in r.message for r in caplog.records)

    def test_logger_name(self):
        assert TRAFFIC_LOGGER.name == "aiocamedomotic.traffic"

    def test_non_dict_response(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aiocamedomotic.traffic"):
            log_traffic("POST", "http://host/domo/", None, "plain text", 200, 5.0)

        text = caplog.records[0].message
        assert "<-- plain text" in text
