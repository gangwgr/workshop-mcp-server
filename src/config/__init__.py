"""
Configuration package for MCP server.

This package contains configuration classes, environment variable handling,
and settings management.
"""

from .settings import Settings, get_settings
from .constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TIMEOUT

__all__ = [
    "Settings",
    "get_settings",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_TIMEOUT",
]
