"""Modelos Pydantic de la API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UploadRecord(BaseModel):
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


class StoredFileItem(BaseModel):
    name: str
    protocol: str
    size: int
    path: str
    created_at: str
    modified_at: str


class FilesListResponse(BaseModel):
    total: int
    items: list[StoredFileItem]


class DeleteFileRequest(BaseModel):
    protocol: str
    name: str


class DeleteFileResponse(BaseModel):
    success: bool
    message: str
    deleted: StoredFileItem
    remote_deleted: bool
    local_deleted: bool
    warning: str | None = None
