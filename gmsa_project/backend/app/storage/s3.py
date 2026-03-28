"""StorageHandler para S3 / MinIO."""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.storage.base import (
    StorageConfigurationError,
    StorageCredentials,
    StorageHandler,
    StoragePathError,
)

logger = logging.getLogger(__name__)


class S3StorageHandler(StorageHandler):
    """Sube y elimina archivos en un bucket S3 / MinIO."""

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
        safe_name = self._validate_filename(filename)
        content_type, _ = mimetypes.guess_type(safe_name)
        content_type = content_type or "application/octet-stream"

        s3 = self._get_client()
        with open(temp_path, "rb") as file_obj:
            s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=safe_name,
                Body=file_obj.read(),
                ContentType=content_type,
            )

        saved_path = f"s3://{settings.S3_BUCKET}/{safe_name}"
        logger.info("S3Storage save OK '%s' -> %s", safe_name, saved_path)
        return saved_path

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        safe_name = self._validate_filename(filename)

        try:
            s3 = self._get_client()
            s3.delete_object(Bucket=settings.S3_BUCKET, Key=safe_name)
            logger.info("S3Storage delete OK '%s' from bucket %s", safe_name, settings.S3_BUCKET)
        except (ClientError, BotoCoreError) as exc:
            raise StorageConfigurationError(f"Error S3 al eliminar '{safe_name}': {exc}") from exc

    def _validate_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo S3 es invalido. No se permiten rutas embebidas ni '..'."
            )
        return safe_name
