"""
Emisión de líneas a la bitácora forense (formato pipe estándar del proyecto).
"""
import logging
from typing import TYPE_CHECKING

from core.context import get_user_id_for_log
from core.security_levels import SECURITY

if TYPE_CHECKING:
    from django.http import HttpRequest

log = logging.getLogger("security.audit")


def client_ip(request: "HttpRequest") -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "desconocida")[:45]


def user_label_for_audit(request: "HttpRequest") -> str:
    uid = get_user_id_for_log()
    if uid != "anonymous":
        return f"ID:{uid}"
    u = getattr(request, "user", None)
    if u is not None and getattr(u, "is_authenticated", False):
        return f"ID:{u.pk}"
    return "Anónimo"


def emit_bitacora(
    request: "HttpRequest",
    level: int,
    event: str,
    status_code: int | str,
    *,
    user_override: str | None = None,
) -> None:
    """Escribe una línea en el logger security.audit (formateador BitacoraFormatter)."""
    ua = (request.META.get("HTTP_USER_AGENT") or "-")[:500]
    user = user_override if user_override is not None else user_label_for_audit(request)
    endpoint = getattr(request, "path", "/")[:2048]
    ip = client_ip(request)
    log.log(
        level,
        event,
        extra={
            "bitacora_event": event,
            "bitacora_user": user,
            "bitacora_ip": ip,
            "bitacora_endpoint": endpoint,
            "bitacora_status": status_code if isinstance(status_code, str) else str(status_code),
            "bitacora_ua": ua,
        },
    )


def emit_security_event(request: "HttpRequest", event: str, status_code: int) -> None:
    emit_bitacora(request, SECURITY, event, status_code)
