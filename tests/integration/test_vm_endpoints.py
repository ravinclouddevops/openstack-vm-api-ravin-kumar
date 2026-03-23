"""
Integration tests for VM API endpoints.

Uses FastAPI TestClient with mocked services — tests the full HTTP layer
including routing, validation, error mapping, and response serialisation.

The `client` fixture (from conftest) exposes `client.vm_service` as a
MagicMock so each test can set return_value / side_effect without
touching real OpenStack.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.exceptions import NotFoundError
from app.models.vm import ConsoleResponse, VMResponse, VMStatus, VMSummary


class TestListVMsEndpoint:
    def test_200_returns_list(self, client: TestClient):
        client.vm_service.list_vms.return_value = [
            VMSummary(id="vm-1", name="web", status=VMStatus.ACTIVE, created_at=None),
        ]
        resp = client.get("/api/v1/vms")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "vm-1"

    def test_passes_status_query_param(self, client: TestClient):
        client.vm_service.list_vms.return_value = []
        resp = client.get("/api/v1/vms?status=SHUTOFF")
        assert resp.status_code == 200
        client.vm_service.list_vms.assert_called_once_with(status_filter="SHUTOFF")

    def test_empty_returns_200(self, client: TestClient):
        client.vm_service.list_vms.return_value = []
        resp = client.get("/api/v1/vms")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetVMEndpoint:
    def test_200_returns_vm(self, client: TestClient):
        client.vm_service.get_vm.return_value = VMResponse(
            id="vm-001", name="my-vm", status=VMStatus.ACTIVE
        )
        resp = client.get("/api/v1/vms/vm-001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "vm-001"

    def test_404_when_not_found(self, client: TestClient):
        client.vm_service.get_vm.side_effect = NotFoundError("Server vm-999 not found")
        resp = client.get("/api/v1/vms/vm-999")
        assert resp.status_code == 404
        assert resp.json()["error"] == "NOT_FOUND"


class TestCreateVMEndpoint:
    VALID_PAYLOAD = {
        "name": "my-vm",
        "flavor_id": "m1.small",
        "image_id": "img-001",
        "networks": [{"network_id": "net-abc"}],
    }

    def test_202_accepted(self, client: TestClient):
        client.vm_service.create_vm.return_value = VMResponse(
            id="new-vm", name="my-vm", status=VMStatus.BUILD
        )
        resp = client.post("/api/v1/vms", json=self.VALID_PAYLOAD)
        assert resp.status_code == 202
        assert resp.json()["status"] == "BUILD"

    def test_422_missing_required_fields(self, client: TestClient):
        resp = client.post("/api/v1/vms", json={"name": "incomplete"})
        assert resp.status_code == 422

    def test_422_empty_name(self, client: TestClient):
        payload = {**self.VALID_PAYLOAD, "name": ""}
        resp = client.post("/api/v1/vms", json=payload)
        assert resp.status_code == 422


class TestDeleteVMEndpoint:
    def test_202_deleted(self, client: TestClient):
        client.vm_service.delete_vm.return_value = None
        resp = client.delete("/api/v1/vms/vm-001")
        assert resp.status_code == 202
        assert "vm-001" in resp.json()["message"]

    def test_404_not_found(self, client: TestClient):
        client.vm_service.delete_vm.side_effect = NotFoundError("not found")
        resp = client.delete("/api/v1/vms/missing")
        assert resp.status_code == 404


class TestPowerEndpoints:
    def test_start_202(self, client: TestClient):
        client.vm_service.start_vm.return_value = VMResponse(
            id="vm-001", name="x", status=VMStatus.ACTIVE
        )
        resp = client.post("/api/v1/vms/vm-001/start")
        assert resp.status_code == 202

    def test_stop_202(self, client: TestClient):
        client.vm_service.stop_vm.return_value = VMResponse(
            id="vm-001", name="x", status=VMStatus.SHUTOFF
        )
        resp = client.post("/api/v1/vms/vm-001/stop")
        assert resp.status_code == 202

    def test_reboot_default_soft(self, client: TestClient):
        client.vm_service.reboot_vm.return_value = VMResponse(
            id="vm-001", name="x", status=VMStatus.ACTIVE
        )
        resp = client.post("/api/v1/vms/vm-001/reboot", json={})
        assert resp.status_code == 202

    def test_start_404(self, client: TestClient):
        client.vm_service.start_vm.side_effect = NotFoundError("not found")
        resp = client.post("/api/v1/vms/bad/start")
        assert resp.status_code == 404


class TestMetadataEndpoint:
    def test_patch_metadata(self, client: TestClient):
        client.vm_service.update_metadata.return_value = VMResponse(
            id="vm-001", name="x", status=VMStatus.ACTIVE, metadata={"env": "prod"}
        )
        resp = client.patch(
            "/api/v1/vms/vm-001/metadata",
            json={"metadata": {"env": "prod"}},
        )
        assert resp.status_code == 200
        assert resp.json()["metadata"]["env"] == "prod"


class TestConsoleEndpoint:
    def test_get_console(self, client: TestClient):
        client.vm_service.get_console_url.return_value = ConsoleResponse(
            console_type="novnc", url="https://console.example.com"
        )
        resp = client.get("/api/v1/vms/vm-001/console")
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://console.example.com"
