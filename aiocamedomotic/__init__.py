# SPDX-FileCopyrightText: 2024 - GitHub user: fredericks1982
# SPDX-License-Identifier: Apache-2.0
"""
The **CAME Domotic Library** provides a streamlined Python interface for
interacting with CAME Domotic plants, much like the official *CAME Domotic app*.

This library is designed to simplify the management of domotic devices by abstracting
the complexities of the CAME Domotic API.

Note:
    This library is independently developed and is not affiliated with, endorsed by,
    or supported by CAME. It may not be compatible with all CAME Domotic systems.
    While this library is stable and publicly released, it comes with no guarantees.
    Use at your own risk. This library is not intended for use in critical systems,
    such as security or life-support systems.
"""

from __future__ import annotations

import logging
import sys
from importlib.metadata import PackageNotFoundError, version

from .auth import Auth  # noqa: F401
from .came_domotic_api import CameDomoticAPI  # noqa: F401
from .const import CAME_MAC_PREFIXES, ServerFeature  # noqa: F401
from .errors import CameDomoticServerTimeoutError  # noqa: F401
from .utils import LOGGER, async_is_came_endpoint  # noqa: F401

# Get the package version
try:
    __version__ = version(__package__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"

# region Logging

# Configure the package logger


_formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s",
)
_formatter.default_msec_format = "%s.%03d"
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_formatter)
LOGGER.addHandler(_console_handler)
LOGGER.setLevel(logging.WARNING)


def get_logger() -> logging.Logger:
    """
    Allows to set the log level and other properties from the calling code.

    Returns:
        Logger: The package logger
    """
    return LOGGER


# endregion
