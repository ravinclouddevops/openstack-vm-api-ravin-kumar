"""
Integration tests for Volume API endpoints.
Uses `client.volume_service` MagicMock to control service responses.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.exceptions import NotFoundError
from app.models.volume import (
    SnapshotResponse,
    SnapshotStatus,
    VolumeResponse,
    VolumeStatus,
)


def _vol(id: str = "vol-001", status: str = "available", size: int = 20) -> VolumeResponse:
    return VolumeResponse(id=id, name="test-vol", status=VolumeStatus(status), size_gb=size)


def _snap(id: str = "snap-001") -> SnapshotResponse:
    return SnapshotResponse(
        id=id, name="snap", status=SnapshotStatus.AVAILABLE, size_gb=20, volume_id="vol-001"
    )


class TestListVolumesEndpoint:
    def test_200_list(self, client: TestClient):
        client.volume_service.list_volumes.return_value = [_vol(), _vol(id="vol-002")]
        resp = client.get("/api/v1/volumes")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_empty_list(self, client: TestClient):
        client.volume_service.list_volumes.return_value = []
        resp = client.get("/api/v1/volumes")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetVolumeEndpoint:
    def test_200_get(self, client: TestClient):
        client.volume_service.get_volume.return_value = _vol()
        resp = client.get("/api/v1/volumes/vol-001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "vol-001"

    def test_404_not_found(self, client: TestClient):
        client.volume_service.get_volume.side_effect = NotFoundError("not found")
        resp = client.get("/api/v1/volumes/missing")
        assert resp.status_code == 404


class TestCreateVolumeEndpoint:
    def test_202_created(self, client: TestClient):
        client.volume_service.create_volume.return_value = _vol(size=50)
        resp = client.post("/api/v1/volumes", json={"name": "data", "size_gb": 50})
        assert resp.status_code == 202
        assert resp.json()["size_gb"] == 50

    def test_422_missing_name(self, client: TestClient):
        resp = client.post("/api/v1/volumes", json={"size_gb": 10})
        assert resp.status_code == 422

    def test_422_size_too_small(self, client: TestClient):
        resp = client.post("/api/v1/volumes", json={"name": "v", "size_gb": 0})
        assert resp.status_code == 422


class TestDeleteVolumeEndpoint:
    def test_202_deleted(self, client: TestClient):
        client.volume_service.delete_volume.return_value = None
        resp = client.delete("/api/v1/volumes/vol-001")
        assert resp.status_code == 202

    def test_404_not_found(self, client: TestClient):
        client.volume_service.delete_volume.side_effect = NotFoundError("not found")
        resp = client.delete("/api/v1/volumes/missing")
        assert resp.status_code == 404


class TestAttachDetachEndpoints:
    def test_attach_202(self, client: TestClient):
        client.volume_service.attach_volume.return_value = _vol(status="in-use")
        resp = client.post(
            "/api/v1/volumes/vol-001/attach",
            json={"vm_id": "vm-001", "mount_point": "/dev/vdb"},
        )
        assert resp.status_code == 202
        assert resp.json()["status"] == "in-use"

    def test_detach_202(self, client: TestClient):
        client.volume_service.detach_volume.return_value = _vol()
        resp = client.post("/api/v1/volumes/vol-001/detach?vm_id=vm-001")
        assert resp.status_code == 202

    def test_attach_missing_vm_id(self, client: TestClient):
        resp = client.post("/api/v1/volumes/vol-001/attach", json={})
        assert resp.status_code == 422


class TestSnapshotEndpoints:
    def test_create_snapshot_202(self, client: TestClient):
        client.volume_service.create_snapshot.return_value = _snap()
        resp = client.post(
            "/api/v1/volumes/vol-001/snapshots",
            json={"name": "my-snap"},
        )
        assert resp.status_code == 202
        assert resp.json()["id"] == "snap-001"

    def test_list_snapshots(self, client: TestClient):
        client.volume_service.list_snapshots.return_value = [_snap(), _snap(id="snap-002")]
        resp = client.get("/api/v1/volumes/vol-001/snapshots")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_create_snapshot_422_missing_name(self, client: TestClient):
        resp = client.post("/api/v1/volumes/vol-001/snapshots", json={})
        assert resp.status_code == 422


class TestHealthEndpoints:
    def test_health(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready(self, client: TestClient):
        resp = client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
