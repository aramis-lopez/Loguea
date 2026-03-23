"""Filtros de logging: inyectan request_id y user_id sin exponer secretos."""
import logging

from core.context import get_request_id, get_user_id_for_log


class RequestContextFilter(logging.Filter):
    """Añade request_id y user_id a cada registro para correlación."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        if not hasattr(record, "user_id"):
            record.user_id = get_user_id_for_log()
        return True
