"""
Conteo de intentos fallidos de login por IP (Django cache).
Al superar umbral: bloqueo temporal y registro SECURITY.
"""
from typing import TYPE_CHECKING, Literal

from django.conf import settings
from django.core.cache import cache

from core.security_audit import client_ip, emit_security_event

if TYPE_CHECKING:
    from django.http import HttpRequest

FAIL_KEY = "sec_bf_fail:{ip}"
BLOCK_KEY = "sec_bf_block:{ip}"


def _threshold() -> int:
    return int(getattr(settings, "SECURITY_BF_THRESHOLD", 5))


def _window() -> int:
    return int(getattr(settings, "SECURITY_BF_WINDOW_SEC", 900))


def _block_ttl() -> int:
    return int(getattr(settings, "SECURITY_BF_BLOCK_SEC", 1800))


def is_login_blocked(request: "HttpRequest") -> bool:
    ip = client_ip(request)
    return bool(cache.get(BLOCK_KEY.format(ip=ip)))


def record_failed_login(request: "HttpRequest") -> Literal["ok", "blocked", "just_blocked"]:
    """
    Incrementa fallos por IP. Si alcanza umbral, fija bloqueo y emite SECURITY.
    """
    ip = client_ip(request)
    if cache.get(BLOCK_KEY.format(ip=ip)):
        return "blocked"

    fk = FAIL_KEY.format(ip=ip)
    try:
        n = cache.incr(fk)
    except ValueError:
        cache.set(fk, 1, timeout=_window())
        n = 1

    if n >= _threshold():
        cache.set(BLOCK_KEY.format(ip=ip), 1, timeout=_block_ttl())
        emit_security_event(
            request,
            "Bloqueo por fuerza bruta: umbral de intentos fallidos alcanzado",
            429,
        )
        cache.delete(fk)
        return "just_blocked"
    return "ok"


def clear_login_attempts(request: "HttpRequest") -> None:
    ip = client_ip(request)
    cache.delete(FAIL_KEY.format(ip=ip))
    cache.delete(BLOCK_KEY.format(ip=ip))
