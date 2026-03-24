"""
storage/s3.py
-------------
StorageHandler para S3 / MinIO.

Lee credenciales desde settings (que a su vez las carga del .env).
Sube el archivo al bucket configurado usando boto3 con firma s3v4,
compatible con MinIO y AWS S3.
"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

import boto3
from botocore.client import Config

from app.config import settings
from app.storage.base import StorageCredentials, StorageHandler

logger = logging.getLogger(__name__)


class S3StorageHandler(StorageHandler):
    """Sube archivos a un bucket S3 / MinIO."""

    def _get_client(self):
        scheme = "https" if settings.S3_USE_SSL else "http"
        return boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{settings.S3_ENDPOINT}",
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        s3 = self._get_client()
        with open(temp_path, "rb") as f:
            s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=filename,
                Body=f.read(),
                ContentType=content_type,
            )

        saved_path = f"s3://{settings.S3_BUCKET}/{filename}"
        logger.info("S3Storage: '%s' → %s", filename, saved_path)
        return saved_path
