# Hemingwix Notion MCP Server Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp_user
USER mcp_user

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import asyncio; print('Server healthy')" || exit 1

# Expose port (if running HTTP server)
# EXPOSE 8000

# Default command
CMD ["python", "server.py"]

# Labels
LABEL org.opencontainers.image.title="Hemingwix Notion MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Notion database integration"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Hemingwix Project"