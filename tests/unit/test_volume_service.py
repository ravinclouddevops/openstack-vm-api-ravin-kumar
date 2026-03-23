"""
Unit tests for VolumeService.
"""
from __future__ import annotations

import pytest

from app.exceptions import NotFoundError
from app.models.volume import (
    SnapshotCreateRequest,
    VolumeAttachRequest,
    VolumeCreateRequest,
    VolumeStatus,
)
from app.services.volume_service import VolumeService
from tests.conftest import make_fake_snapshot, make_fake_volume


class TestListVolumes:
    def test_returns_list(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.list_volumes.return_value = [
            make_fake_volume(id="v1", name="data"),
            make_fake_volume(id="v2", name="backup"),
        ]
        result = volume_service.list_volumes()
        assert len(result) == 2
        assert result[0].id == "v1"

    def test_empty_list(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.list_volumes.return_value = []
        assert volume_service.list_volumes() == []


class TestGetVolume:
    def test_returns_volume(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        result = volume_service.get_volume("vol-001")
        assert result.id == "vol-001"
        assert result.status == VolumeStatus.AVAILABLE

    def test_not_found(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.side_effect = NotFoundError("not found")
        with pytest.raises(NotFoundError):
            volume_service.get_volume("missing")


class TestCreateVolume:
    def test_creates_volume(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.create_volume.return_value = make_fake_volume(
            name="new-vol", size=50
        )
        request = VolumeCreateRequest(name="new-vol", size_gb=50)
        result = volume_service.create_volume(request)
        assert result.size_gb == 50
        call_kwargs = mock_volume_repo.create_volume.call_args.kwargs
        assert call_kwargs["name"] == "new-vol"
        assert call_kwargs["size"] == 50

    def test_creates_from_snapshot(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.create_volume.return_value = make_fake_volume()
        request = VolumeCreateRequest(
            name="from-snap", size_gb=20, source_snapshot_id="snap-001"
        )
        volume_service.create_volume(request)
        call_kwargs = mock_volume_repo.create_volume.call_args.kwargs
        assert call_kwargs["snapshot_id"] == "snap-001"


class TestDeleteVolume:
    def test_deletes_volume(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        volume_service.delete_volume("vol-001")
        mock_volume_repo.delete_volume.assert_called_once_with("vol-001")

    def test_not_found(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.side_effect = NotFoundError("not found")
        with pytest.raises(NotFoundError):
            volume_service.delete_volume("missing")


class TestAttachDetach:
    def test_attach_volume(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        request = VolumeAttachRequest(vm_id="vm-001", mount_point="/dev/vdb")
        volume_service.attach_volume("vol-001", request)
        mock_volume_repo.attach_volume.assert_called_once_with(
            server_id="vm-001", volume_id="vol-001", device="/dev/vdb"
        )

    def test_detach_volume(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        volume_service.detach_volume("vol-001", "vm-001")
        mock_volume_repo.detach_volume.assert_called_once_with(
            server_id="vm-001", volume_id="vol-001"
        )


class TestSnapshots:
    def test_create_snapshot(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        mock_volume_repo.create_snapshot.return_value = make_fake_snapshot()
        request = SnapshotCreateRequest(name="my-snap", description="backup", force=False)
        result = volume_service.create_snapshot("vol-001", request)
        assert result.id == "snap-001"
        mock_volume_repo.create_snapshot.assert_called_once_with(
            volume_id="vol-001",
            name="my-snap",
            description="backup",
            force=False,
        )

    def test_list_snapshots(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.list_snapshots.return_value = [
            make_fake_snapshot(id="s1"),
            make_fake_snapshot(id="s2"),
        ]
        result = volume_service.list_snapshots("vol-001")
        assert len(result) == 2

    def test_delete_snapshot(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_snapshot.return_value = make_fake_snapshot()
        volume_service.delete_snapshot("snap-001")
        mock_volume_repo.delete_snapshot.assert_called_once_with("snap-001")


class TestVolumeStatusMapping:
    def test_unknown_status_falls_back(self, volume_service: VolumeService, mock_volume_repo):
        vol = make_fake_volume(status="some_unknown_status")
        mock_volume_repo.get_volume.return_value = vol
        result = volume_service.get_volume("vol-001")
        assert result.status.value == "unknown"

    def test_none_status_falls_back(self, volume_service: VolumeService, mock_volume_repo):
        vol = make_fake_volume(status=None)
        mock_volume_repo.get_volume.return_value = vol
        result = volume_service.get_volume("vol-001")
        assert result.status.value == "unknown"


class TestSnapshotStatusMapping:
    def test_unknown_snap_status(self, volume_service: VolumeService, mock_volume_repo):
        from tests.conftest import make_fake_snapshot
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        snap = make_fake_snapshot(status="weird_status")
        mock_volume_repo.create_snapshot.return_value = snap
        result = volume_service.create_snapshot(
            "vol-001", SnapshotCreateRequest(name="s")
        )
        assert result.status.value == "error"


class TestVolumeResponseMapping:
    def test_maps_attachments(self, volume_service: VolumeService, mock_volume_repo):
        vol = make_fake_volume()
        vol.attachments = [
            {"attachment_id": "att-1", "server_id": "vm-1", "device": "/dev/vdb"}
        ]
        mock_volume_repo.get_volume.return_value = vol
        result = volume_service.get_volume("vol-001")
        assert len(result.attachments) == 1
        assert result.attachments[0].device == "/dev/vdb"

    def test_create_volume_with_all_optional_fields(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.create_volume.return_value = make_fake_volume()
        request = VolumeCreateRequest(
            name="full-vol",
            size_gb=100,
            volume_type="ssd",
            availability_zone="nova",
            description="test desc",
            metadata={"key": "val"},
        )
        volume_service.create_volume(request)
        call_kwargs = mock_volume_repo.create_volume.call_args.kwargs
        assert call_kwargs["volume_type"] == "ssd"
        assert call_kwargs["availability_zone"] == "nova"
        assert call_kwargs["description"] == "test desc"
        assert call_kwargs["metadata"] == {"key": "val"}

    def test_list_snapshots_no_filter(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.list_snapshots.return_value = []
        volume_service.list_snapshots(volume_id=None)
        mock_volume_repo.list_snapshots.assert_called_once_with(None)


class TestVolumeEdgeCases:
    def test_volume_bootable_true_string(self, volume_service: VolumeService, mock_volume_repo):
        vol = make_fake_volume()
        vol.is_bootable = "true"
        mock_volume_repo.get_volume.return_value = vol
        result = volume_service.get_volume("vol-001")
        assert result.bootable is True

    def test_volume_bootable_false(self, volume_service: VolumeService, mock_volume_repo):
        vol = make_fake_volume()
        vol.is_bootable = False
        mock_volume_repo.get_volume.return_value = vol
        result = volume_service.get_volume("vol-001")
        assert result.bootable is False

    def test_snapshot_with_none_created_at(self, volume_service: VolumeService, mock_volume_repo):
        from tests.conftest import make_fake_snapshot
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        snap = make_fake_snapshot()
        snap.created_at = None
        mock_volume_repo.create_snapshot.return_value = snap
        result = volume_service.create_snapshot(
            "vol-001", SnapshotCreateRequest(name="s")
        )
        assert result.created_at is None

    def test_attach_volume_no_mount_point(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.get_volume.return_value = make_fake_volume()
        from app.models.volume import VolumeAttachRequest
        request = VolumeAttachRequest(vm_id="vm-001")  # no mount_point
        volume_service.attach_volume("vol-001", request)
        mock_volume_repo.attach_volume.assert_called_once_with(
            server_id="vm-001", volume_id="vol-001", device=None
        )

    def test_list_volumes_empty(self, volume_service: VolumeService, mock_volume_repo):
        mock_volume_repo.list_volumes.return_value = []
        assert volume_service.list_volumes() == []
