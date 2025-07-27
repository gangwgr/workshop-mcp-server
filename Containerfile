# Use Red Hat UBI Python 3.12 image
FROM registry.access.redhat.com/ubi9/python-312:latest

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastmcp pydantic uvicorn

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command - exactly what works locally
CMD ["python", "-m", "src"] 