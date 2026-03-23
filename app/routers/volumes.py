"""
Volume management REST endpoints — /api/v1/volumes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_volume_service
from app.models.common import MessageResponse
from app.models.volume import (
    SnapshotCreateRequest,
    SnapshotResponse,
    VolumeAttachRequest,
    VolumeCreateRequest,
    VolumeResponse,
)
from app.services.volume_service import VolumeService

router = APIRouter(prefix="/volumes", tags=["Volumes"])


@router.get(
    "",
    response_model=list[VolumeResponse],
    summary="List all volumes",
)
async def list_volumes(
    service: VolumeService = Depends(get_volume_service),
) -> list[VolumeResponse]:
    return service.list_volumes()


@router.post(
    "",
    response_model=VolumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new volume",
    description="Creates a Cinder block storage volume. Optionally bootstrap from a snapshot.",
)
async def create_volume(
    request: VolumeCreateRequest,
    service: VolumeService = Depends(get_volume_service),
) -> VolumeResponse:
    return service.create_volume(request)


@router.get(
    "/{volume_id}",
    response_model=VolumeResponse,
    summary="Get volume details",
)
async def get_volume(
    volume_id: str,
    service: VolumeService = Depends(get_volume_service),
) -> VolumeResponse:
    return service.get_volume(volume_id)


@router.delete(
    "/{volume_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete a volume",
)
async def delete_volume(
    volume_id: str,
    service: VolumeService = Depends(get_volume_service),
) -> MessageResponse:
    service.delete_volume(volume_id)
    return MessageResponse(message=f"Volume {volume_id} deletion initiated")


@router.post(
    "/{volume_id}/attach",
    response_model=VolumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Attach a volume to a VM",
)
async def attach_volume(
    volume_id: str,
    request: VolumeAttachRequest,
    service: VolumeService = Depends(get_volume_service),
) -> VolumeResponse:
    return service.attach_volume(volume_id, request)


@router.post(
    "/{volume_id}/detach",
    response_model=VolumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Detach a volume from a VM",
)
async def detach_volume(
    volume_id: str,
    vm_id: str = Query(..., description="VM UUID to detach from"),
    service: VolumeService = Depends(get_volume_service),
) -> VolumeResponse:
    return service.detach_volume(volume_id, vm_id)


@router.post(
    "/{volume_id}/snapshots",
    response_model=SnapshotResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a snapshot of a volume",
)
async def create_snapshot(
    volume_id: str,
    request: SnapshotCreateRequest,
    service: VolumeService = Depends(get_volume_service),
) -> SnapshotResponse:
    return service.create_snapshot(volume_id, request)


@router.get(
    "/{volume_id}/snapshots",
    response_model=list[SnapshotResponse],
    summary="List snapshots for a volume",
)
async def list_snapshots(
    volume_id: str,
    service: VolumeService = Depends(get_volume_service),
) -> list[SnapshotResponse]:
    return service.list_snapshots(volume_id)
