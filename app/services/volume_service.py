"""
Volume Service — Cinder volume lifecycle business logic.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.models.volume import (
    AttachmentInfo,
    SnapshotCreateRequest,
    SnapshotResponse,
    SnapshotStatus,
    VolumeAttachRequest,
    VolumeCreateRequest,
    VolumeResponse,
    VolumeStatus,
)
from app.repositories.volume_repository import VolumeRepository

logger = logging.getLogger(__name__)


def _map_vol_status(raw: Optional[str]) -> VolumeStatus:
    try:
        return VolumeStatus(raw or "unknown")
    except ValueError:
        return VolumeStatus.UNKNOWN


def _map_snap_status(raw: Optional[str]) -> SnapshotStatus:
    try:
        return SnapshotStatus(raw or "error")
    except ValueError:
        return SnapshotStatus.ERROR


def _to_volume_response(vol: Any) -> VolumeResponse:
    attachments = [
        AttachmentInfo(
            attachment_id=a.get("attachment_id"),
            server_id=a.get("server_id"),
            device=a.get("device"),
        )
        for a in (vol.attachments or [])
    ]
    return VolumeResponse(
        id=vol.id,
        name=vol.name,
        status=_map_vol_status(vol.status),
        size_gb=vol.size,
        volume_type=vol.volume_type,
        availability_zone=vol.availability_zone,
        description=vol.description,
        metadata=dict(vol.metadata or {}),
        attachments=attachments,
        bootable=str(getattr(vol, "is_bootable", False)).lower() == "true",
        encrypted=getattr(vol, "is_encrypted", False) or False,
        created_at=str(vol.created_at) if vol.created_at else None,
        updated_at=str(vol.updated_at) if vol.updated_at else None,
    )


def _to_snapshot_response(snap: Any) -> SnapshotResponse:
    return SnapshotResponse(
        id=snap.id,
        name=snap.name,
        status=_map_snap_status(snap.status),
        size_gb=snap.size,
        volume_id=snap.volume_id,
        description=snap.description,
        created_at=str(snap.created_at) if snap.created_at else None,
    )


class VolumeService:
    def __init__(self, repo: VolumeRepository) -> None:
        self._repo = repo

    def list_volumes(self) -> List[VolumeResponse]:
        return [_to_volume_response(v) for v in self._repo.list_volumes()]

    def get_volume(self, volume_id: str) -> VolumeResponse:
        return _to_volume_response(self._repo.get_volume(volume_id))

    def create_volume(self, request: VolumeCreateRequest) -> VolumeResponse:
        kwargs: Dict[str, Any] = {
            "name": request.name,
            "size": request.size_gb,
        }
        if request.volume_type:
            kwargs["volume_type"] = request.volume_type
        if request.availability_zone:
            kwargs["availability_zone"] = request.availability_zone
        if request.description:
            kwargs["description"] = request.description
        if request.metadata:
            kwargs["metadata"] = request.metadata
        if request.source_snapshot_id:
            kwargs["snapshot_id"] = request.source_snapshot_id

        vol = self._repo.create_volume(**kwargs)
        return _to_volume_response(vol)

    def delete_volume(self, volume_id: str) -> None:
        self._repo.get_volume(volume_id)
        self._repo.delete_volume(volume_id)

    def attach_volume(self, volume_id: str, request: VolumeAttachRequest) -> VolumeResponse:
        self._repo.get_volume(volume_id)
        self._repo.attach_volume(
            server_id=request.vm_id,
            volume_id=volume_id,
            device=request.mount_point,
        )
        return self.get_volume(volume_id)

    def detach_volume(self, volume_id: str, vm_id: str) -> VolumeResponse:
        self._repo.get_volume(volume_id)
        self._repo.detach_volume(server_id=vm_id, volume_id=volume_id)
        return self.get_volume(volume_id)

    def create_snapshot(self, volume_id: str, request: SnapshotCreateRequest) -> SnapshotResponse:
        self._repo.get_volume(volume_id)
        snap = self._repo.create_snapshot(
            volume_id=volume_id,
            name=request.name,
            description=request.description,
            force=request.force,
        )
        return _to_snapshot_response(snap)

    def list_snapshots(self, volume_id: Optional[str] = None) -> List[SnapshotResponse]:
        return [_to_snapshot_response(s) for s in self._repo.list_snapshots(volume_id)]

    def delete_snapshot(self, snapshot_id: str) -> None:
        self._repo.get_snapshot(snapshot_id)
        self._repo.delete_snapshot(snapshot_id)
