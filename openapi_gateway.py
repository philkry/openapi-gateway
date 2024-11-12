import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.routing import APIRoute
import httpx
from openapi_spec_validator import validate_spec
from jsonschema import validate as jsonschema_validate, ValidationError


# Set up logging based on environment variable
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Configure logging to stdout
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

def load_openapi_spec(spec_path):
    logger.info(f"Loading OpenAPI specification from {spec_path}")
    try:
        with open(spec_path, 'r') as f:
            spec = json.load(f)
        validate_spec(spec)  # Validate the OpenAPI spec structure
        logger.info("OpenAPI specification validated successfully")
        return spec
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load OpenAPI specification: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to validate OpenAPI specification: {str(e)}")
        raise

def find_operation(path: str, method: str, spec: dict):
    """Find the operation definition for a given path and method."""
    # Normalize path parameters
    path_parts = path.split('/')
    for path_template, path_item in spec['paths'].items():
        template_parts = path_template.split('/')
        if len(path_parts) != len(template_parts):
            continue

        matches = True
        for part, template in zip(path_parts, template_parts):
            if template.startswith('{') and template.endswith('}'):
                continue
            if part != template:
                matches = False
                break

        if matches and method.lower() in path_item:
            return path_item[method.lower()]

    return None

def validate_parameters(request: Request, operation_def: dict):
    query_params = dict(request.query_params)
    if 'parameters' in operation_def:
        for param in operation_def['parameters']:
            if param['in'] == 'query':
                param_name = param['name']

                if param['required'] and param_name not in query_params:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required query parameter: {param_name}"
                    )

                if param_name in query_params:
                    value = query_params[param_name]
                    if 'enum' in param['schema'] and value not in param['schema']['enum']:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid value for {param_name}. Must be one of: {', '.join(param['schema']['enum'])}"
                        )

async def validate_request_body(request: Request, operation_def: dict):
    content_type = request.headers.get('content-type')
    if request.method in ["POST", "PUT", "PATCH"] and 'requestBody' in operation_def:
        request_body_spec = operation_def['requestBody']

        if 'application/json' in request_body_spec['content']:
            if content_type != "application/json":
                raise HTTPException(
                    status_code=415,
                    detail="Unsupported Media Type. Expected 'application/json'"
                )
            try:
                request_body = await request.json()
                schema = request_body_spec['content']['application/json']['schema']
                jsonschema_validate(instance=request_body, schema=schema)
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Invalid request body: {str(e)}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON body")

@app.on_event("startup")
async def startup_event():
    openapi_spec_path = os.getenv("OPENAPI_SPEC_PATH", "openapi.json")
    app.openapi_spec = load_openapi_spec(openapi_spec_path)
    logger.info("API Gateway initialized")

    # Register routes
    for path, path_def in app.openapi_spec["paths"].items():
        for method, operation_def in path_def.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue

            logger.info(f"Registering route: {method.upper()} {path}")

            async def endpoint(request: Request, op_def=operation_def):
                # Validate against the OpenAPI spec
                validate_parameters(request, op_def)
                await validate_request_body(request, op_def)
                return await forward_request(request)

            app.router.add_api_route(
                path,
                endpoint=endpoint,
                methods=[method.upper()],
            )

async def forward_request(request: Request) -> Response:
    upstream_url = os.getenv("UPSTREAM_SERVER_URL", "https://example.com/api")
    full_url = f"{upstream_url}{request.url.path}"
    if request.url.query:
        full_url = f"{full_url}?{request.url.query}"

    headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=await request.body()
            )
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        logger.error(f"Error forwarding request: {str(e)}")
        raise HTTPException(status_code=502, detail="Bad Gateway")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)