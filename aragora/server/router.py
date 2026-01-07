"""
Request router for dispatching HTTP requests to handlers.

Provides a centralized routing mechanism that:
- Registers handlers by path patterns
- Dispatches requests to appropriate handlers
- Handles method routing (GET, POST, PUT, DELETE)
- Supports path parameters (e.g., /api/debates/{id})
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Pattern, TYPE_CHECKING

if TYPE_CHECKING:
    from aragora.server.handlers.base import BaseHandler, HandlerResult

logger = logging.getLogger(__name__)


@dataclass
class Route:
    """A registered route with pattern and handler."""

    pattern: Pattern[str]
    handler: "BaseHandler"
    methods: set[str] = field(default_factory=lambda: {"GET"})
    name: str = ""

    def matches(self, path: str, method: str) -> tuple[bool, dict[str, str]]:
        """Check if route matches path and method.

        Returns:
            Tuple of (matches, path_params)
        """
        if method not in self.methods:
            return False, {}

        match = self.pattern.match(path)
        if match:
            return True, match.groupdict()
        return False, {}


class RequestRouter:
    """Central request dispatcher to modular handlers.

    Routes requests based on URL path patterns to registered handlers.

    Usage:
        router = RequestRouter()

        # Register handlers
        router.register(debates_handler)
        router.register(agents_handler)

        # Dispatch request
        result = router.dispatch("GET", "/api/debates", {}, http_handler)
    """

    def __init__(self):
        """Initialize the router."""
        self._routes: list[Route] = []
        self._handlers: list["BaseHandler"] = []

    def register(self, handler: "BaseHandler") -> None:
        """Register a handler with its routes.

        Args:
            handler: Handler instance with ROUTES class attribute
        """
        self._handlers.append(handler)

        # Check if handler has explicit routes
        routes = getattr(handler, "ROUTES", None)
        if not routes:
            return

        for route_path in routes:
            # Convert path pattern to regex
            # Support {param} syntax for path parameters
            pattern_str = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", route_path)
            pattern = re.compile(f"^{pattern_str}$")

            # Determine methods from handler capabilities
            methods = {"GET"}
            if hasattr(handler, "handle_post"):
                methods.add("POST")
            if hasattr(handler, "handle_put"):
                methods.add("PUT")
            if hasattr(handler, "handle_delete"):
                methods.add("DELETE")

            route = Route(
                pattern=pattern,
                handler=handler,
                methods=methods,
                name=handler.__class__.__name__,
            )
            self._routes.append(route)

    def dispatch(
        self,
        method: str,
        path: str,
        query_params: dict,
        http_handler: Any = None,
    ) -> Optional["HandlerResult"]:
        """Dispatch a request to the appropriate handler.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            query_params: Parsed query parameters
            http_handler: HTTP handler instance for reading body, etc.

        Returns:
            HandlerResult if handled, None otherwise
        """
        # First check explicit routes
        for route in self._routes:
            matches, path_params = route.matches(path, method)
            if matches:
                return self._invoke_handler(
                    route.handler,
                    method,
                    path,
                    query_params,
                    path_params,
                    http_handler,
                )

        # Fall back to can_handle check for handlers without explicit routes
        for handler in self._handlers:
            if hasattr(handler, "can_handle") and handler.can_handle(path):
                return self._invoke_handler(
                    handler,
                    method,
                    path,
                    query_params,
                    {},
                    http_handler,
                )

        return None

    def _invoke_handler(
        self,
        handler: "BaseHandler",
        method: str,
        path: str,
        query_params: dict,
        path_params: dict,
        http_handler: Any,
    ) -> Optional["HandlerResult"]:
        """Invoke the appropriate method on a handler.

        Args:
            handler: Handler instance
            method: HTTP method
            path: Request path
            query_params: Query parameters
            path_params: Path parameters extracted from URL
            http_handler: HTTP handler instance

        Returns:
            HandlerResult if handled, None otherwise
        """
        try:
            if method == "GET" and hasattr(handler, "handle"):
                return handler.handle(path, query_params, http_handler)
            elif method == "POST" and hasattr(handler, "handle_post"):
                return handler.handle_post(path, query_params, http_handler)
            elif method == "PUT" and hasattr(handler, "handle_put"):
                return handler.handle_put(path, query_params, http_handler)
            elif method == "DELETE" and hasattr(handler, "handle_delete"):
                return handler.handle_delete(path, query_params, http_handler)
        except Exception as e:
            logger.error(f"Handler error for {method} {path}: {e}", exc_info=True)
            # Return None to let caller handle the error
            return None

        return None

    def get_all_routes(self) -> list[dict[str, Any]]:
        """Get list of all registered routes for documentation.

        Returns:
            List of route info dicts
        """
        routes_info = []
        for route in self._routes:
            routes_info.append({
                "pattern": route.pattern.pattern,
                "methods": list(route.methods),
                "handler": route.name,
            })
        return routes_info

    def get_handler_for_path(self, path: str, method: str = "GET") -> Optional["BaseHandler"]:
        """Get the handler that would handle a given path.

        Useful for testing and introspection.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Handler instance or None
        """
        for route in self._routes:
            matches, _ = route.matches(path, method)
            if matches:
                return route.handler

        for handler in self._handlers:
            if hasattr(handler, "can_handle") and handler.can_handle(path):
                return handler

        return None
