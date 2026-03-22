"""
schemas.py
----------
Pydantic models used for request validation and response serialization.

Keeping all data shapes here makes them easy to find, update, and reuse
across routers without importing from unrelated modules.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UploadRecord(BaseModel):
    """A single entry in the upload history."""

    id: str
    filename: str
    protocol: str
    username: str
    size_kb: float
    status: Literal["Éxito", "Error"]
    saved_path: str
    uploaded_at: str


class UploadResponse(BaseModel):
    success: bool
    message: str
    record: UploadRecord


class HistoryResponse(BaseModel):
    total: int
    items: list[UploadRecord]


class ConfigResponse(BaseModel):
    project_name: str
    max_file_size_mb: int
    allowed_extensions: list[str]
    supported_protocols: list[str]
