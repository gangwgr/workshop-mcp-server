FROM registry.access.redhat.com/ubi9/python-312:latest

# Set working directory (creates /app with default user permissions)
WORKDIR /app

# Copy dependencies and install packages
COPY pyproject.toml /app/pyproject.toml
RUN pip install uv
RUN uv venv ~/.venv
RUN uv pip install --python ~/.venv/bin/python -r pyproject.toml

# Download Red Hat certificates (optional, may fail outside corporate network)
RUN wget https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem -O /tmp/certs.pem 2>/dev/null \
    && cat /tmp/certs.pem >> `~/.venv/bin/python -m certifi` \
    && rm -f /tmp/certs.pem \
    || echo "Red Hat certificate download skipped (not in corporate network)"

# Copy source code
COPY template_mcp_server /app/template_mcp_server

# Set Python path to include working directory
ENV PYTHONPATH=/app

# Set entrypoint to run the application
CMD ["/opt/app-root/src/.venv/bin/python", "-m", "template_mcp_server.src.main"]
