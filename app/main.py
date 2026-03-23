"""
FastAPI application factory.

Wires together routers, exception handlers, middleware, and OpenAPI metadata.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging, request_logging_middleware
from app.routers import health, vms, volumes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle events."""
    settings = get_settings()
    configure_logging(settings.log_level)
    yield
    # Clean shutdown: clear the connection cache
    from app.dependencies import get_openstack_connection
    get_openstack_connection.cache_clear()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for managing OpenStack VM lifecycle operations including "
            "provisioning, power management, metadata, and block storage."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_logging_middleware)

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(vms.router, prefix=api_prefix)
    app.include_router(volumes.router, prefix=api_prefix)

    return app


app = create_app()
