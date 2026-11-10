"""Minimal signed Cloudinary client for private clinical assets."""

from dataclasses import dataclass
import hashlib
from time import time
from typing import Any
from urllib.parse import urlencode

import httpx

from .settings import CloudinarySettings


class CloudinaryError(RuntimeError):
    pass


class CloudinaryUnavailableError(CloudinaryError):
    pass


@dataclass(frozen=True)
class UploadedAsset:
    asset_id: str
    public_id: str
    version: int
    resource_type: str
    format: str
    bytes: int


def _signature(params: dict[str, Any], secret: str) -> str:
    serialized = "&".join(f"{key}={params[key]}" for key in sorted(params) if params[key] not in (None, ""))
    return hashlib.sha256(f"{serialized}{secret}".encode()).hexdigest()


class CloudinaryClient:
    def __init__(self, settings: CloudinarySettings, *, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._client = httpx.Client(timeout=12.0, transport=transport, follow_redirects=False)

    def upload(self, *, content: bytes, filename: str, public_id: str) -> UploadedAsset:
        timestamp = int(time())
        params: dict[str, Any] = {
            "folder": "vitta-one/clinical",
            "public_id": public_id,
            "timestamp": timestamp,
            "type": "authenticated",
        }
        data = {**params, "api_key": self.settings.api_key, "signature": _signature(params, self.settings.api_secret)}
        url = f"https://api.cloudinary.com/v1_1/{self.settings.cloud_name}/auto/upload"
        try:
            response = self._client.post(url, data=data, files={"file": (filename, content, "application/octet-stream")})
            response.raise_for_status()
            payload = response.json()
            return UploadedAsset(
                asset_id=str(payload["asset_id"]), public_id=str(payload["public_id"]),
                version=int(payload["version"]), resource_type=str(payload["resource_type"]),
                format=str(payload["format"]), bytes=int(payload["bytes"]),
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise CloudinaryUnavailableError("Não foi possível armazenar o anexo agora.") from exc

    def private_download_url(self, *, public_id: str, format: str, resource_type: str) -> str:
        timestamp = int(time())
        params: dict[str, Any] = {
            "attachment": "true",
            "expires_at": timestamp + self.settings.download_ttl_seconds,
            "format": format,
            "public_id": public_id,
            "timestamp": timestamp,
            "type": "authenticated",
        }
        query = {**params, "api_key": self.settings.api_key, "signature": _signature(params, self.settings.api_secret)}
        return f"https://api.cloudinary.com/v1_1/{self.settings.cloud_name}/{resource_type}/download?{urlencode(query)}"

    def delete(self, *, public_id: str, resource_type: str) -> None:
        timestamp = int(time())
        params: dict[str, Any] = {"invalidate": "true", "public_id": public_id, "timestamp": timestamp, "type": "authenticated"}
        data = {**params, "api_key": self.settings.api_key, "signature": _signature(params, self.settings.api_secret)}
        url = f"https://api.cloudinary.com/v1_1/{self.settings.cloud_name}/{resource_type}/destroy"
        try:
            response = self._client.post(url, data=data)
            response.raise_for_status()
            result = str(response.json().get("result", ""))
            if result not in {"ok", "not found"}:
                raise CloudinaryUnavailableError("Não foi possível remover o anexo agora.")
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            raise CloudinaryUnavailableError("Não foi possível remover o anexo agora.") from exc

