"""
Unit tests for VMService.

All OpenStack calls are mocked — no network required.
"""
from __future__ import annotations

import pytest

from app.exceptions import NotFoundError
from app.models.vm import (
    VMCreateRequest,
    VMMetadataUpdateRequest,
    VMRebootRequest,
    RebootType,
    NetworkRequest,
    VMStatus,
)
from app.services.vm_service import VMService
from tests.conftest import make_fake_server


class TestListVMs:
    def test_returns_summary_list(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.list_servers.return_value = [
            make_fake_server(id="vm-1", name="web-01", status="ACTIVE"),
            make_fake_server(id="vm-2", name="db-01", status="SHUTOFF"),
        ]
        result = vm_service.list_vms()
        assert len(result) == 2
        assert result[0].id == "vm-1"
        assert result[1].status == VMStatus.SHUTOFF

    def test_passes_status_filter(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.list_servers.return_value = []
        vm_service.list_vms(status_filter="active")
        mock_vm_repo.list_servers.assert_called_once_with(filters={"status": "ACTIVE"})

    def test_empty_list(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.list_servers.return_value = []
        assert vm_service.list_vms() == []


class TestGetVM:
    def test_returns_full_response(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        result = vm_service.get_vm("vm-001")
        assert result.id == "vm-001"
        assert result.status == VMStatus.ACTIVE
        assert "default" in result.addresses

    def test_not_found_propagates(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.side_effect = NotFoundError("Server vm-999 not found")
        with pytest.raises(NotFoundError):
            vm_service.get_vm("vm-999")


class TestCreateVM:
    def test_creates_with_all_fields(self, vm_service: VMService, mock_vm_repo):
        created = make_fake_server(id="new-vm", status="BUILD")
        mock_vm_repo.create_server.return_value = created
        mock_vm_repo.get_server.return_value = created

        request = VMCreateRequest(
            name="my-vm",
            flavor_id="m1.small",
            image_id="img-001",
            networks=[NetworkRequest(network_id="net-001")],
            key_name="my-key",
            security_groups=["default", "web"],
            metadata={"env": "test"},
        )
        result = vm_service.create_vm(request)
        assert result.id == "new-vm"

        call_kwargs = mock_vm_repo.create_server.call_args.kwargs
        assert call_kwargs["name"] == "my-vm"
        assert call_kwargs["networks"] == [{"uuid": "net-001"}]
        assert call_kwargs["metadata"] == {"env": "test"}

    def test_creates_minimal_request(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.create_server.return_value = make_fake_server()
        request = VMCreateRequest(
            name="bare-vm",
            flavor_id="m1.tiny",
            image_id="img-001",
        )
        result = vm_service.create_vm(request)
        assert result.name == "test-vm"
        # no networks key when empty
        call_kwargs = mock_vm_repo.create_server.call_args.kwargs
        assert "networks" not in call_kwargs


class TestDeleteVM:
    def test_delete_calls_repo(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        vm_service.delete_vm("vm-001")
        mock_vm_repo.delete_server.assert_called_once_with("vm-001")

    def test_delete_not_found(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.side_effect = NotFoundError("not found")
        with pytest.raises(NotFoundError):
            vm_service.delete_vm("missing")


class TestPowerOperations:
    def test_start_vm(self, vm_service: VMService, mock_vm_repo):
        server = make_fake_server(status="SHUTOFF")
        mock_vm_repo.get_server.return_value = server
        vm_service.start_vm("vm-001")
        mock_vm_repo.start_server.assert_called_once_with("vm-001")

    def test_stop_vm(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        vm_service.stop_vm("vm-001")
        mock_vm_repo.stop_server.assert_called_once_with("vm-001")

    def test_reboot_soft(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        vm_service.reboot_vm("vm-001", VMRebootRequest(reboot_type=RebootType.SOFT))
        mock_vm_repo.reboot_server.assert_called_once_with("vm-001", "SOFT")

    def test_reboot_hard(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        vm_service.reboot_vm("vm-001", VMRebootRequest(reboot_type=RebootType.HARD))
        mock_vm_repo.reboot_server.assert_called_once_with("vm-001", "HARD")


class TestMetadata:
    def test_update_metadata(self, vm_service: VMService, mock_vm_repo):
        server = make_fake_server()
        mock_vm_repo.get_server.return_value = server
        mock_vm_repo.set_server_metadata.return_value = {"env": "prod"}

        result = vm_service.update_metadata(
            "vm-001", VMMetadataUpdateRequest(metadata={"env": "prod"})
        )
        mock_vm_repo.set_server_metadata.assert_called_once_with("vm-001", {"env": "prod"})

    def test_metadata_not_found(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.side_effect = NotFoundError("not found")
        with pytest.raises(NotFoundError):
            vm_service.update_metadata("bad-id", VMMetadataUpdateRequest(metadata={}))


class TestConsole:
    def test_get_console(self, vm_service: VMService, mock_vm_repo):
        mock_vm_repo.get_server.return_value = make_fake_server()
        mock_vm_repo.get_console_url.return_value = {
            "console_type": "novnc",
            "url": "https://console.example.com/vnc",
        }
        result = vm_service.get_console_url("vm-001")
        assert result.url == "https://console.example.com/vnc"
        assert result.console_type == "novnc"
