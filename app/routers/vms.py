"""
VM lifecycle REST endpoints — /api/v1/vms
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_vm_service
from app.models.common import MessageResponse
from app.models.vm import (
    ConsoleResponse,
    VMCreateRequest,
    VMMetadataUpdateRequest,
    VMRebootRequest,
    VMResponse,
    VMSummary,
)
from app.services.vm_service import VMService

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])


@router.get(
    "",
    response_model=List[VMSummary],
    summary="List virtual machines",
)
async def list_vms(
    status: Optional[str] = Query(None, description="Filter by status e.g. ACTIVE, SHUTOFF"),
    service: VMService = Depends(get_vm_service),
) -> List[VMSummary]:
    return service.list_vms(status_filter=status)


@router.post(
    "",
    response_model=VMResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create (boot) a virtual machine",
)
async def create_vm(
    request: VMCreateRequest,
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.create_vm(request)


@router.get(
    "/{vm_id}",
    response_model=VMResponse,
    summary="Get virtual machine details",
)
async def get_vm(
    vm_id: str,
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.get_vm(vm_id)


@router.delete(
    "/{vm_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete (terminate) a virtual machine",
)
async def delete_vm(
    vm_id: str,
    service: VMService = Depends(get_vm_service),
) -> MessageResponse:
    service.delete_vm(vm_id)
    return MessageResponse(message=f"VM {vm_id} deletion initiated")


@router.post(
    "/{vm_id}/start",
    response_model=VMResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start (power on) a virtual machine",
)
async def start_vm(
    vm_id: str,
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.start_vm(vm_id)


@router.post(
    "/{vm_id}/stop",
    response_model=VMResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Stop (power off) a virtual machine",
)
async def stop_vm(
    vm_id: str,
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.stop_vm(vm_id)


@router.post(
    "/{vm_id}/reboot",
    response_model=VMResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Reboot a virtual machine",
)
async def reboot_vm(
    vm_id: str,
    request: VMRebootRequest = VMRebootRequest(),
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.reboot_vm(vm_id, request)


@router.patch(
    "/{vm_id}/metadata",
    response_model=VMResponse,
    summary="Update VM metadata key/value pairs",
)
async def update_metadata(
    vm_id: str,
    request: VMMetadataUpdateRequest,
    service: VMService = Depends(get_vm_service),
) -> VMResponse:
    return service.update_metadata(vm_id, request)


@router.get(
    "/{vm_id}/console",
    response_model=ConsoleResponse,
    summary="Get VNC console URL for a virtual machine",
)
async def get_console(
    vm_id: str,
    console_type: str = Query("novnc", description="Console type: novnc, xvpvnc, spice-html5"),
    service: VMService = Depends(get_vm_service),
) -> ConsoleResponse:
    return service.get_console_url(vm_id, console_type)
