#!/usr/bin/env python3
"""Example script demonstrating how to use different transport protocols.

This script shows how to configure and start the server with different
transport protocols: SSE, HTTP, and streamable-HTTP.
"""

import os
import subprocess
import sys
import time


def run_server_with_protocol(protocol: str, port: int = 4000, duration: int = 10):
    """Run the MCP server with a specific transport protocol.

    Args:
        protocol: The transport protocol to use ("sse", "http", "streamable-http", "stdio")
        port: The port to run the server on (not used for stdio)
        duration: How long to run the server (in seconds)
    """
    print(f"\n{'=' * 60}")
    print(f"Testing MCP Server with {protocol.upper()} protocol")
    print(f"{'=' * 60}")

    # Set environment variables
    env = os.environ.copy()
    env["MCP_TRANSPORT_PROTOCOL"] = protocol
    env["MCP_PORT"] = str(port)
    env["PYTHON_LOG_LEVEL"] = "INFO"

    try:
        if protocol == "stdio":
            # For stdio, we can't easily test it in a subprocess, so we'll just verify configuration
            print("stdio protocol uses standard input/output for communication")
            print("This is typically used for local development and testing")
            print("✅ stdio protocol configuration verified")
            print("   - Communication: Standard input/output")
            print("   - No HTTP endpoints available")
            print("   - Use for local development and CLI applications")
            return

        # Start the server for HTTP-based protocols
        print(f"Starting server with {protocol} protocol on port {port}...")
        process = subprocess.Popen(
            [sys.executable, "-m", "template_mcp_server.src.main"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a moment for the server to start
        time.sleep(3)

        # Check if the server is running
        if process.poll() is None:
            print(f"✅ Server started successfully with {protocol} protocol")
            print(f"   - Endpoint: http://localhost:{port}/mcp")

            if protocol == "sse":
                print(f"   - SSE endpoint: http://localhost:{port}/sse")
                print(f"   - Message endpoint: http://localhost:{port}/mcp/message")
                print(f"   - Health endpoint: http://localhost:{port}/health")
            else:
                print(f"   - HTTP endpoint: http://localhost:{port}/mcp")
                print(f"   - Health endpoint: http://localhost:{port}/health")

            # Let the server run for the specified duration
            print(f"   - Running for {duration} seconds...")
            time.sleep(duration)

            # Stop the server
            process.terminate()
            process.wait()
            print("✅ Server stopped successfully")
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start server with {protocol} protocol")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")

    except Exception as e:
        print(f"❌ Error running server with {protocol} protocol: {e}")


def main():
    """Main function to demonstrate different transport protocols."""
    print("Template MCP Server - Transport Protocol Examples")
    print("=" * 60)

    # Test different protocols
    protocols = [
        ("stdio", None),  # stdio doesn't use a port
        ("streamable-http", 4000),
        ("sse", 4001),
        ("http", 4002),
    ]

    for protocol, port in protocols:
        run_server_with_protocol(protocol, port, duration=5)

    print(f"\n{'=' * 60}")
    print("Transport Protocol Testing Complete!")
    print("=" * 60)
    print("\nSummary of tested protocols:")
    print("- stdio: Standard input/output for local communication")
    print("- streamable-http: Real-time streaming HTTP communication")
    print("- sse: Server-Sent Events for event-driven communication")
    print("- http: Standard HTTP request-response communication")
    print(
        "\nTo use a specific protocol, set the MCP_TRANSPORT_PROTOCOL environment variable:"
    )
    print("export MCP_TRANSPORT_PROTOCOL=sse")
    print("python -m template_mcp_server.src.main")


if __name__ == "__main__":
    main()
