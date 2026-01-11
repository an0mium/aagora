"""Token extraction and authentication header utilities.

This module consolidates token extraction patterns used across
the server codebase, eliminating magic numbers like auth_header[7:].
"""

from __future__ import annotations

from typing import Any


def extract_bearer_token(auth_header: str | None) -> str | None:
    """Extract Bearer token from Authorization header.

    Args:
        auth_header: The Authorization header value

    Returns:
        The token string if present, None otherwise

    Examples:
        >>> extract_bearer_token("Bearer abc123")
        'abc123'
        >>> extract_bearer_token("Basic dXNlcjpwYXNz")
        None
        >>> extract_bearer_token(None)
        None
    """
    if not auth_header:
        return None
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # len("Bearer ") == 7
    return None


def extract_api_key_token(auth_header: str | None) -> str | None:
    """Extract API key from Authorization header with ApiKey prefix.

    Args:
        auth_header: The Authorization header value

    Returns:
        The API key string if present, None otherwise

    Examples:
        >>> extract_api_key_token("ApiKey xyz789")
        'xyz789'
        >>> extract_api_key_token("Bearer abc123")
        None
    """
    if not auth_header:
        return None
    if auth_header.startswith("ApiKey "):
        return auth_header[7:]  # len("ApiKey ") == 7
    return None


def extract_auth_token(auth_header: str | None) -> str | None:
    """Extract token from Authorization header (Bearer or ApiKey).

    Tries Bearer first, then ApiKey. Use this when you accept
    either authentication method.

    Args:
        auth_header: The Authorization header value

    Returns:
        The token string if present, None otherwise

    Examples:
        >>> extract_auth_token("Bearer abc123")
        'abc123'
        >>> extract_auth_token("ApiKey xyz789")
        'xyz789'
    """
    token = extract_bearer_token(auth_header)
    if token:
        return token
    return extract_api_key_token(auth_header)


def extract_token_from_headers(
    headers: dict[str, str],
    header_name: str = "Authorization",
) -> str | None:
    """Extract auth token from a headers dictionary.

    Handles case-insensitive header lookup and supports both
    Bearer and ApiKey prefixes.

    Args:
        headers: Dictionary of HTTP headers
        header_name: Header to extract from (default: Authorization)

    Returns:
        The token string if present, None otherwise

    Examples:
        >>> headers = {"Authorization": "Bearer abc123"}
        >>> extract_token_from_headers(headers)
        'abc123'
        >>> headers = {"authorization": "Bearer abc123"}  # lowercase
        >>> extract_token_from_headers(headers)
        'abc123'
    """
    # Try exact match first
    auth_header = headers.get(header_name)
    if auth_header:
        return extract_auth_token(auth_header)

    # Try case-insensitive lookup
    header_lower = header_name.lower()
    for key, value in headers.items():
        if key.lower() == header_lower:
            return extract_auth_token(value)

    return None


def extract_x_api_key(headers: dict[str, str]) -> str | None:
    """Extract API key from X-API-Key header.

    Some APIs use X-API-Key instead of Authorization.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        The API key if present, None otherwise

    Examples:
        >>> headers = {"X-API-Key": "my-secret-key"}
        >>> extract_x_api_key(headers)
        'my-secret-key'
    """
    # Try common variations
    for header in ["X-API-Key", "X-Api-Key", "x-api-key"]:
        if header in headers:
            return headers[header]

    # Case-insensitive fallback
    for key, value in headers.items():
        if key.lower() == "x-api-key":
            return value

    return None


def extract_token_from_request(request: Any) -> str | None:
    """Extract token from an aiohttp-like request object.

    Works with any request object that has a headers attribute
    returning a dict-like object.

    Args:
        request: Request object with headers attribute

    Returns:
        The token string if present, None otherwise
    """
    headers = getattr(request, "headers", {})
    if not headers:
        return None

    # Try Authorization header first
    token = extract_token_from_headers(dict(headers))
    if token:
        return token

    # Try X-API-Key header
    return extract_x_api_key(dict(headers))


def extract_token_from_websocket(websocket: Any) -> str | None:
    """Extract token from a WebSocket connection.

    Works with various WebSocket implementations that have
    headers available via request_headers or headers attribute.

    Args:
        websocket: WebSocket connection object

    Returns:
        The token string if present, None otherwise
    """
    # Try various attribute names used by different WebSocket libraries
    headers = None

    if hasattr(websocket, "request_headers"):
        headers = websocket.request_headers
    elif hasattr(websocket, "headers"):
        headers = websocket.headers
    elif hasattr(websocket, "request") and hasattr(websocket.request, "headers"):
        headers = websocket.request.headers

    if not headers:
        return None

    return extract_token_from_headers(dict(headers))
