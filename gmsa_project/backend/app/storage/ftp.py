"""StorageHandler para FTP."""

from __future__ import annotations

import logging
from datetime import datetime
from ftplib import FTP, all_errors, error_perm
from pathlib import Path

from app.config import settings
from app.storage.base import (
    StorageAuthenticationError,
    StorageConfigurationError,
    StorageCredentials,
    StorageHandler,
    StoragePathError,
    StoragePermissionError,
)

logger = logging.getLogger(__name__)


class FTPStorageHandler(StorageHandler):
    """Sube, lista y elimina archivos en un servidor FTP."""

    def _get_client(self) -> FTP:
        ftp = FTP()
        ftp.connect(settings.FTP_HOST, settings.FTP_PORT, timeout=10)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        ftp.set_pasv(True)
        ftp.cwd(settings.FTP_DIR)
        return ftp

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        ftp = None
        safe_name = self._validate_filename(filename)

        try:
            ftp = self._get_client()
            with open(temp_path, "rb") as file_obj:
                ftp.storbinary(f"STOR {safe_name}", file_obj)

            base_dir = settings.FTP_DIR.rstrip("/")
            saved_path = f"ftp://{settings.FTP_HOST}:{settings.FTP_PORT}{base_dir}/{safe_name}"
            logger.info("FTPStorage save OK '%s' -> %s", safe_name, saved_path)
            return saved_path
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        ftp = None
        safe_name = self._validate_filename(filename)

        try:
            ftp = self._get_client()
            ftp.delete(safe_name)
            logger.info("FTPStorage delete OK '%s'", safe_name)
        except error_perm as exc:
            message = str(exc)
            upper_message = message.upper()

            if message.startswith("530"):
                raise StorageAuthenticationError(
                    "Autenticacion FTP rechazada. Verifica las credenciales configuradas."
                ) from exc
            if message.startswith("550"):
                if "NO SUCH FILE" in upper_message or "NOT FOUND" in upper_message:
                    logger.info("FTPStorage delete skipped '%s' because remote file was absent", safe_name)
                    return
                raise StoragePermissionError(
                    "FTP rechazo la eliminacion del archivo. Verifica permisos sobre el directorio remoto."
                ) from exc
            raise StorageConfigurationError(f"Error FTP al eliminar '{safe_name}': {exc}") from exc
        except all_errors as exc:
            raise StorageConfigurationError(f"Error FTP al eliminar '{safe_name}': {exc}") from exc
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def list_files(
        self,
        credentials: StorageCredentials | None = None,
    ) -> list[dict]:
        ftp = None
        items: list[dict] = []

        try:
            ftp = self._get_client()

            try:
                for name, facts in ftp.mlsd():
                    if facts.get("type") != "file":
                        continue
                    items.append(
                        self._build_item(
                            name=name,
                            size=int(facts.get("size", "0") or 0),
                            modified_at=self._parse_ftp_dt(facts.get("modify")),
                        )
                    )
            except all_errors:
                for name in ftp.nlst():
                    safe_name = Path(name).name
                    if not safe_name or safe_name in {".", ".."}:
                        continue

                    size = 0
                    modified_at = None
                    try:
                        size = ftp.size(safe_name) or 0
                    except all_errors:
                        pass

                    try:
                        response = ftp.sendcmd(f"MDTM {safe_name}")
                        modified_at = self._parse_ftp_dt(response.split()[-1])
                    except all_errors:
                        pass

                    items.append(self._build_item(name=safe_name, size=int(size), modified_at=modified_at))

            return sorted(items, key=lambda item: item["modified_at"], reverse=True)
        except error_perm as exc:
            message = str(exc)
            if message.startswith("530"):
                raise StorageAuthenticationError(
                    "Autenticacion FTP rechazada. Verifica las credenciales configuradas."
                ) from exc
            raise StorageConfigurationError(f"Error FTP al listar archivos: {exc}") from exc
        except all_errors as exc:
            raise StorageConfigurationError(f"Error FTP al listar archivos: {exc}") from exc
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def _validate_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo FTP es invalido. No se permiten rutas embebidas ni '..'."
            )
        return safe_name

    def _build_item(self, *, name: str, size: int, modified_at: str | None) -> dict:
        safe_name = self._validate_filename(name)
        modified = modified_at or datetime.now().isoformat(timespec="seconds")
        base_dir = settings.FTP_DIR.rstrip("/") or "/"
        return {
            "name": safe_name,
            "protocol": "ftp",
            "size": size,
            "path": f"ftp://{settings.FTP_HOST}:{settings.FTP_PORT}{base_dir}/{safe_name}",
            "created_at": modified,
            "modified_at": modified,
        }

    def _parse_ftp_dt(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y%m%d%H%M%S").isoformat(timespec="seconds")
        except ValueError:
            return None
