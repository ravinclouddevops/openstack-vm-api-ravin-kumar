"""
Pydantic v2 models for Virtual Machine resources.

Separates *request* schemas (what the client sends) from *response* schemas
(what we return) to keep the API contract explicit and stable.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enumerations ────────────────────────────────────────────────────────────────

class VMStatus(str, Enum):
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    SHUTOFF = "SHUTOFF"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    BUILD = "BUILD"
    REBUILD = "REBUILD"
    MIGRATING = "MIGRATING"
    DELETED = "DELETED"
    UNKNOWN = "UNKNOWN"


class RebootType(str, Enum):
    SOFT = "SOFT"   # graceful OS reboot
    HARD = "HARD"   # power-cycle


# ── Request schemas ─────────────────────────────────────────────────────────────

class NetworkRequest(BaseModel):
    network_id: str = Field(..., description="Neutron network UUID")


class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="VM display name")
    flavor_id: str = Field(..., description="Nova flavor UUID or name")
    image_id: str = Field(..., description="Glance image UUID")
    networks: list[NetworkRequest] = Field(
        default_factory=list,
        description="Networks to attach; empty = Nova picks the default",
    )
    key_name: str | None = Field(None, description="SSH key-pair name")
    security_groups: list[str] = Field(
        default_factory=list,
        description="Security group names or IDs",
    )
    user_data: str | None = Field(
        None,
        description="Base-64 encoded cloud-init script",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary key/value metadata",
    )
    availability_zone: str | None = Field(None, description="Target AZ")


class VMMetadataUpdateRequest(BaseModel):
    metadata: dict[str, str] = Field(..., description="Metadata key/value pairs to set")


class VMRebootRequest(BaseModel):
    reboot_type: RebootType = Field(
        RebootType.SOFT,
        description="SOFT = graceful shutdown, HARD = power-cycle",
    )


# ── Response schemas ────────────────────────────────────────────────────────────

class AddressInfo(BaseModel):
    ip_address: str
    mac_address: str | None = None
    version: int | None = None


class VMResponse(BaseModel):
    id: str
    name: str
    status: VMStatus
    flavor_id: str | None = None
    image_id: str | None = None
    key_name: str | None = None
    addresses: dict[str, list[AddressInfo]] = Field(default_factory=dict)
    security_groups: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    availability_zone: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    host_id: str | None = None

    model_config = {"from_attributes": True}


class ConsoleResponse(BaseModel):
    console_type: str
    url: str


class VMSummary(BaseModel):
    """Lightweight representation used in list responses."""
    id: str
    name: str
    status: VMStatus
    created_at: str | None = None
