"""
Pydantic v2 models for Cinder Volume resources.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

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
    volume_type: Optional[str] = Field(None, description="Cinder volume type")
    availability_zone: Optional[str] = None
    description: Optional[str] = Field(None, max_length=255)
    metadata: Dict[str, str] = Field(default_factory=dict)
    source_snapshot_id: Optional[str] = Field(
        None, description="Create volume from this snapshot"
    )


class VolumeAttachRequest(BaseModel):
    vm_id: str = Field(..., description="Nova server UUID to attach to")
    mount_point: Optional[str] = Field(
        None,
        description="Device path e.g. /dev/vdb  (Nova may override this)",
    )


class SnapshotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    force: bool = Field(
        False,
        description="Snapshot even if volume is attached (in-use)",
    )


# ── Response schemas ────────────────────────────────────────────────────────────

class AttachmentInfo(BaseModel):
    attachment_id: Optional[str] = None
    server_id: Optional[str] = None
    device: Optional[str] = None


class VolumeResponse(BaseModel):
    id: str
    name: Optional[str] = None
    status: VolumeStatus
    size_gb: int
    volume_type: Optional[str] = None
    availability_zone: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    attachments: List[AttachmentInfo] = Field(default_factory=list)
    bootable: bool = False
    encrypted: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    id: str
    name: Optional[str] = None
    status: SnapshotStatus
    size_gb: int
    volume_id: str
    description: Optional[str] = None
    created_at: Optional[str] = None
