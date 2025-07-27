"""
Constants for the MCP server.

This module contains constant values used throughout the application.
"""

# Server defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 30

# File operation limits
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_ITEMS = 1000

# HTTP client defaults
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_HTTP_MAX_REDIRECTS = 10
DEFAULT_USER_AGENT = "MCP-Server-Template/1.0.0"

# Rate limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"

# Security
SAFE_FILE_EXTENSIONS = [
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".xml",
    ".csv",
    ".log",
    ".conf",
    ".ini",
]

DANGEROUS_FILE_EXTENSIONS = [
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".vbs",
    ".scr",
    ".pif",
    ".com",
    ".dll",
    ".so",
    ".dylib",
    ".app",
    ".dmg",
    ".pkg",
]

# MCP Protocol
MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_CAPABILITIES = [
    "tools",
    "resources",
    "prompts",
    "logging",
]

# Tool categories
TOOL_CATEGORIES = {
    "system": ["hello_world", "get_server_info"],
    "text": ["echo_message", "format_text", "validate_email"],
    "math": ["calculate_sum", "generate_random_data"],
    "file": ["read_file_content", "list_directory", "get_file_info"],
    "http": ["fetch_url", "post_data", "put_data", "delete_resource"],
}

# Error messages
ERROR_MESSAGES = {
    "invalid_url": "Invalid URL format",
    "file_not_found": "File not found",
    "permission_denied": "Permission denied",
    "file_too_large": "File too large",
    "invalid_json": "Invalid JSON format",
    "connection_error": "Connection error",
    "timeout_error": "Request timeout",
    "validation_error": "Validation error",
    "server_error": "Internal server error",
}

# Success messages
SUCCESS_MESSAGES = {
    "file_read": "File read successfully",
    "directory_listed": "Directory listed successfully",
    "url_fetched": "URL fetched successfully",
    "data_posted": "Data posted successfully",
    "server_started": "Server started successfully",
}

# Environment variables
ENV_VARS = {
    "SERVER_NAME": "MCP_SERVER_NAME",
    "HOST": "MCP_HOST",
    "PORT": "MCP_PORT",
    "TRANSPORT": "MCP_TRANSPORT",
    "LOG_LEVEL": "MCP_LOG_LEVEL",
    "DEBUG": "MCP_DEBUG",
    "ENVIRONMENT": "MCP_ENVIRONMENT",
}

# Validation patterns
PATTERNS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
    "ipv4": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
}

# Content types
CONTENT_TYPES = {
    "json": "application/json",
    "text": "text/plain",
    "html": "text/html",
    "xml": "application/xml",
    "csv": "text/csv",
    "yaml": "application/yaml",
    "form": "application/x-www-form-urlencoded",
    "multipart": "multipart/form-data",
}

# HTTP status codes
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}
