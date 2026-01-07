"""
OpenAPI Schema Generator for Aragora API.

Generates OpenAPI 3.0 specification for all API endpoints.
"""

import json
from datetime import datetime
from typing import Any

# API version
API_VERSION = "1.0.0"

# OpenAPI schema components
COMMON_SCHEMAS = {
    "Error": {
        "type": "object",
        "properties": {
            "error": {"type": "string", "description": "Error message"},
            "code": {"type": "string", "description": "Error code"},
            "trace_id": {"type": "string", "description": "Request trace ID for debugging"},
        },
        "required": ["error"],
    },
    "PaginatedResponse": {
        "type": "object",
        "properties": {
            "total": {"type": "integer", "description": "Total items available"},
            "offset": {"type": "integer", "description": "Current offset"},
            "limit": {"type": "integer", "description": "Page size"},
            "has_more": {"type": "boolean", "description": "More items available"},
        },
    },
    "Agent": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Agent name"},
            "elo": {"type": "number", "description": "ELO rating"},
            "matches": {"type": "integer", "description": "Total matches played"},
            "wins": {"type": "integer", "description": "Total wins"},
            "losses": {"type": "integer", "description": "Total losses"},
        },
    },
    "Debate": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Debate ID"},
            "topic": {"type": "string", "description": "Debate topic/question"},
            "status": {"type": "string", "enum": ["active", "completed", "failed"]},
            "created_at": {"type": "string", "format": "date-time"},
            "messages": {"type": "array", "items": {"$ref": "#/components/schemas/Message"}},
        },
    },
    "Message": {
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
            "content": {"type": "string"},
            "agent": {"type": "string"},
            "round": {"type": "integer"},
            "timestamp": {"type": "string", "format": "date-time"},
        },
    },
    "HealthCheck": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
            "version": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "checks": {"type": "object", "additionalProperties": {"type": "boolean"}},
        },
    },
}

