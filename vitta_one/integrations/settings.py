"""Strict environment configuration for external providers."""

from dataclasses import dataclass
import os


class IntegrationConfigurationError(RuntimeError):
    """Safe configuration failure without echoing secret values."""


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _complete_or_none(names: tuple[str, ...]) -> tuple[str, ...] | None:
    values = tuple(_env(name) for name in names)
    if not any(values):
        return None
    if not all(values):
        missing = ", ".join(name for name, value in zip(names, values) if not value)
        raise IntegrationConfigurationError(f"Configuração incompleta; defina: {missing}.")
    return values


@dataclass(frozen=True)
class CloudinarySettings:
    cloud_name: str
    api_key: str
    api_secret: str
    max_bytes: int = 10 * 1024 * 1024
    download_ttl_seconds: int = 300


def cloudinary_settings() -> CloudinarySettings | None:
    values = _complete_or_none(("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"))
    if values is None:
        return None
    try:
        max_bytes = int(_env("VITTA_ONE_ATTACHMENT_MAX_BYTES") or 10 * 1024 * 1024)
        ttl = int(_env("VITTA_ONE_ATTACHMENT_DOWNLOAD_TTL_SECONDS") or 300)
    except ValueError as exc:
        raise IntegrationConfigurationError("Limites do armazenamento devem ser inteiros positivos.") from exc
    if max_bytes <= 0 or ttl < 60 or ttl > 3600:
        raise IntegrationConfigurationError("Limites do armazenamento estão fora da faixa permitida.")
    return CloudinarySettings(*values, max_bytes=max_bytes, download_ttl_seconds=ttl)


@dataclass(frozen=True)
class ZapSignSettings:
    api_token: str
    webhook_token: str
    base_url: str = "https://api.zapsign.com.br/api/v1"
    timeout_seconds: float = 12.0


def zapsign_settings() -> ZapSignSettings | None:
    values = _complete_or_none(("ZAPSIGN_API_TOKEN", "ZAPSIGN_WEBHOOK_TOKEN"))
    if values is None:
        return None
    base_url = (_env("ZAPSIGN_API_BASE_URL") or "https://api.zapsign.com.br/api/v1").rstrip("/")
    if not base_url.startswith("https://"):
        raise IntegrationConfigurationError("ZAPSIGN_API_BASE_URL deve usar HTTPS.")
    return ZapSignSettings(*values, base_url=base_url)


@dataclass(frozen=True)
class AsaasSettings:
    api_key: str
    webhook_token: str
    base_url: str = "https://api-sandbox.asaas.com/v3"
    user_agent: str = "Vitta-One/1.0"
    timeout_seconds: float = 12.0


def asaas_settings() -> AsaasSettings | None:
    values = _complete_or_none(("ASAAS_API_KEY", "ASAAS_WEBHOOK_TOKEN"))
    if values is None:
        return None
    base_url = (_env("ASAAS_API_BASE_URL") or "https://api-sandbox.asaas.com/v3").rstrip("/")
    production = base_url == "https://api.asaas.com/v3"
    if production and _env("VITTA_ONE_ALLOW_ASAAS_PRODUCTION").lower() != "true":
        raise IntegrationConfigurationError("Asaas Produção exige opt-in explícito.")
    if not base_url.startswith("https://"):
        raise IntegrationConfigurationError("ASAAS_API_BASE_URL deve usar HTTPS.")
    return AsaasSettings(*values, base_url=base_url, user_agent=_env("ASAAS_USER_AGENT") or "Vitta-One/1.0")


def integration_status() -> dict[str, str]:
    """Return configuration health without returning any credential or URL."""
    result: dict[str, str] = {}
    for name, loader in (("cloudinary", cloudinary_settings), ("zapsign", zapsign_settings), ("asaas", asaas_settings)):
        try:
            result[name] = "CONFIGURED" if loader() is not None else "NOT_CONFIGURED"
        except IntegrationConfigurationError:
            result[name] = "INVALID_CONFIGURATION"
    return result

