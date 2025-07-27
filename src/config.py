"""
Simple configuration for the FastMCP template server.
"""

import os
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    """Simple server settings."""
    server_name: str = "FastMCP Template"
    debug: bool = False
    log_level: str = "INFO"
    
    # Optional file access settings
    allowed_paths: list[str] = ["."]  # Restrict file access to current directory
    max_file_size: int = 10 * 1024 * 1024  # 10MB limit
    
    class Config:
        env_prefix = "MCP_"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings