FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # Application
    APP_HOME=/app \
    PATH="/home/appuser/.local/bin:${PATH}"

# Create and set working directory
WORKDIR ${APP_HOME}

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .

# Install Python packages as non-root user
USER appuser
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Create necessary directories with correct permissions
RUN mkdir -p ${APP_HOME}/data ${APP_HOME}/logs

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]