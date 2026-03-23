"""
Pydantic v2 models for Cinder Volume resources.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class VolumeStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in-use"
    CREATING = "creating"
    DELETING = "deleting"
    ERROR = "error"
    ERROR_DELETING = "error_deleting"
    BACKING_UP = "backing-up"
    RESTORING_BACKUP = "restoring-backup"
    SNAPSHOTTING = "snapshotting"
    UNKNOWN = "unknown"


class SnapshotStatus(str, Enum):
    AVAILABLE = "available"
    CREATING = "creating"
    DELETING = "deleting"
    ERROR = "error"


# ── Request schemas ─────────────────────────────────────────────────────────────

class VolumeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    size_gb: int = Field(..., ge=1, le=65536, description="Volume size in GiB")
    volume_type: str | None = Field(None, description="Cinder volume type")
    availability_zone: str | None = None
    description: str | None = Field(None, max_length=255)
    metadata: dict[str, str] = Field(default_factory=dict)
    source_snapshot_id: str | None = Field(
        None, description="Create volume from this snapshot"
    )


class VolumeAttachRequest(BaseModel):
    vm_id: str = Field(..., description="Nova server UUID to attach to")
    mount_point: str | None = Field(
        None,
        description="Device path e.g. /dev/vdb  (Nova may override this)",
    )


class SnapshotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=255)
    force: bool = Field(
        False,
        description="Snapshot even if volume is attached (in-use)",
    )


# ── Response schemas ────────────────────────────────────────────────────────────

class AttachmentInfo(BaseModel):
    attachment_id: str | None = None
    server_id: str | None = None
    device: str | None = None


class VolumeResponse(BaseModel):
    id: str
    name: str | None = None
    status: VolumeStatus
    size_gb: int
    volume_type: str | None = None
    availability_zone: str | None = None
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    attachments: list[AttachmentInfo] = Field(default_factory=list)
    bootable: bool = False
    encrypted: bool = False
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    id: str
    name: str | None = None
    status: SnapshotStatus
    size_gb: int
    volume_id: str
    description: str | None = None
    created_at: str | None = None
