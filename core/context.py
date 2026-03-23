"""Contexto por petición para trazabilidad en logs (sin datos sensibles)."""
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)


def get_request_id() -> str:
    rid = request_id_var.get()
    return rid if rid is not None else "n/a"


def get_user_id_for_log() -> str | int:
    uid = user_id_var.get()
    return uid if uid is not None else "anonymous"
