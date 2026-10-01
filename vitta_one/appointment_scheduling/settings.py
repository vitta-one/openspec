"""Runtime settings owned by appointment scheduling."""

import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_CLINIC_TIMEZONE_ENV = "VITTA_ONE_CLINIC_TIMEZONE"


class ClinicTimezoneConfigurationError(RuntimeError):
    """Raised when the clinic timezone contract is missing or invalid."""


def clinic_timezone_name() -> str:
    value = os.getenv(_CLINIC_TIMEZONE_ENV, "").strip()
    if not value:
        raise ClinicTimezoneConfigurationError(
            f"{_CLINIC_TIMEZONE_ENV} deve ser definido com um timezone IANA válido."
        )
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ClinicTimezoneConfigurationError(
            f"{_CLINIC_TIMEZONE_ENV} deve ser definido com um timezone IANA válido."
        ) from exc
    return value


def clinic_timezone() -> ZoneInfo:
    return ZoneInfo(clinic_timezone_name())
