"""
Structured JSON logging configuration.
Outputs request-scoped fields (method, path, status, duration_ms) so logs
can be ingested by ELK / Loki / CloudWatch without extra parsing.
"""
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":%(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """ASGI middleware that logs every request with timing."""
    logger = logging.getLogger("api.access")
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        '"method":"%s","path":"%s","status":%d,"duration_ms":%s',
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
