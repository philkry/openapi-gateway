# OpenAPI Gateway

A FastAPI-based OpenAPI Gateway that provides request validation and forwarding based on OpenAPI specifications. This gateway acts as a protective layer in front of your upstream services, ensuring all incoming requests conform to your API specifications before they reach your backend services.

## Features

- **OpenAPI Specification Validation**: Validates your API specification on startup
- **Request Validation**:
  - Query parameter validation against OpenAPI spec
  - Request body validation for JSON payloads
  - Content-type validation
  - Parameter enumeration validation
- **Dynamic Route Registration**: Automatically registers routes based on your OpenAPI specification
- **Request Forwarding**: Forwards validated requests to your upstream service
- **Comprehensive Logging**: Configurable logging levels for debugging and monitoring
- **Docker Support**: Easy deployment using Docker

## Configuration

The OpenAPI Gateway is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAPI_SPEC_PATH` | Path to your OpenAPI specification file | `openapi.json` |
| `UPSTREAM_SERVER_URL` | URL of your upstream service | `https://example.com/api` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

## Docker Deployment

### Using Pre-built Image

```bash
# Pull the latest version
docker pull ghcr.io/philkry/openapi-gateway:v1.0.0

# Run the container
docker run -d \
  -p 8000:8000 \
  -v /path/to/your/openapi.json:/app/openapi.json \
  -e UPSTREAM_SERVER_URL=https://your-api.com \
  -e LOG_LEVEL=INFO \
  ghcr.io/philkry/openapi-gateway:latest
```

### Building Locally

```bash
# Clone the repository
git clone https://github.com/philkry/openapi-gateway.git
cd openapi-gateway

# Build the image
docker build -t openapi-gateway .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v /path/to/your/openapi.json:/app/openapi.json \
  -e UPSTREAM_SERVER_URL=https://your-api.com \
  openapi-gateway
```

## OpenAPI Specification

Place your OpenAPI specification in a file named `openapi.json` (or specify a different path using `OPENAPI_SPEC_PATH`). The OpenAPI Gateway will:

1. Validate the specification on startup
2. Register routes dynamically based on the paths defined
3. Validate incoming requests against the specification

Example OpenAPI specification:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Sample API",
    "version": "1.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "parameters": [
          {
            "name": "role",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "enum": ["admin", "user"]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response"
          }
        }
      }
    }
  }
}
```

## Request Flow

1. Client sends request to OpenAPI Gateway
2. Gateway validates request against OpenAPI specification:
   - Validates path parameters
   - Validates query parameters
   - Validates request body (if applicable)
   - Checks content-type headers
3. If validation passes, request is forwarded to upstream service
4. Response from upstream service is returned to client
5. If validation fails, gateway returns appropriate error response

## Error Handling

The OpenAPI Gateway provides detailed error messages for various scenarios:

- `400 Bad Request`: Invalid request parameters or body
- `415 Unsupported Media Type`: Incorrect content-type
- `502 Bad Gateway`: Upstream service communication error

## Development

Requirements:
- Python 3.9+
- FastAPI
- httpx
- openapi-spec-validator
- uvicorn

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python openapi_gateway.py
```

## Releasing New Versions

The OpenAPI Gateway uses semantic versioning. To release a new version:

1. Create and push a new tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. The GitHub Action will automatically:
   - Build the Docker image
   - Push it to GitHub Container Registry with tags:
     * Full version (v1.0.0)
     * Minor version (v1.0)
     * Major version (v1)
