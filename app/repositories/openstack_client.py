"""
OpenStack connection factory.

Builds an openstack.connection.Connection from environment variables or a
named cloud in clouds.yaml.  The connection object is thread-safe and is
intended to be used as a long-lived singleton (via FastAPI dependency injection).
"""
from __future__ import annotations

import logging

import openstack
import openstack.connection
from openstack.exceptions import (
    HttpException,
    NotFoundException,
    ConflictException,
    SDKException,
)

from app.config import Settings
from app.exceptions import (
    NotFoundError,
    ConflictError,
    OpenStackError,
    QuotaExceededError,
)

logger = logging.getLogger(__name__)


def build_connection(settings: Settings) -> openstack.connection.Connection:
    """
    Create and return an authenticated OpenStack connection.

    Priority order:
    1. Named cloud in clouds.yaml (OS_CLOUD / os_cloud setting)
    2. Explicit credential env-vars (OS_AUTH_URL, OS_USERNAME, …)
    """
    if settings.os_cloud:
        logger.info("Connecting to OpenStack cloud: %s", settings.os_cloud)
        return openstack.connect(cloud=settings.os_cloud)

    logger.info("Connecting to OpenStack via explicit credentials, auth_url=%s", settings.os_auth_url)
    return openstack.connect(
        auth_url=settings.os_auth_url,
        username=settings.os_username,
        password=settings.os_password,
        project_name=settings.os_project_name,
        user_domain_name=settings.os_user_domain_name,
        project_domain_name=settings.os_project_domain_name,
        region_name=settings.os_region_name,
    )


def map_openstack_error(exc: Exception, resource_type: str = "resource") -> Exception:
    """
    Translate openstacksdk HTTP exceptions into domain exceptions so the
    service layer stays SDK-agnostic.
    """
    if isinstance(exc, NotFoundException):
        return NotFoundError(f"{resource_type} not found", detail=str(exc))
    if isinstance(exc, ConflictException):
        return ConflictError(f"{resource_type} conflict", detail=str(exc))
    if isinstance(exc, HttpException):
        status = getattr(exc, "status_code", 0)
        if status == 403:
            return QuotaExceededError("Quota exceeded or insufficient privileges", detail=str(exc))
        return OpenStackError(f"OpenStack returned HTTP {status}", detail=str(exc))
    if isinstance(exc, SDKException):
        return OpenStackError("OpenStack SDK error", detail=str(exc))
    return exc
