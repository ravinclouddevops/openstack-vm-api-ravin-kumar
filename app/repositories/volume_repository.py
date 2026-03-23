"""
Volume Repository — wraps Cinder (block storage) via openstacksdk.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import openstack.connection
from openstack.exceptions import SDKException

from app.repositories.openstack_client import map_openstack_error

logger = logging.getLogger(__name__)


class VolumeRepository:
    """Encapsulates all Cinder (block storage) operations."""

    def __init__(self, conn: openstack.connection.Connection) -> None:
        self._conn = conn

    def list_volumes(self, filters: Optional[Dict] = None) -> List[Any]:
        try:
            return list(self._conn.block_storage.volumes(**(filters or {})))
        except SDKException as exc:
            raise map_openstack_error(exc, "volume") from exc

    def get_volume(self, volume_id: str) -> Any:
        try:
            vol = self._conn.block_storage.get_volume(volume_id)
            if vol is None:
                from app.exceptions import NotFoundError
                raise NotFoundError(f"Volume {volume_id} not found")
            return vol
        except SDKException as exc:
            raise map_openstack_error(exc, "volume") from exc

    def create_volume(self, **kwargs: Any) -> Any:
        try:
            logger.info("Creating volume: name=%s size=%s", kwargs.get("name"), kwargs.get("size"))
            return self._conn.block_storage.create_volume(**kwargs)
        except SDKException as exc:
            raise map_openstack_error(exc, "volume") from exc

    def delete_volume(self, volume_id: str) -> None:
        try:
            logger.info("Deleting volume: id=%s", volume_id)
            self._conn.block_storage.delete_volume(volume_id, ignore_missing=True)
        except SDKException as exc:
            raise map_openstack_error(exc, "volume") from exc

    def attach_volume(self, server_id: str, volume_id: str, device: Optional[str] = None) -> Any:
        try:
            logger.info("Attaching volume %s to server %s", volume_id, server_id)
            kwargs: Dict[str, Any] = {"volumeId": volume_id}
            if device:
                kwargs["device"] = device
            return self._conn.compute.create_volume_attachment(server_id, **kwargs)
        except SDKException as exc:
            raise map_openstack_error(exc, "volume attachment") from exc

    def detach_volume(self, server_id: str, volume_id: str) -> None:
        try:
            logger.info("Detaching volume %s from server %s", volume_id, server_id)
            self._conn.compute.delete_volume_attachment(volume_id, server_id, ignore_missing=True)
        except SDKException as exc:
            raise map_openstack_error(exc, "volume attachment") from exc

    def create_snapshot(self, volume_id: str, name: str, description: Optional[str], force: bool = False) -> Any:
        try:
            logger.info("Creating snapshot of volume %s", volume_id)
            return self._conn.block_storage.create_snapshot(
                volume_id=volume_id,
                name=name,
                description=description,
                force=force,
            )
        except SDKException as exc:
            raise map_openstack_error(exc, "snapshot") from exc

    def list_snapshots(self, volume_id: Optional[str] = None) -> List[Any]:
        try:
            filters: Dict[str, Any] = {}
            if volume_id:
                filters["volume_id"] = volume_id
            return list(self._conn.block_storage.snapshots(**filters))
        except SDKException as exc:
            raise map_openstack_error(exc, "snapshot") from exc

    def get_snapshot(self, snapshot_id: str) -> Any:
        try:
            snap = self._conn.block_storage.get_snapshot(snapshot_id)
            if snap is None:
                from app.exceptions import NotFoundError
                raise NotFoundError(f"Snapshot {snapshot_id} not found")
            return snap
        except SDKException as exc:
            raise map_openstack_error(exc, "snapshot") from exc

    def delete_snapshot(self, snapshot_id: str) -> None:
        try:
            self._conn.block_storage.delete_snapshot(snapshot_id, ignore_missing=True)
        except SDKException as exc:
            raise map_openstack_error(exc, "snapshot") from exc

    def wait_for_volume(self, volume_id: str, status: str = "available", timeout: int = 120) -> Any:
        try:
            return self._conn.block_storage.wait_for_status(
                self._conn.block_storage.get_volume(volume_id),
                status=status,
                wait=timeout,
            )
        except SDKException as exc:
            raise map_openstack_error(exc, "volume") from exc
