"""
Shared pytest fixtures used across unit and integration test suites.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_vm_service, get_volume_service
from app.main import create_app
from app.repositories.vm_repository import VMRepository
from app.repositories.volume_repository import VolumeRepository
from app.services.vm_service import VMService
from app.services.volume_service import VolumeService


# ── Fake OpenStack objects ─────────────────────────────────────────────────────

def make_fake_server(
    id: str = "vm-001",
    name: str = "test-vm",
    status: str = "ACTIVE",
    **kwargs: Any,
) -> MagicMock:
    server = MagicMock()
    server.id = id
    server.name = name
    server.status = status
    server.flavor = {"id": "m1.small"}
    server.image = {"id": "img-001"}
    server.key_name = "my-key"
    server.addresses = {"default": [{"addr": "10.0.0.1", "version": 4}]}
    server.security_groups = [{"name": "default"}]
    server.metadata = {}
    server.availability_zone = "nova"
    server.created_at = "2024-01-01T00:00:00Z"
    server.updated_at = "2024-01-01T00:01:00Z"
    server.host_id = "host-abc"
    for k, v in kwargs.items():
        setattr(server, k, v)
    return server


def make_fake_volume(
    id: str = "vol-001",
    name: str = "test-vol",
    status: str = "available",
    size: int = 20,
    **kwargs: Any,
) -> MagicMock:
    vol = MagicMock()
    vol.id = id
    vol.name = name
    vol.status = status
    vol.size = size
    vol.volume_type = "standard"
    vol.availability_zone = "nova"
    vol.description = "Test volume"
    vol.metadata = {}
    vol.attachments = []
    vol.is_bootable = False
    vol.is_encrypted = False
    vol.created_at = "2024-01-01T00:00:00Z"
    vol.updated_at = "2024-01-01T00:01:00Z"
    for k, v in kwargs.items():
        setattr(vol, k, v)
    return vol


def make_fake_snapshot(
    id: str = "snap-001",
    name: str = "test-snap",
    status: str = "available",
    volume_id: str = "vol-001",
    size: int = 20,
) -> MagicMock:
    snap = MagicMock()
    snap.id = id
    snap.name = name
    snap.status = status
    snap.volume_id = volume_id
    snap.size = size
    snap.description = "Test snapshot"
    snap.created_at = "2024-01-01T00:00:00Z"
    return snap


# ── Repository mocks ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_vm_repo() -> MagicMock:
    return MagicMock(spec=VMRepository)


@pytest.fixture
def mock_volume_repo() -> MagicMock:
    return MagicMock(spec=VolumeRepository)


# ── Service fixtures ──────────────────────────────────────────────────────────
# Unit tests get a real VMService/VolumeService backed by a mock repository.
# Integration (endpoint) tests get a MagicMock service so return_value can be
# set directly on service methods.

@pytest.fixture
def vm_service(mock_vm_repo: MagicMock) -> VMService:
    """Real VMService with a mocked repository — used in unit tests."""
    return VMService(mock_vm_repo)


@pytest.fixture
def volume_service(mock_volume_repo: MagicMock) -> VolumeService:
    """Real VolumeService with a mocked repository — used in unit tests."""
    return VolumeService(mock_volume_repo)


# ── HTTP test client ──────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    """
    TestClient with dependency overrides.
    Services are injected as MagicMocks so integration tests control
    return values without touching OpenStack.
    """
    app = create_app()
    _vm_svc = MagicMock(spec=VMService)
    _vol_svc = MagicMock(spec=VolumeService)
    app.dependency_overrides[get_vm_service] = lambda: _vm_svc
    app.dependency_overrides[get_volume_service] = lambda: _vol_svc
    client = TestClient(app)
    # Attach service mocks as attributes so tests can configure them
    client.vm_service = _vm_svc  # type: ignore[attr-defined]
    client.volume_service = _vol_svc  # type: ignore[attr-defined]
    return client
