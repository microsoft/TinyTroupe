# Multi-stage Docker build for TinyTroupe
# Created by Devon (DevOps Engineer) - RovoDev Multi-Agent Team
# Optimized for production deployment with security and performance

# Build stage
FROM python:3.11-slim as builder

# Devon's optimization: Use build args for flexibility
ARG TINYTROUPE_VERSION=latest
ARG BUILD_ENV=production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash tinytroupe

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -e .

# Production stage
FROM python:3.11-slim as production

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash tinytroupe

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=tinytroupe:tinytroupe . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R tinytroupe:tinytroupe /app

# Switch to non-root user
USER tinytroupe

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import tinytroupe; print('TinyTroupe is healthy')" || exit 1

# Expose port for API
EXPOSE 8000

# Default command
CMD ["python", "-m", "tinytroupe.server"]