"""
Request-ID middleware for the FastAPI application.

Injects a unique ``X-Request-ID`` header into every request and response
to support distributed tracing and log correlation.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import REQUEST_ID_HEADER


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to every HTTP request.

    If the client sends an ``X-Request-ID`` header, it is preserved;
    otherwise, a new UUID v4 is generated. The ID is set on both the
    request state and the response headers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Generate or preserve a request ID, then pass it downstream."""
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def configure_request_id(app: FastAPI) -> None:
    """
    Add Request-ID middleware to the application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(RequestIDMiddleware)