# Endpoint definitions
ENDPOINTS = {
    # Health & System
    "/api/health": {
        "get": {
            "tags": ["System"],
            "summary": "Health check",
            "description": "Get system health status for load balancers and monitoring",
            "responses": {
                "200": {"description": "System healthy", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HealthCheck"}}}},
                "503": {"description": "System unhealthy"},
            },
        },
    },
    "/api/health/detailed": {
        "get": {
            "tags": ["System"],
            "summary": "Detailed health check",
            "description": "Get detailed health status with component checks",
            "responses": {
                "200": {"description": "Detailed health information"},
            },
        },
    },
    "/api/nomic/state": {
        "get": {
            "tags": ["System"],
            "summary": "Get nomic loop state",
            "description": "Get current state of the nomic self-improvement loop",
            "responses": {"200": {"description": "Nomic state"}},
        },
    },
    # Agents
    "/api/agents": {
        "get": {
            "tags": ["Agents"],
            "summary": "List all agents",
            "description": "Get list of all known agents",
            "parameters": [
                {"name": "include_stats", "in": "query", "schema": {"type": "boolean", "default": False}, "description": "Include ELO stats"},
            ],
            "responses": {
                "200": {
                    "description": "List of agents",
                    "content": {"application/json": {"schema": {"type": "object", "properties": {"agents": {"type": "array", "items": {"$ref": "#/components/schemas/Agent"}}, "total": {"type": "integer"}}}}},
                },
            },
        },
    },
    "/api/leaderboard": {
        "get": {
            "tags": ["Agents"],
            "summary": "Get agent leaderboard",
            "description": "Get agents ranked by ELO rating",
            "parameters": [
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}},
                {"name": "domain", "in": "query", "schema": {"type": "string"}, "description": "Filter by expertise domain"},
            ],
            "responses": {"200": {"description": "Agent rankings"}},
        },
    },
    "/api/agent/{name}/profile": {
        "get": {
            "tags": ["Agents"],
            "summary": "Get agent profile",
            "description": "Get detailed profile for an agent",
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "responses": {
                "200": {"description": "Agent profile"},
                "404": {"description": "Agent not found"},
            },
        },
    },
    "/api/agent/{name}/history": {
        "get": {
            "tags": ["Agents"],
            "summary": "Get agent match history",
            "parameters": [
                {"name": "name", "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
            ],
            "responses": {"200": {"description": "Match history"}},
        },
    },
    # Debates
    "/api/debates": {
        "get": {
            "tags": ["Debates"],
            "summary": "List debates",
            "description": "Get list of all debates",
            "parameters": [
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}},
            ],
            "responses": {"200": {"description": "List of debates"}},
        },
    },
    "/api/debates/{id}": {
        "get": {
            "tags": ["Debates"],
            "summary": "Get debate by ID",
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "responses": {
                "200": {"description": "Debate details", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Debate"}}}},
                "404": {"description": "Debate not found"},
            },
        },
    },
    "/api/debates/{id}/messages": {
        "get": {
            "tags": ["Debates"],
            "summary": "Get debate messages",
            "description": "Get paginated message history for a debate",
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50, "maximum": 200}},
                {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
            ],
            "responses": {"200": {"description": "Paginated messages"}},
        },
    },
    "/api/debates/{id}/convergence": {
        "get": {
            "tags": ["Debates"],
            "summary": "Get convergence status",
            "description": "Check if debate has reached semantic convergence",
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "responses": {"200": {"description": "Convergence status"}},
        },
    },
    "/api/debates/{id}/citations": {
        "get": {
            "tags": ["Debates"],
            "summary": "Get evidence citations",
            "description": "Get grounded verdict with evidence citations",
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "responses": {"200": {"description": "Citations and grounding score"}},
        },
    },
    "/api/debates/{id}/fork": {
        "post": {
            "tags": ["Debates"],
            "summary": "Fork debate",
            "description": "Create a counterfactual branch from a specific round",
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "requestBody": {
                "content": {"application/json": {"schema": {"type": "object", "properties": {"branch_point": {"type": "integer"}, "new_premise": {"type": "string"}}}}},
            },
            "responses": {
                "201": {"description": "Forked debate created"},
                "400": {"description": "Invalid branch point"},
            },
        },
    },
    # Analytics
    "/api/analytics/disagreement": {
        "get": {
            "tags": ["Analytics"],
            "summary": "Disagreement analysis",
            "description": "Get metrics on agent disagreement patterns",
            "responses": {"200": {"description": "Disagreement statistics"}},
        },
    },
    "/api/analytics/consensus": {
        "get": {
            "tags": ["Analytics"],
            "summary": "Consensus statistics",
            "description": "Get statistics on consensus formation",
            "responses": {"200": {"description": "Consensus metrics"}},
        },
    },
    # Flips
    "/api/flips/recent": {
        "get": {
            "tags": ["Insights"],
            "summary": "Recent position flips",
            "description": "Get recent instances of agents changing positions",
            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}}],
            "responses": {"200": {"description": "Recent flips"}},
        },
    },
    "/api/flips/summary": {
        "get": {
            "tags": ["Insights"],
            "summary": "Flip summary",
            "description": "Get summary statistics on position flips",
            "responses": {"200": {"description": "Flip summary"}},
        },
    },
    # Pulse/Trending
    "/api/pulse/trending": {
        "get": {
            "tags": ["Pulse"],
            "summary": "Trending topics",
            "description": "Get current trending debate topics",
            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}}],
            "responses": {"200": {"description": "Trending topics"}},
        },
    },
    "/api/pulse/suggest": {
        "get": {
            "tags": ["Pulse"],
            "summary": "Suggest debate topic",
            "description": "Get AI-suggested debate topic based on trends",
            "parameters": [{"name": "category", "in": "query", "schema": {"type": "string"}}],
            "responses": {"200": {"description": "Suggested topic"}},
        },
    },
    # Metrics
    "/api/metrics": {
        "get": {
            "tags": ["Monitoring"],
            "summary": "System metrics",
            "description": "Get system performance metrics",
            "responses": {"200": {"description": "Metrics data"}},
        },
    },
    "/api/metrics/prometheus": {
        "get": {
            "tags": ["Monitoring"],
            "summary": "Prometheus metrics",
            "description": "Get metrics in Prometheus format",
            "responses": {"200": {"description": "Prometheus-formatted metrics", "content": {"text/plain": {}}}},
        },
    },
}


