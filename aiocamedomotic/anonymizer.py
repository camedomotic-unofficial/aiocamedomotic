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

"""Anonymization utilities for HTTP traffic logging.

This module provides automatic redaction of sensitive fields in CAME Domotic
API request and response payloads, enabling safe sharing of traffic logs
for debugging purposes.

The traffic logger (``aiocamedomotic.traffic``) is a child of the main
library logger and can be configured independently::

    import logging
    logging.getLogger("aiocamedomotic.traffic").setLevel(logging.DEBUG)
"""

from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

TRAFFIC_LOGGER = logging.getLogger(f"{__package__}.traffic")
"""Dedicated logger for HTTP traffic. Enable at DEBUG level to see
anonymized request/response payloads with elapsed times."""

# ---------------------------------------------------------------------------
# Sensitive field definitions
# ---------------------------------------------------------------------------

# Fields whose values are fully replaced with "***"
_FULL_REDACT_FIELDS: frozenset[str] = frozenset({"sl_pwd", "sl_new_pwd"})

# Fields whose values are partially shown: (chars_to_keep, mask_suffix)
_PARTIAL_REDACT_FIELDS: dict[str, tuple[int, str]] = {
    "sl_login": (2, "***"),
    "sl_client_id": (3, "***"),
    "client": (3, "***"),
    "keycode": (8, "********"),
    "serial": (3, "*****"),
}

# Fields that may contain URIs with embedded credentials
_URI_FIELDS: frozenset[str] = frozenset({"uri", "uri_still"})

# IPv4 pattern for host anonymization
_IPV4_RE = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.)\d{1,3}$")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _partial_redact(value: str, keep: int, mask: str) -> str:
    """Return a partially redacted string.

    If the value is shorter than *keep*, it is fully redacted to ``"***"``
    to avoid leaking short values entirely.
    """
    if len(value) < keep:
        return "***"
    return value[:keep] + mask


def _anonymize_uri(uri: str) -> str:
    """Redact embedded credentials in a URI.

    If the URI contains ``user:pass@host``, the userinfo portion is replaced
    with ``***:***``. URIs without credentials are returned unchanged.
    """
    if not uri:
        return uri
    try:
        parts = urlsplit(uri)
        if "@" in (parts.netloc or ""):
            # Rebuild netloc without credentials
            host_port = parts.netloc.rsplit("@", 1)[1]
            clean_netloc = f"***:***@{host_port}"
            return urlunsplit(
                (parts.scheme, clean_netloc, parts.path, parts.query, parts.fragment)
            )
        return uri
    except Exception:  # pylint: disable=broad-except
        return "<uri-redacted>"


def _anonymize_host(host: str) -> str:
    """Partially redact a host string.

    - IPv4: replaces the last octet (``192.168.1.100`` → ``192.168.1.***``).
    - Hostname: keeps the first segment (``came-server.local`` → ``came-server.***``).
    - Single-segment, empty, or unparsable: returns ``***``.
    """
    if not host:
        return "***"

    ipv4_match = _IPV4_RE.match(host)
    if ipv4_match:
        return ipv4_match.group(1) + "***"

    if "." in host:
        first_segment = host.split(".", 1)[0]
        return f"{first_segment}.***"

    return "***"


def _anonymize_url(url: str) -> str:
    """Redact the host portion of a URL while preserving scheme, port, and path."""
    if not url:
        return url
    try:
        parts = urlsplit(url)
        hostname = parts.hostname or ""
        anon_host = _anonymize_host(hostname)

        # Reconstruct netloc with anonymized host but preserve port
        anon_netloc = f"{anon_host}:{parts.port}" if parts.port else anon_host

        return urlunsplit(
            (parts.scheme, anon_netloc, parts.path, parts.query, parts.fragment)
        )
    except Exception:  # pylint: disable=broad-except
        return "<url-redacted>"


