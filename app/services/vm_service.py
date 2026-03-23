"""
VM Service — orchestrates VM lifecycle business logic.

Converts raw OpenStack objects to typed Pydantic response models.
This is the layer unit tests mock; integration tests use the real repository.
"""
from __future__ import annotations

import logging
from typing import Any

from app.models.vm import (
    AddressInfo,
    ConsoleResponse,
    VMCreateRequest,
    VMMetadataUpdateRequest,
    VMRebootRequest,
    VMResponse,
    VMStatus,
    VMSummary,
)
from app.repositories.vm_repository import VMRepository

logger = logging.getLogger(__name__)


def _map_status(raw: str | None) -> VMStatus:
    try:
        return VMStatus(raw or "UNKNOWN")
    except ValueError:
        return VMStatus.UNKNOWN


def _map_addresses(raw: dict) -> dict[str, list[AddressInfo]]:
    result: dict[str, list[AddressInfo]] = {}
    for net, addrs in (raw or {}).items():
        result[net] = [
            AddressInfo(
                ip_address=a.get("addr", ""),
                mac_address=a.get("OS-EXT-IPS-MAC:mac_addr"),
                version=a.get("version"),
            )
            for a in addrs
        ]
    return result


def _to_vm_response(server: Any) -> VMResponse:
    sg_names = [sg.get("name", "") for sg in (server.get("security_groups") or [])]
    return VMResponse(
        id=server.id,
        name=server.name,
        status=_map_status(server.status),
        flavor_id=server.flavor.get("id") if server.flavor else None,
        image_id=server.image.get("id") if server.image else None,
        key_name=server.key_name,
        addresses=_map_addresses(server.addresses or {}),
        security_groups=sg_names,
        metadata=dict(server.metadata or {}),
        availability_zone=getattr(server, "availability_zone", None),
        created_at=str(server.created_at) if server.created_at else None,
        updated_at=str(server.updated_at) if server.updated_at else None,
        host_id=server.host_id,
    )


class VMService:
    def __init__(self, repo: VMRepository) -> None:
        self._repo = repo

    def list_vms(self, status_filter: str | None = None) -> list[VMSummary]:
        filters: dict[str, Any] = {}
        if status_filter:
            filters["status"] = status_filter.upper()
        servers = self._repo.list_servers(filters=filters)
        return [
            VMSummary(
                id=s.id,
                name=s.name,
                status=_map_status(s.status),
                created_at=str(s.created_at) if s.created_at else None,
            )
            for s in servers
        ]

    def get_vm(self, vm_id: str) -> VMResponse:
        server = self._repo.get_server(vm_id)
        return _to_vm_response(server)

    def create_vm(self, request: VMCreateRequest) -> VMResponse:
        networks = [{"uuid": n.network_id} for n in request.networks]
        security_groups = [{"name": sg} for sg in request.security_groups]

        kwargs: dict[str, Any] = {
            "name": request.name,
            "flavorRef": request.flavor_id,
            "imageRef": request.image_id,
        }
        if networks:
            kwargs["networks"] = networks
        if security_groups:
            kwargs["security_groups"] = security_groups
        if request.key_name:
            kwargs["key_name"] = request.key_name
        if request.user_data:
            kwargs["user_data"] = request.user_data
        if request.metadata:
            kwargs["metadata"] = request.metadata
        if request.availability_zone:
            kwargs["availability_zone"] = request.availability_zone

        server = self._repo.create_server(**kwargs)
        return _to_vm_response(server)

    def delete_vm(self, vm_id: str) -> None:
        # Verify exists before deleting (raises NotFoundError if not)
        self._repo.get_server(vm_id)
        self._repo.delete_server(vm_id)

    def start_vm(self, vm_id: str) -> VMResponse:
        self._repo.get_server(vm_id)  # validate existence
        self._repo.start_server(vm_id)
        return self.get_vm(vm_id)

    def stop_vm(self, vm_id: str) -> VMResponse:
        self._repo.get_server(vm_id)
        self._repo.stop_server(vm_id)
        return self.get_vm(vm_id)

    def reboot_vm(self, vm_id: str, request: VMRebootRequest) -> VMResponse:
        self._repo.get_server(vm_id)
        self._repo.reboot_server(vm_id, request.reboot_type.value)
        return self.get_vm(vm_id)

    def update_metadata(self, vm_id: str, request: VMMetadataUpdateRequest) -> VMResponse:
        self._repo.get_server(vm_id)
        self._repo.set_server_metadata(vm_id, request.metadata)
        return self.get_vm(vm_id)

    def get_console_url(self, vm_id: str, console_type: str = "novnc") -> ConsoleResponse:
        self._repo.get_server(vm_id)
        result = self._repo.get_console_url(vm_id, console_type)
        return ConsoleResponse(console_type=result["console_type"], url=result["url"])
