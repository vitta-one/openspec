"""Legacy deployment fallback and public activation URL."""

from dataclasses import dataclass
import os
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ClinicLocation:
    name: str
    address: str
    configured: bool
    persisted: bool = False
    revision: int = 0


def clinic_location() -> ClinicLocation:
    name = " ".join(os.getenv("VITTA_ONE_CLINIC_NAME", "").split())
    address = " ".join(os.getenv("VITTA_ONE_CLINIC_ADDRESS", "").split())
    configured = bool(name and address and len(name) <= 160 and len(address) <= 500)
    if not configured:
        return ClinicLocation(name="", address="", configured=False)
    return ClinicLocation(name=name, address=address, configured=configured)


def patient_activation_url() -> str:
    base = os.getenv("VITTA_ONE_PUBLIC_URL", "").strip().rstrip("/")
    parsed = urlparse(base)
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    secure_scheme = parsed.scheme == "https" or local_http
    if (
        not secure_scheme
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return ""
    return f"{base}/ativar-paciente"