def generate_openapi_schema() -> dict[str, Any]:
    """Generate complete OpenAPI 3.0 schema."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Aragora API",
            "description": "Multi-agent debate framework API for Aragora LiveWire",
            "version": API_VERSION,
            "contact": {
                "name": "Aragora Team",
            },
            "license": {
                "name": "MIT",
            },
        },
        "servers": [
            {"url": "http://localhost:8080", "description": "Development server"},
            {"url": "https://api.aragora.dev", "description": "Production server"},
        ],
        "tags": [
            {"name": "System", "description": "Health checks and system status"},
            {"name": "Agents", "description": "Agent management and statistics"},
            {"name": "Debates", "description": "Debate operations and queries"},
            {"name": "Analytics", "description": "Analysis and statistics"},
            {"name": "Insights", "description": "Position flips and patterns"},
            {"name": "Pulse", "description": "Trending topics and suggestions"},
            {"name": "Monitoring", "description": "Metrics and monitoring"},
        ],
        "paths": ENDPOINTS,
        "components": {
            "schemas": COMMON_SCHEMAS,
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API token authentication",
                },
            },
        },
        "security": [{"bearerAuth": []}],
    }


def get_openapi_json() -> str:
    """Get OpenAPI schema as JSON string."""
    return json.dumps(generate_openapi_schema(), indent=2)


def get_openapi_yaml() -> str:
    """Get OpenAPI schema as YAML string."""
    try:
        import yaml
        return yaml.dump(generate_openapi_schema(), default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON if PyYAML not installed
        return get_openapi_json()


# Endpoint to serve OpenAPI spec
def handle_openapi_request(format: str = "json") -> tuple[str, str]:
    """Handle request for OpenAPI spec.

    Returns:
        Tuple of (content, content_type)
    """
    if format == "yaml":
        return get_openapi_yaml(), "application/yaml"
    return get_openapi_json(), "application/json"


def extract_endpoints_from_handlers() -> dict[str, dict]:
    """Extract endpoints from handler docstrings dynamically."""
    import re
    from pathlib import Path

    handlers_dir = Path(__file__).parent / "handlers"
    endpoints = {}

    if not handlers_dir.exists():
        return endpoints

    # Pattern: - GET /api/path - Description
    pattern = r"- (GET|POST|PUT|DELETE|PATCH) (/api/[^\s]+)\s*-\s*(.+)"

    for handler_file in handlers_dir.glob("*.py"):
        if handler_file.name.startswith("_"):
            continue

        try:
            content = handler_file.read_text()
        except Exception:
            continue

        for match in re.finditer(pattern, content):
            method = match.group(1).lower()
            path = match.group(2)
            description = match.group(3).strip()

            # Normalize path parameters: :param -> {param}, * -> {id}
            path = re.sub(r":(\w+)", r"{\1}", path)
            path = re.sub(r"\*", "{id}", path)

            # Determine tag from handler file
            tag = handler_file.stem.replace("_", " ").title()

            if path not in endpoints:
                endpoints[path] = {}

            # Extract path parameters
            params = []
            for param_match in re.finditer(r"\{(\w+)\}", path):
                params.append({
                    "name": param_match.group(1),
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                })

            endpoint_def = {
                "tags": [tag],
                "summary": description,
                "description": description,
                "responses": {
                    "200": {"description": "Successful response"},
                    "400": {"description": "Bad request", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "401": {"description": "Unauthorized"},
                    "500": {"description": "Server error"},
                },
            }

            if params:
                endpoint_def["parameters"] = params

            if method in ("post", "put", "patch"):
                endpoint_def["requestBody"] = {
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }

            endpoints[path][method] = endpoint_def

    return endpoints


def generate_full_openapi_schema() -> dict[str, Any]:
    """Generate complete OpenAPI schema including dynamically extracted endpoints."""
    base_schema = generate_openapi_schema()

    # Add dynamically extracted endpoints
    dynamic_endpoints = extract_endpoints_from_handlers()
    for path, methods in dynamic_endpoints.items():
        if path not in base_schema["paths"]:
            base_schema["paths"][path] = methods
        else:
            # Merge methods
            for method, spec in methods.items():
                if method not in base_schema["paths"][path]:
                    base_schema["paths"][path][method] = spec

    return base_schema


def save_openapi_schema(output_path: str = "docs/api/openapi.json") -> tuple[str, int]:
    """Save complete OpenAPI schema to file.

    Returns:
        Tuple of (file_path, endpoint_count)
    """
    from pathlib import Path

    schema = generate_full_openapi_schema()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        json.dump(schema, f, indent=2)

    endpoint_count = sum(len(methods) for methods in schema["paths"].values())
    return str(output.absolute()), endpoint_count
