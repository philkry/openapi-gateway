FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY openapi_gateway.py .

# Set environment variables
ENV OPENAPI_SPEC_PATH=/app/openapi.json
ENV UPSTREAM_SERVER_URL=https://example.com/api

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "openapi_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