def _anonymize_value(  # pylint: disable=too-many-return-statements
    key: str, value: Any
) -> Any:
    """Return an anonymized version of *value* based on *key*.

    Dispatches to full redaction, partial redaction, URI sanitization, or
    special-case handling for ``sl_users_list``.
    """
    if key in _FULL_REDACT_FIELDS:
        return "***" if isinstance(value, str) else value

    if key in _PARTIAL_REDACT_FIELDS:
        if isinstance(value, str):
            keep, mask = _PARTIAL_REDACT_FIELDS[key]
            return _partial_redact(value, keep, mask)
        return value

    if key in _URI_FIELDS:
        if isinstance(value, str):
            return _anonymize_uri(value)
        return value

    # Context-aware: only redact "name" inside sl_users_list items
    if key == "sl_users_list" and isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                item_copy = item.copy()
                if "name" in item_copy and isinstance(item_copy["name"], str):
                    item_copy["name"] = _partial_redact(item_copy["name"], 2, "***")
                if "sl_login" in item_copy and isinstance(item_copy["sl_login"], str):
                    item_copy["sl_login"] = _partial_redact(
                        item_copy["sl_login"], 2, "***"
                    )
                result.append(item_copy)
            else:
                result.append(item)
        return result

    return value


def _anonymize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively anonymize sensitive fields in a dictionary (in-place)."""
    for key in list(data.keys()):
        value = data[key]

        # Apply field-level anonymization first
        value = _anonymize_value(key, value)
        data[key] = value

        # Recurse into nested structures
        if isinstance(value, dict):
            _anonymize_dict(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _anonymize_dict(item)

    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def anonymize_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of *data* with sensitive fields anonymized.

    This function never modifies the original dictionary. The following
    fields are redacted:

    - ``sl_pwd``, ``sl_new_pwd``: fully replaced with ``"***"``
    - ``sl_login``, ``sl_client_id``, ``client``, ``keycode``, ``serial``:
      partially masked (first N characters preserved)
    - ``uri``, ``uri_still``: embedded credentials redacted
    - ``sl_users_list`` items: ``name`` / ``sl_login`` partially masked

    Args:
        data: The request or response payload dictionary.

    Returns:
        A new dictionary with sensitive values redacted.
    """
    copied = copy.deepcopy(data)
    return _anonymize_dict(copied)


def log_traffic(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    method: str,
    url: str,
    request_payload: dict[str, Any] | None,
    response_payload: dict[str, Any] | None,
    http_status: int | None,
    elapsed_ms: float,
) -> None:
    """Log an HTTP request/response exchange with anonymized payloads.

    This function is fail-safe: any exception during anonymization or
    formatting is caught and logged as a warning, never propagated to
    the caller.

    Args:
        method: HTTP method (e.g., ``"POST"``, ``"GET"``).
        url: The full endpoint URL.
        request_payload: The request body dict, or ``None``.
        response_payload: The parsed response dict, or ``None``.
        http_status: The HTTP response status code, or ``None``.
        elapsed_ms: Elapsed time in milliseconds.
    """
    try:
        anon_url = _anonymize_url(url)

        status_part = f"status={http_status}, " if http_status is not None else ""
        header = f"HTTP {method} {anon_url} [{status_part}{elapsed_ms:.1f}ms]"

        lines = [header]

        if request_payload is not None:
            anon_request = anonymize_payload(request_payload)
            lines.append(f"--> {json.dumps(anon_request, separators=(',', ':'))}")

        if response_payload is not None:
            if isinstance(response_payload, dict):
                anon_response = anonymize_payload(response_payload)
                lines.append(f"<-- {json.dumps(anon_response, separators=(',', ':'))}")
            else:
                lines.append(f"<-- {response_payload!s}")

        TRAFFIC_LOGGER.debug("\n".join(lines))

    except Exception:  # pylint: disable=broad-except
        TRAFFIC_LOGGER.warning("Traffic logging failed", exc_info=True)
