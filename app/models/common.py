"""Shared response envelopes and pagination models."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    has_next: bool


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: str | None = None
