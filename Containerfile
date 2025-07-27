FROM registry.access.redhat.com/ubi9/python-312:latest

# --------------------------------------------------------------------------------------------------
# set the working directory to /app
# --------------------------------------------------------------------------------------------------

WORKDIR /app

# --------------------------------------------------------------------------------------------------
# Copy manifest files and install python packages
# --------------------------------------------------------------------------------------------------

COPY pyproject.toml /app/pyproject.toml
RUN pip install uv
RUN uv venv
RUN source /app/.venv/bin/activate
RUN uv pip install -r pyproject.toml
RUN wget https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem \
    && cat Current-IT-Root-CAs.pem >> `/app/.venv/bin/python -m certifi`

# --------------------------------------------------------------------------------------------------
# copy source code and files
# --------------------------------------------------------------------------------------------------

COPY template_mcp_server /app/template_mcp_server

# --------------------------------------------------------------------------------------------------
# Set PYTHONPATH to include /app
# --------------------------------------------------------------------------------------------------

ENV PYTHONPATH=/app


# --------------------------------------------------------------------------------------------------
# add entrypoint for the container
# --------------------------------------------------------------------------------------------------

CMD ["/app/.venv/bin/python", "-m", "template_mcp_server.src.main"]
