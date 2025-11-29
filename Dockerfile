# Use logos-foundry as base image with all shared packages
FROM ghcr.io/c-daly/logos-foundry:0.1.0

WORKDIR /app/talos

# Copy only necessary files
COPY src/ ./src/
COPY pyproject.toml poetry.lock README.md ./

# Install talos dependencies
RUN poetry install --only main --no-root

# Expose Talos API port (if it has one - using 8002 based on pattern)
EXPOSE 8002

# Run the application
CMD ["poetry", "run", "python", "-m", "talos"]
