# Use Python 3.9.23 as base image
FROM python:3.9.23-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry: Don't create virtual environment
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml ./

# Copy source code
COPY src/ ./src/

# Copy config
COPY config/ ./config/

# Copy models
COPY models/ ./models/

# Copy tasks
COPY tasks/ ./tasks/

# Copy logs
COPY logs/ ./logs/

# Install dependencies
RUN poetry install --only=main

# Expose port
EXPOSE 9999

# Command to run the application
CMD ["poetry", "run", "server"]