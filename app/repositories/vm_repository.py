"""
VM Repository — thin wrapper around openstacksdk Nova operations.

All OpenStack SDK calls live here; nothing above this layer imports openstack.
Errors are mapped to domain exceptions before bubbling up.
"""
from __future__ import annotations

import logging
from typing import Any

import openstack.connection
from openstack.exceptions import SDKException

from app.repositories.openstack_client import map_openstack_error

logger = logging.getLogger(__name__)


class VMRepository:
    """Encapsulates all Nova (compute) operations."""

    def __init__(self, conn: openstack.connection.Connection) -> None:
        self._conn = conn

    # ── Read operations ────────────────────────────────────────────────────────

    def list_servers(self, filters: dict | None = None) -> list[Any]:
        """Return a list of Server objects matching optional filters."""
        try:
            return list(self._conn.compute.servers(**(filters or {})))
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def get_server(self, server_id: str) -> Any:
        """Fetch a single server by ID; raises NotFoundError if missing."""
        try:
            server = self._conn.compute.get_server(server_id)
            if server is None:
                from app.exceptions import NotFoundError
                raise NotFoundError(f"Server {server_id} not found")
            return server
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    # ── Create / delete ────────────────────────────────────────────────────────

    def create_server(self, **kwargs: Any) -> Any:
        """Boot a new server; kwargs map directly to Nova create params."""
        try:
            logger.info("Creating server: name=%s", kwargs.get("name"))
            return self._conn.compute.create_server(**kwargs)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    def delete_server(self, server_id: str) -> None:
        """Terminate a server.  Idempotent – no error if already deleted."""
        try:
            logger.info("Deleting server: id=%s", server_id)
            self._conn.compute.delete_server(server_id, ignore_missing=True)
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    # ── Power operations ───────────────────────────────────────────────────────

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

    # ── Metadata ───────────────────────────────────────────────────────────────

    def set_server_metadata(self, server_id: str, metadata: dict[str, str]) -> dict:
        try:
            return dict(self._conn.compute.set_server_metadata(server_id, **metadata))
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc

    # ── Console ────────────────────────────────────────────────────────────────

    def get_console_url(self, server_id: str, console_type: str = "novnc") -> dict:
        """Return console URL dict; falls back gracefully if unsupported."""
        try:
            result = self._conn.compute.create_console(
                server_id, console_type=console_type
            )
            return {"console_type": console_type, "url": result.get("url", "")}
        except SDKException as exc:
            raise map_openstack_error(exc, "console") from exc

    # ── Wait helpers ───────────────────────────────────────────────────────────

    def wait_for_server(
        self,
        server_id: str,
        status: str = "ACTIVE",
        timeout: int = 300,
    ) -> Any:
        try:
            return self._conn.compute.wait_for_server(
                self._conn.compute.get_server(server_id),
                status=status,
                wait=timeout,
            )
        except SDKException as exc:
            raise map_openstack_error(exc, "server") from exc
