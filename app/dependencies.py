"""
FastAPI Dependency Injection providers.

Uses functools.lru_cache to ensure the OpenStack connection is built once
per process.  Tests can override these dependencies via app.dependency_overrides.
"""
from __future__ import annotations

from functools import lru_cache

import openstack.connection

from app.config import Settings, get_settings
from app.repositories.openstack_client import build_connection
from app.repositories.vm_repository import VMRepository
from app.repositories.volume_repository import VolumeRepository
from app.services.vm_service import VMService
from app.services.volume_service import VolumeService


@lru_cache
def get_openstack_connection() -> openstack.connection.Connection:
    """Singleton OpenStack connection, created on first request."""
    return build_connection(get_settings())


def get_vm_service() -> VMService:
    conn = get_openstack_connection()
    return VMService(VMRepository(conn))


def get_volume_service() -> VolumeService:
    conn = get_openstack_connection()
    return VolumeService(VolumeRepository(conn))
