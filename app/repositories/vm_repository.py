"""
VM Repository — thin wrapper around openstacksdk Nova operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import openstack.connection
from openstack.exceptions import SDKException

from app.repositories.openstack_client import map_openstack_error

logger = logging.getLogger(__name__)


class VMRepository:
    """Encapsulates all Nova (compute) operations."""

    def __init__(self, conn: openstack.connection.Connection) -> None:
        self._conn = conn

    def list_servers(self, filters: Optional[Dict] = None) -> List[Any]:
        try:
            return list(self._conn.compute.servers(**(filters or {})))
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def get_server(self, server_id: str) -> Any:
        try:
            server = self._conn.compute.get_server(server_id)
            if server is None:
                from app.exceptions import NotFoundError
                raise NotFoundError(f"Server {server_id} not found")
            return server
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def create_server(self, **kwargs: Any) -> Any:
        try:
            logger.info("Creating server: name=%s", kwargs.get("name"))
            return self._conn.compute.create_server(**kwargs)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def delete_server(self, server_id: str) -> None:
        try:
            logger.info("Deleting server: id=%s", server_id)
            self._conn.compute.delete_server(server_id, ignore_missing=True)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def start_server(self, server_id: str) -> None:
        try:
            self._conn.compute.start_server(server_id)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def stop_server(self, server_id: str) -> None:
        try:
            self._conn.compute.stop_server(server_id)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def reboot_server(self, server_id: str, reboot_type: str = "SOFT") -> None:
        try:
            self._conn.compute.reboot_server(server_id, reboot_type)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def set_server_metadata(self, server_id: str, metadata: Dict[str, str]) -> Dict:
        try:
            return dict(self._conn.compute.set_server_metadata(server_id, **metadata))
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def get_console_url(self, server_id: str, console_type: str = "novnc") -> Dict:
        try:
            result = self._conn.compute.create_console(
                server_id, console_type=console_type
            )
            return {"console_type": console_type, "url": result.get("url", "")}
        except SDKException as exc:
            raise map_openstack_error(exc, "console") from exc

    def wait_for_server(self, server_id: str, status: str = "ACTIVE", timeout: int = 300) -> Any:
        try:
            return self._conn.compute.wait_for_server(
                self._conn.compute.get_server(server_id),
                status=status,
                wait=timeout,
            )
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc
