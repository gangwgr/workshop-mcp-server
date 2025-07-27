"""
Configuration settings for the MCP server.

This module provides centralized configuration management with environment
variable support, validation, and default values.
"""

import os
from typing import List, Optional

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    All settings can be overridden by environment variables with the same name.
    """

    # Server configuration
    SERVER_NAME: str = Field(
        default="MCP Server Template", description="Name of the MCP server"
    )
    SERVER_DESCRIPTION: str = Field(
        default="A template for creating Model Context Protocol servers",
        description="Description of the MCP server",
    )
    HOST: str = Field(default="127.0.0.1", description="Host to bind the server to")
    PORT: int = Field(default=8000, description="Port to bind the server to")
    TRANSPORT: str = Field(
        default="http", description="Transport method (stdio, http, streamable-http)"
    )

    # Dependencies for FastMCP
    DEPENDENCIES: List[str] = Field(
        default_factory=lambda: ["fastmcp", "httpx", "structlog"],
        description="List of dependencies for FastMCP",
    )

    # CORS configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"], description="List of allowed origins for CORS"
    )

    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json, text)")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")

    # Security settings
    MAX_REQUEST_SIZE: int = Field(
        default=10 * 1024 * 1024, description="Maximum request size in bytes"
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Rate limit requests per minute"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # File operations settings
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size for read operations"
    )
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default_factory=lambda: [
            ".txt",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".py",
            ".js",
            ".ts",
        ],
        description="List of allowed file extensions",
    )

    # HTTP client settings
    HTTP_TIMEOUT: int = Field(default=30, description="HTTP request timeout in seconds")
    HTTP_MAX_REDIRECTS: int = Field(
        default=10, description="Maximum number of HTTP redirects"
    )

    # Development settings
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    RELOAD: bool = Field(default=False, description="Enable auto-reload in development")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    @field_validator("TRANSPORT")
    @classmethod
    def validate_transport(cls, v):
        """Validate transport method."""
        valid_transports = ["stdio", "http", "streamable-http"]
        if v not in valid_transports:
            raise ValueError(f"TRANSPORT must be one of: {valid_transports}")
        return v

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"LOG_FORMAT must be one of: {valid_formats}")
        return v.lower()

    @field_validator("PORT")
    @classmethod
    def validate_port(cls, v):
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name."""
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of: {valid_environments}")
        return v.lower()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.HOST}:{self.PORT}"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
        validate_assignment=True,
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: The global settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.

    Returns:
        Settings: The reloaded settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
