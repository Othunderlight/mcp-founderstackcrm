
# Stage 1: Build stage to install dependencies
FROM python:3.11-slim as builder

# Install uv
RUN pip install uv

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Define environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8081"]
