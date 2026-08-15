"""
Response timing middleware for the FastAPI application.

Adds ``X-Response-Time`` header to every response, indicating the
wall-clock duration of request processing in milliseconds.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request


async def response_timing_middleware(request: Request, call_next):
    """
    Measure and attach the ``X-Response-Time`` header to every response.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
    return response


def configure_response_timing(app: FastAPI) -> None:
    """
    Add response-timing middleware to the application.

    Args:
        app: The FastAPI application instance.
    """
    app.middleware("http")(response_timing_middleware)